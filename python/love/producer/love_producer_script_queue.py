# This file is part of LOVE-producer.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by Inria Chile and
# the LSST Project (https://www.lsst.org).
#
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership and dependencies.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["LoveProducerScriptQueue"]

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

from love.producer.love_producer_csc import LoveProducerCSC
from lsst.ts.idl.enums import Script, ScriptQueue
from lsst.ts.salobj import AckError, Domain, Remote
from lsst.ts.salobj.base_script import HEARTBEAT_INTERVAL as SCRIPT_HEARTBEAT_INTERVAL
from lsst.ts.utils import make_done_future


class LoveProducerScriptQueue(LoveProducerCSC):
    """Specialized LOVE producer to deal with the ScriptQueue CSC."""

    cmd_timeout = 5.0  # command timeout in seconds.
    max_script_log_messages = 20

    def __init__(
        self, domain: Domain, log: Optional[logging.Logger] = None, **kwargs
    ) -> None:
        if "salindex" not in kwargs:
            raise RuntimeError(
                "ScriptQueue is an indexed component, `salindex` must be specified."
            )

        kwargs_reformatted = kwargs.copy()
        if "csc" in kwargs_reformatted:
            kwargs_reformatted.pop("csc")

        super().__init__(
            domain=domain,
            csc="ScriptQueue",
            log=log,
            remote_readonly=False,
            **kwargs_reformatted,
        )

        self.remote_scripts = Remote(
            domain,
            "Script",
            index=0,
            readonly=True,
        )

        self.state = dict(
            enabled=False,
            running=False,
            waitingIndices=[],
            currentIndices=[],
            finishedIndices=[],
        )

        self.available_scripts = dict(
            standard=dict(),
            external=dict(),
        )

        self.scripts = dict()

        self.scripts_heartbeat = dict()

        self.scripts_log_messages = dict()

        self.script_reply = dict(evt_logMessage=self.send_script_log_message)

        self._set_revcode_mapping(
            self.remote_scripts.evt_logMessage.rev_code, "script_logMessage"
        )

        self._set_template_manager_message(
            topic_name="script_logMessage",
            topic=self.remote_scripts.evt_logMessage,
        )

        self._script_heartbeat_producer_task = None

        self.scripts_schema_task: asyncio.Future = make_done_future()

        self._non_topic_data_stream = {
            "stateStream",
            "scriptsStream",
            "availableScriptsStream",
        }

        self.script_messages_to_reply = {"evt_logMessage"}

        self.register_additional_action(
            "evt_script", self.handle_event_scriptqueue_script
        )
        self.register_additional_action(
            "evt_queue", self.handle_event_scriptqueue_queue
        )
        self.register_additional_action(
            "evt_availableScripts", self.handle_event_scriptqueue_available_scripts
        )
        self.register_additional_action(
            "evt_configSchema", self.handle_event_scriptqueue_config_schema
        )

        self.register_asynchronous_data_category("stateStream", "_stateStream")
        self.register_asynchronous_data_category("scriptsStream", "_scriptsStream")
        self.register_asynchronous_data_category(
            "availableScriptsStream", "_availableScriptsStream"
        )

        self.store_samples(_stateStream=self.scriptqueue_state_message_data)
        self.store_samples(_scriptsStream=self.scripts_state_message_data)
        self.store_samples(
            _availableScriptsStream=self.available_scripts_state_message_data
        )

    async def start(self) -> None:
        await super().start()

        await self.set_script_heartbeat_producer()

        self.remote_scripts.evt_heartbeat.callback = (
            self.monitor_script_heartbeat_callback
        )

        self.remote_scripts.evt_logMessage.callback = (
            self.monitor_script_log_message_callback
        )

        self.remote_scripts.evt_state.callback = self.handle_event_script_state

        self.remote_scripts.evt_metadata.callback = self.handle_event_script_metadata
        self.remote_scripts.evt_description.callback = (
            self.handle_event_script_description
        )
        self.remote_scripts.evt_checkpoints.callback = (
            self.handle_event_script_checkpoints
        )
        self.remote_scripts.evt_logLevel.callback = self.handle_event_script_log_level

    def should_reply_to_message_data(self, message_data: dict) -> bool:
        """Determines whether a reply to message data should be sent.

        Override base class default behavior.

        Parameters
        ----------
        message_data: `dict`
            Input dictionary with information used by the producer to determine
            some action to take.

        Returns
        -------
        `bool`
            Should reply to message data?
        """

        data = message_data.get("data", [dict()])[0]
        csc = data.get("csc", None)

        try:
            sample_name = self.get_sample_name(message_data)
        except RuntimeError:
            self.log.debug("Error getting sample name for message_data.")
            return False

        if csc == "Script" and sample_name in self.script_messages_to_reply:
            return True
        else:
            return super().should_reply_to_message_data(message_data=message_data)

    async def send_reply_to_message_data(self, message_data: dict) -> None:
        """Send reply to message data."""

        data = message_data.get("data", [dict()])[0]
        csc = data.get("csc", None)

        if csc != "Script":
            await super().send_reply_to_message_data(message_data)
        else:
            try:
                sample_name = self.get_sample_name(message_data)
            except RuntimeError:
                self.log.exception("Error getting sample. Ignoring.")
                return
            if sample_name in self.script_reply:
                await self.script_reply[sample_name](message_data)

    async def get_initial_state_messages_as_json(self) -> AsyncIterator[int]:
        """Asynchronously generetate all initial state messages.

        Yields
        ------
        initial_state : `str`
            Initial state messages as json.
        """

        for csc in {"all", "ScriptQueue", "ScriptQueueState", "Script"}:
            yield self.get_message_initial_state_as_json_for_csc(csc)

    async def handle_event_scriptqueue_script(self, event: Any) -> None:
        """Additional action for script queue script event.

        Parameters
        ----------
        event : `ScriptQueue_logevent_script`
            ScriptQueue_logevent_script event data.
        """
        if event.scriptSalIndex not in self.scripts:
            self.scripts[event.scriptSalIndex] = self.get_empty_script(
                event.scriptSalIndex
            )

        self.scripts[event.scriptSalIndex]["type"] = (
            "standard" if event.isStandard else "external"
        )
        self.scripts[event.scriptSalIndex]["path"] = event.path
        self.scripts[event.scriptSalIndex]["process_state"] = (
            ScriptQueue.ScriptProcessState(event.processState).name
        )
        self.scripts[event.scriptSalIndex]["script_state"] = Script.ScriptState(
            event.scriptState
        ).name
        self.scripts[event.scriptSalIndex][
            "timestampConfigureEnd"
        ] = event.timestampConfigureEnd
        self.scripts[event.scriptSalIndex][
            "timestampConfigureStart"
        ] = event.timestampConfigureStart
        self.scripts[event.scriptSalIndex][
            "timestampProcessEnd"
        ] = event.timestampProcessEnd
        self.scripts[event.scriptSalIndex][
            "timestampProcessStart"
        ] = event.timestampProcessStart
        self.scripts[event.scriptSalIndex][
            "timestampRunStart"
        ] = event.timestampRunStart

        self.store_samples(_scriptsStream=self.scripts_state_message_data)
        await self.send_scripts_state()

    async def handle_event_scriptqueue_queue(self, event: Any) -> None:
        """Saves the queue state using the event data and queries the state of
        each script that does not exist or has not been set up

        Parameters
        ----------
        event : `ScriptQueue_logevent_queue`
            The SAL event data.
        """
        self.state["running"] = event.running == 1
        # The ScriptQueue CSC will be extended to support multiple
        # current scripts in the future. For now, only one is supported.
        # See: DM-44198.
        self.state["currentIndices"] = (
            [event.currentSalIndex] if event.currentSalIndex > 0 else []
        )
        self.state["finishedIndices"] = list(event.pastSalIndices[: event.pastLength])
        self.state["waitingIndices"] = list(event.salIndices[: event.length])
        self.state["enabled"] = event.enabled == 1

        salindex_new_scripts = set(
            self.state["waitingIndices"]
            + self.state["finishedIndices"]
            + self.state["currentIndices"]
        )

        salindex_current_scripts = set(self.scripts.keys())

        for salindex in salindex_current_scripts - salindex_new_scripts:
            self.log.debug(
                f"Script {salindex} not in queue. Removing from internal database."
            )
            del self.scripts[salindex]
            del self.scripts_heartbeat[salindex]
            del self.scripts_log_messages[salindex]

        for salindex in salindex_new_scripts - salindex_current_scripts:
            self.add_new_script(salindex)

        self.store_samples(_stateStream=self.scriptqueue_state_message_data)
        self.store_samples(_scriptsStream=self.scripts_state_message_data)

        await self.send_scriptqueue_state()
        await self.send_scripts_state()

    async def handle_event_scriptqueue_available_scripts(self, data: Any) -> None:
        """Additional action for availableScripts events.

        Updates the list of available_scripts in the state according to the
        availableScripts event info.

        Parameters
        ----------
        data : `ScriptQueue_logevent_availableScripts`
            The SAL event data.
        """

        if not self.scripts_schema_task.done():
            self.log.debug("Cancelling ongoing script schema query.")
            self.scripts_schema_task.cancel()
            try:
                await self.scripts_schema_task
            except asyncio.CancelledError:
                pass
            except Exception:
                self.log.exception("Unexpected error in script_schema_task.")

        for script_path in data.standard.split(":"):
            if script_path not in self.available_scripts["standard"]:
                self.available_scripts["standard"][script_path] = ""

        for script_path in data.external.split(":"):
            if script_path not in self.available_scripts["external"]:
                self.available_scripts["external"][script_path] = ""

        self.store_samples(
            _availableScriptsStream=self.available_scripts_state_message_data
        )
        await self.send_available_scripts()

        self.log.debug("Scheduling update of script schemas.")
        self.scripts_schema_task = asyncio.create_task(self.update_scripts_schema())

    async def handle_event_scriptqueue_config_schema(self, event: Any) -> None:
        """Additional action for configSchema event.

        Parameters
        ----------
        event : `ScriptQueue_logevent_configSchema`
            ScriptQueue_logevent_configSchema event data.
        """
        event_script_type = "standard" if event.isStandard else "external"

        if event.path not in self.available_scripts[event_script_type]:
            self.log.warning(
                f"Script {event.path} not in {event_script_type} available scripts database. Adding..."
            )

        self.available_scripts[event_script_type][event.path] = (
            event.configSchema if event.configSchema else "# empty schema"
        )

        # Only update status if script_schema_task is not running, otherwise
        # we expect a lot more information to come through.
        if self.scripts_schema_task.done():
            self.store_samples(
                _availableScriptsStream=self.available_scripts_state_message_data
            )
            await self.send_available_scripts()

    async def handle_event_script_metadata(self, event: Any) -> None:
        """Callback for the logevent_metadata.

        Used to extract the expected duration of the script.

        Parameters
        ----------
        event : `Script_logevent_metadata`
            Event data.
        """
        if event.salIndex in self.scripts:
            self.scripts[event.salIndex]["expected_duration"] = event.duration
            self.store_samples(_scriptsStream=self.scripts_state_message_data)
            await self.send_scripts_state()

    async def handle_event_script_state(self, event: Any) -> None:
        """Callback for the Script_logevent_state event.

        Used to update the state of the script.

        Parameters
        ----------
        event : `Script_logevent_state`
            Event data.
        """
        if event.salIndex in self.scripts:
            self.scripts[event.salIndex]["script_state"] = Script.ScriptState(
                event.state
            ).name
            self.scripts[event.salIndex]["last_checkpoint"] = event.lastCheckpoint
            self.store_samples(_scriptsStream=self.scripts_state_message_data)
            await self.send_scripts_state()

    async def handle_event_script_description(self, event: Any) -> None:
        """Callback for the logevent_description.

        Used to extract Script's description, classname and remotes.

        Parameters
        ----------
        event: `Script_logevent_description`
            Event data.
        """
        if event.salIndex in self.scripts:
            salindex = event.salIndex
            self.scripts[salindex]["description"] = event.description
            self.scripts[salindex]["classname"] = event.classname
            self.scripts[salindex]["remotes"] = event.remotes
            self.store_samples(_scriptsStream=self.scripts_state_message_data)
            await self.send_scripts_state()

    async def handle_event_script_checkpoints(self, event: Any) -> None:
        """Callback for the logevent_checkpoints.

        Used to extract Script's checkpoint pause and stop information.

        Parameters
        ----------
        event : `Script_logevent_checkpoints`
            Event data.
        """
        if event.salIndex in self.scripts:
            salindex = event.salIndex
            self.scripts[salindex]["pause_checkpoints"] = event.pause
            self.scripts[salindex]["stop_checkpoints"] = event.stop
            self.store_samples(_scriptsStream=self.scripts_state_message_data)
            await self.send_scripts_state()

    async def handle_event_script_log_level(self, event: Any) -> None:
        """Listens to the logLevel event.

        Parameters
        ----------
        event : `Script_logevent_logLevel`
            Event data.
        """
        if event.salIndex in self.scripts:
            salindex = event.salIndex
            self.scripts[salindex]["log_level"] = event.level
            self.store_samples(_scriptsStream=self.scripts_state_message_data)
            await self.send_scripts_state()

    async def update_scripts_schema(self) -> None:
        """Update scripts schema."""

        show_schema_all = [
            self.remote.cmd_showSchema.set_start(
                isStandard=True,
                path=script_path,
                timeout=self.cmd_timeout,
            )
            for script_path in self.available_scripts["standard"]
        ] + [
            self.remote.cmd_showSchema.set_start(
                isStandard=False,
                path=script_path,
                timeout=self.cmd_timeout,
            )
            for script_path in self.available_scripts["external"]
        ]

        for show_schema in show_schema_all:
            try:
                await show_schema
            except asyncio.CancelledError:
                self.log.exception("showSchema command task canceled.")
            except AckError as ack_err:
                self.log.exception(
                    f"showSchema command rejectedwith {ack_err.ackcmd.ack}: {ack_err.ackcmd.result}."
                )
            except Exception:
                self.log.exception("Error getting schema for script.")

        self.store_samples(
            _availableScriptsStream=self.available_scripts_state_message_data
        )
        await self.send_available_scripts()

    def add_new_script(self, salindex: int) -> None:
        """Add new script to the internal script database.

        Parameters
        ----------
        salindex : `int`
            The SAL index of the stript
        """
        if salindex not in self.scripts:
            self.scripts[salindex] = self.get_empty_script(salindex)

        if salindex not in self.scripts_heartbeat:
            self.scripts_heartbeat[salindex] = self.get_empty_script_heartbeat(salindex)

        if salindex not in self.scripts_log_messages:
            self.scripts_log_messages[salindex] = deque(
                [], self.max_script_log_messages
            )

    def get_empty_script(self, salindex: int) -> dict:
        """Return an empty script data structure.

        Parameters
        ----------
        salindex : `int`
            The SAL index of the script.

        Returns
        -------
        `dict`
            The empty, default, script.
        """
        default_value = "UNKNOWN"
        return dict(
            remote=None,
            setup=True,  # flag to trigger show_script only once,
            index=salindex,
            path=default_value,
            type=default_value,
            process_state=default_value,
            script_state=default_value,
            timestampConfigureEnd=0,
            timestampConfigureStart=0,
            timestampProcessEnd=0,
            timestampProcessStart=0,
            timestampRunStart=0,
            expected_duration=0,
            last_checkpoint="",
            description="",
            classname="",
            remotes="",
            last_heartbeat_timestamp=0,
            lost_heartbeats=0,
            pause_checkpoints="",
            stop_checkpoints="",
            log_level=logging.INFO,
        )

    def get_empty_script_heartbeat(self, script_index: int) -> dict:
        """Heartbeat message data structure.

        Returns
        -------
        `dict`
            Heartbeat message.
        """
        return dict(
            category="event",
            producer_snd=0,
            data=[
                dict(
                    csc="ScriptHeartbeats",
                    salindex=self.remote.salinfo.index,
                    data=dict(
                        stream=dict(
                            script_heartbeat=dict(
                                salindex=script_index,
                                lost=0,
                                last_heartbeat_timestamp=-1.0,
                            ),
                        ),
                    ),
                ),
            ],
        )

    @property
    def scriptqueue_state_message_data(self) -> dict:
        """Script queue state message.

        The data structure matches the required by the manager/frontend view.
        """

        data = dict(
            enabled=self.state["enabled"],
            running=self.state["running"],
        )

        return dict(
            csc="ScriptQueueState",
            salindex=self.remote.salinfo.index,
            data=dict(stateStream=data),
        )

    @property
    def scripts_state_message_data(self) -> dict:
        """Scripts state message.

        The data structure matches the required by the manager/frontend view.
        """

        data = dict(
            current_scripts=[
                self.scripts[index] for index in self.state["currentIndices"]
            ],
            waiting_scripts=[
                self.scripts[index] for index in self.state["waitingIndices"]
            ],
            finished_scripts=[
                self.scripts[index] for index in self.state["finishedIndices"]
            ],
        )

        return dict(
            csc="ScriptQueueState",
            salindex=self.remote.salinfo.index,
            data=dict(scriptsStream=data),
        )

    @property
    def available_scripts_state_message_data(self) -> dict:
        """Available scripts message.

        The data structure matches the required by the manager/frontend view.
        """

        available_scripts = [
            dict(
                type="standard",
                path=script_path,
                configSchema=self.available_scripts["standard"][script_path],
            )
            for script_path in self.available_scripts["standard"]
        ] + [
            dict(
                type="external",
                path=script_path,
                configSchema=self.available_scripts["external"][script_path],
            )
            for script_path in self.available_scripts["external"]
        ]

        data = dict(
            available_scripts=available_scripts,
        )

        return dict(
            csc="ScriptQueueState",
            salindex=self.remote.salinfo.index,
            data=dict(availableScriptsStream=data),
        )

    def get_scriptqueue_state_message_as_json(self) -> str:
        """Parses the current state into a LOVE friendly format.

        Returns
        -------
        `str`
            ScriptQueue state message.
        """

        return self._love_manager_message.get_message_category_as_json(
            category="event",
            data=self.scriptqueue_state_message_data,
        )

    def get_scripts_state_message_as_json(self) -> str:
        """Parses the current scripts state into a LOVE friendly format.

        Returns
        -------
        `str`
            Scripts state message.
        """

        return self._love_manager_message.get_message_category_as_json(
            category="event",
            data=self.scripts_state_message_data,
        )

    def get_available_scripts_state_message_as_json(self) -> str:
        """Parses the available scripts into a LOVE friendly format.

        Returns
        -------
        `str`
            Available scripts message.
        """

        return self._love_manager_message.get_message_category_as_json(
            category="event",
            data=self.available_scripts_state_message_data,
        )

    async def send_scriptqueue_state(self):
        """Send script queue state."""
        await self.send_message(self.get_scriptqueue_state_message_as_json())

    async def send_scripts_state(self):
        """Send scripts state."""
        await self.send_message(self.get_scripts_state_message_as_json())

    async def send_available_scripts(self):
        """Send available scripts."""
        await self.send_message(self.get_available_scripts_state_message_as_json())

    async def send_script_heartbeat(self, salindex: int) -> None:
        """Send heartbeat message from script.

        Parameters
        ----------
        salindex : `int`
            Index of the script.
        """
        await self.send_message(
            self._love_manager_message.get_message_as_json(
                self._get_script_heartbeat_message(salindex)
            )
        )

    async def send_script_log_message(self, message_data: dict) -> None:
        """Send log messages from the current script.

        Parameters
        ----------
        message_data : `dict`
            Payload of the message with the request to send script log message.
        """

        # The ScriptQueue CSC will be extended to support multiple
        # current scripts in the future. For now, only one is supported.
        # See: DM-44198.
        log_messages = [
            message
            for index in self.state["currentIndices"]
            for message in self.scripts_log_messages.get(index, [])
        ]

        try:
            for message in log_messages:
                await self.send_message(
                    self._love_manager_message.get_message_as_json(message)
                )
        except Exception:
            self.log.exception("Error sending script log message.")

    def _get_script_heartbeat_message(self, salindex: int) -> Dict:
        """Get script heartbeat message.

        Parameters
        ----------
        salindex : `int`
            Index of the script.

        Returns
        -------
        script_heartbeat_message : `dict`
            Script heartbeat message.
        """
        if salindex not in self.scripts_heartbeat:
            self.add_new_script(salindex)
        script_heartbeat_message = self.scripts_heartbeat[salindex]
        last_heartbeat_timestamp = script_heartbeat_message["data"][0]["data"][
            "stream"
        ]["script_heartbeat"]["last_heartbeat_timestamp"]

        if (
            last_heartbeat_timestamp
            < datetime.now().timestamp()
            - SCRIPT_HEARTBEAT_INTERVAL
            - self.heartbeat_timeout
        ):
            script_heartbeat_message["data"][0]["data"]["stream"]["script_heartbeat"][
                "lost"
            ] += 1
        else:
            script_heartbeat_message["data"][0]["data"]["stream"]["script_heartbeat"][
                "lost"
            ] = 0

        return script_heartbeat_message

    async def close(self):
        await self.remote_scripts.close()
        return await super().close()

    async def set_script_heartbeat_producer(self) -> None:
        if self._script_heartbeat_producer_task is not None:
            raise RuntimeError("Script hearbeat producer already set.")

        self._script_heartbeat_producer_task = asyncio.create_task(
            self._produce_script_heartbeat()
        )

    async def _produce_script_heartbeat(self) -> None:
        """Produce script heartbeat messages."""
        while not self.done_task.done():
            try:
                scripts_indices = (
                    self.state["currentIndices"] + self.state["waitingIndices"]
                )
                self.log.debug(f"Sending HB for scripts: {scripts_indices}.")

                for script_id in scripts_indices:
                    await self.send_script_heartbeat(script_id)
            except Exception:
                self.log.exception("Error sending script heartbeats.")

            await asyncio.sleep(self.heartbeat_timeout)

    def monitor_script_heartbeat_callback(self, data: Any) -> None:
        """Callback to monitor script heartbeat.

        Parameters
        ----------
        data : `Script_logevent_heartbeat`
            Script heartbeat topic sample.
        """

        if data.salIndex in self.scripts_heartbeat:
            self.scripts_heartbeat[data.salIndex]["data"][0]["data"]["stream"][
                "script_heartbeat"
            ]["last_heartbeat_timestamp"] = datetime.now().timestamp()

    async def monitor_script_log_message_callback(self, data: Any) -> None:
        """Callback to monitor script log messages.

        Parameters
        ----------
        data :  `Script_logevent_logMessage`
        """

        if data.salIndex in self.scripts_log_messages:
            _, data_as_dict = self._convert_data_to_dict(data)
            data_as_dict["csc"] = "Script"
            data_as_dict["salindex"] = data.salIndex

            message_as_dict = dict(
                category="event",
                producer_snd=0,
                data=[
                    data_as_dict,
                ],
            )

            self.scripts_log_messages[data.salIndex].append(message_as_dict)

            self.log.debug(f"Received script log message: {data.message}")
            if (
                data.salIndex in self.state["currentIndices"]
                or data.salIndex in self.state["waitingIndices"]
            ):
                await self.send_message(
                    self._love_manager_message.get_message_as_json(message_as_dict)
                )

    @property
    def reply_names(self) -> str:
        return {
            "ScriptQueue",
            "ScriptQueueState",
            "Script",
        }
