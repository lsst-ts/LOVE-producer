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

__all__ = ["LoveProducerCSC"]

import asyncio
import copy
import datetime
import logging
from typing import Any, Awaitable, Optional, Tuple

from lsst.ts.salobj import Domain, Remote

from . import LoveProducerBase
from .producer_utils import get_data_type


class LoveProducerCSC(LoveProducerBase):
    """Specialized LOVE producer to deal with generic CSC behavior."""

    def __init__(
        self, domain: Domain, csc: str, log: Optional[logging.Logger] = None, **kwargs
    ) -> None:
        super().__init__(component_name=csc, log=log)

        self.add_metadata(**kwargs)

        self.remote: Remote = Remote(
            domain,
            csc,
            index=kwargs.get("salindex", 0),
            readonly=kwargs.get("remote_readonly", True),
        )

        self._events_special_cases = {"evt_heartbeat"}

        self._non_topic_data_stream = {}

        self._revcode_topic_attribute_name_map: dict = dict()
        self._template_manager_message: dict = dict()

        self._need_reply_category = {"initial_state"}

        self.periodic_data: list = self.get_periodic_data(**kwargs)
        self.asynchronous_data: list = self.get_asynchronous_data(**kwargs)

        self.store_last_sample_timeout: float = 0.5
        self.heartbeat_timeout = 2.0
        self.heartbeat_max_lost = 5

        self.set_topic_name_revcode_mapping()
        self.set_topic_template_manager_message_format()

        self._heartbeat_monitor_task = None
        self.done_task: asyncio.Future = asyncio.Future()

        self.start_task: Awaitable = asyncio.create_task(self.start())

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
        category = message_data.get("category", None)
        data = message_data.get("data", [dict()])[0]
        csc = data.get("csc", None)
        salindex = data.get("salindex", 0)

        try:
            self.log.debug(
                "Should reply to message_data: "
                f"{category in self._need_reply_category}, "
                f"{csc in self.reply_names}, "
                f"{salindex == self.remote.salinfo.index}, "
                f"{self.is_data_stream_stored(dict(stream=self.get_sample_name(message_data)))}. "
                f"stream={self.get_sample_name(message_data)}"
            )

            return (
                (category in self._need_reply_category)
                and csc in self.reply_names
                and salindex == self.remote.salinfo.index
                and self.is_data_stream_stored(
                    dict(stream=self.get_sample_name(message_data))
                )
            )
        except Exception:
            self.log.exception("Error in should reply to message. Won't reply.")
            return False

    def get_sample_name(self, data_stream: dict) -> str:
        """Override base class default behavior."""
        topic_name = data_stream["data"][0]["data"]["event_name"]
        topic_prefix = self._get_topic_prefix(topic_name=topic_name)
        return f"{topic_prefix}_{topic_name}"

    def get_periodic_data(self, **kwargs) -> dict:
        return dict(
            set(
                self.get_telemetry_attribute_names_and_category()
                if kwargs.get("periodic_data", None) is None
                else self.generate_valid_topic_attribute_names(kwargs["periodic_data"])
            )
        )

    def get_asynchronous_data(self, **kwargs) -> dict:
        return dict(
            set(
                self.get_event_attribute_names_and_category()
                if kwargs.get("asynchronous_data", None) is None
                else self.generate_valid_topic_attribute_names(
                    kwargs["asynchronous_data"]
                )
            )
            - self._events_special_cases
        )

    def get_event_attribute_names_and_category(self) -> list:
        return [
            (f"evt_{event_name}", "event")
            for event_name in self.remote.salinfo.event_names
        ]

    def get_telemetry_attribute_names_and_category(self) -> list:
        return [
            (f"tel_{telemetry_name}", "telemetry")
            for telemetry_name in self.remote.salinfo.telemetry_names
        ]

    def _get_topic_prefix(self, topic_name: str) -> str:
        """Return the prefix for a given topic name, e.g., `evt` for events,
        `tel` for telemetry.

        Parameters
        ----------
        topic_name : `str`

        Returns
        -------
        prefix : `str`
            Prefix for the given topic name.

        Raises
        ------
        RuntimeError :
            If `topic_name` is invalid.
        """

        if topic_name in self._non_topic_data_stream:
            return ""

        topic_names_valid = (
            self.remote.salinfo.event_names + self.remote.salinfo.telemetry_names
        )

        if topic_name not in topic_names_valid:
            raise RuntimeError(
                f"Invalid topic name for {self.component_name}: {topic_name}. "
                f"Must be a valid event or telemetry name: {topic_names_valid}"
            )

        prefix = "evt" if topic_name in self.remote.salinfo.event_names else "tel"

        return prefix

    def generate_valid_topic_attribute_names(self, periodic_data: list) -> list:
        """For each entry in `periodic_data` check that is it part of the
        producer list of topics and return a valid list.

        The names in the input list must follow the same rule as the topics in
        the remote. For instance, telemetry topics must be preceeded by `tel_`
        and events by `evt_`.

        Parameters
        ----------
        periodic_data: `list` of `str`
            List of topic names (precedeed by type).

        Returns
        -------
        periodic_data_list: `list`
            Validated list of periodic names.
        """

        periodic_data_list = []

        for topic_object_name in periodic_data:
            topic_type, topic_name = topic_object_name.split("_", maxsplit=1)
            if (
                topic_type == "tel"
                and topic_name in self.remote.salinfo.telemetry_names
            ):
                self.log.debug(f"Adding {topic_object_name} to periodic data list.")
                periodic_data_list.append((topic_object_name, "telemetry"))
            elif topic_type == "evt" and topic_name in self.remote.salinfo.event_names:
                self.log.debug(f"Adding {topic_object_name} to periodic data list.")
                periodic_data_list.append((topic_object_name, "event"))
            else:
                self.log.warning(
                    f"Topic {topic_object_name} is not a valid topic name. Check your input data."
                )

        return periodic_data_list

    async def start(self) -> None:
        await self.remote.start_task

        await self.set_monitor_periodic_data()
        await self.set_monitor_asynchronous_data()
        await self.set_monitor_heartbeat()

    def set_topic_name_revcode_mapping(self) -> None:
        """Create a mapping between topic name and revcode for all topics so
        the producer can assign the name of the topics from the samples.
        """
        for periodic_topic in self.periodic_data:
            self.log.debug(f"creating mapping for {periodic_topic}")
            self.create_revcode_mapping(periodic_topic)

        for asynchronous_topic in self.asynchronous_data:
            self.log.debug(f"creating mapping for {asynchronous_topic}")
            self.create_revcode_mapping(asynchronous_topic)

    def get_topic_attribute_name(self, rev_code: str) -> str:
        """Returns the associated topic attribute name (e.g. evt_heartbeat) for
        a given rev_code.

        Parameters
        ----------
        rev_code: `str`
            Revision code of the topic.

        Returns
        -------
        `str`
            Topic attribute name, e.g. evt_heartbeat.
        """

        return self._revcode_topic_attribute_name_map[rev_code]

    def create_revcode_mapping(self, topic_attribute_name: str) -> None:
        """For a given topic name, create a revcode mapping.

        Parameters
        ----------
        topic_attribute_name: `str`
            Name of the topic attribute, e.g. evt_heartbeat.
        """

        self._set_revcode_mapping(
            getattr(self.remote, topic_attribute_name).rev_code,
            topic_attribute_name,
        )

    def _set_revcode_mapping(self, rev_code: str, topic_attribute_name: str) -> None:
        """Set the rev code -> topic attribute name mapping.

        Parameters
        ----------
        rev_code : `str`
            The rev_code of the topic.

        topic_attribute_name : `str`
            Name of the topic attribute, e.g. evt_heartbeat.
        """
        self._revcode_topic_attribute_name_map[rev_code] = topic_attribute_name

    async def set_monitor_periodic_data(self) -> None:
        for periodic_data_name in self.periodic_data:
            self.register_monitor_data_periodically(
                getattr(self.remote, periodic_data_name).get,
                category=self.periodic_data[periodic_data_name],
            )

    def set_topic_template_manager_message_format(self) -> None:
        """Generate manager message format for each registered topic."""
        for periodic_topic in self.periodic_data:
            self.log.debug(f"creating manager message for {periodic_topic}")
            self.create_template_manager_message(periodic_topic)

        for asynchronous_topic in self.asynchronous_data:
            self.log.debug(f"creating manager message for {asynchronous_topic}")
            self.create_template_manager_message(asynchronous_topic)

    def create_template_manager_message(self, topic_name):
        """Create template manager message for given topic."""

        topic = getattr(self.remote, topic_name)

        self._set_template_manager_message(topic_name=topic_name, topic=topic)

    def _set_template_manager_message(self, topic_name: str, topic: object) -> None:
        """Cache manager message template for future use.

        Parameters
        ----------
        topic_name : `str`
            Name of the topic. This will
        """
        topic_data = topic.DataType().get_vars()

        self._template_manager_message[topic_name] = {
            topic_attribute: {
                "value": topic_data[topic_attribute],
                "dataType": get_data_type(topic_data[topic_attribute]),
                "units": f"{topic.metadata.field_info[topic_attribute].units}",
            }
            for topic_attribute in topic.metadata.field_info
        }

    async def set_monitor_asynchronous_data(self) -> None:
        await asyncio.gather(
            *[
                self.set_asynchronous_monitor_for(
                    asynchronous_data_name,
                    self.asynchronous_data[asynchronous_data_name],
                )
                for asynchronous_data_name in self.asynchronous_data
                if asynchronous_data_name not in self._events_special_cases
            ]
        )

    async def set_asynchronous_monitor_for(
        self, asynchronous_data_name: str, asynchronous_data_category: str
    ) -> None:
        self.log.debug(
            f"Getting last sample of {asynchronous_data_name} before setting callback."
        )
        await self.store_last_sample(asynchronous_data_name)

        self.register_asynchronous_data_category(
            asynchronous_data_name, asynchronous_data_category
        )

        getattr(self.remote, asynchronous_data_name).callback = (
            self.handle_asynchronous_data_callback
        )

    async def set_monitor_heartbeat(self):
        if hasattr(self.remote, "evt_heartbeat"):
            self.log.debug(
                f"Adding heartbeat monitor for {self.remote.salinfo.name}:{self.remote.salinfo.index}"
            )
            self._heartbeat_monitor_task = asyncio.create_task(
                self._monitor_heartbeat()
            )
        else:
            self.log.warning(
                "Skipping heartbeat monitor. Remote created without heartbeat event."
            )

    async def _monitor_heartbeat(self):
        heartbeat_message = self._get_heartbeat_message()

        heartbeat_send_timer = asyncio.create_task(
            asyncio.sleep(self.heartbeat_timeout)
        )

        while not self.done_task.done():
            (
                heartbeat_message["data"][0]["data"]["stream"]["lost"],
                heartbeat_message["data"][0]["data"]["stream"][
                    "last_heartbeat_timestamp"
                ],
            ) = await self._handle_heartbeat(heartbeat_message)

            try:
                if heartbeat_send_timer.done():
                    heartbeat_message["producer_snd"] = (
                        datetime.datetime.now().timestamp()
                    )

                    await self.send_message(
                        self._love_manager_message.get_message_as_json(
                            heartbeat_message
                        )
                    )
                    heartbeat_send_timer = asyncio.create_task(
                        asyncio.sleep(self.heartbeat_timeout)
                    )

            except Exception as e:
                self.log.exception("Error sending message in monitor heartbeat.")
                raise e

    async def store_last_sample(self, sample_name: str) -> None:
        try:
            last_sample = await getattr(self.remote, sample_name).aget(
                timeout=self.store_last_sample_timeout
            )
        except asyncio.TimeoutError:
            self.log.debug(f"No {sample_name} sample received.")
            return

        await self.handle_asynchronous_data_callback(last_sample)

    def _get_heartbeat_message(self) -> dict:
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
                    csc="Heartbeat",
                    salindex=0,
                    data=dict(
                        stream=dict(
                            csc=self.remote.salinfo.name,
                            salindex=self.remote.salinfo.index,
                            lost=0,
                            last_heartbeat_timestamp=-1,
                            max_lost_heartbeats=self.heartbeat_max_lost,
                        )
                    ),
                ),
            ],
        )

    async def _handle_heartbeat(self, heartbeat_message: dict) -> Tuple[int, float]:
        """Handler heartbeat reception.

        Parameters
        ----------
        heartbeat_message : `dict`
            Heartbeat message dictionary.

        Returns
        -------
        heartbeat_lost : `int`
            Number of heartbeat losts.
        last_heartbeat_timestamp : `float`
            Timestamp of the last hearbeat.
        """
        heartbeat_lost = heartbeat_message["data"][0]["data"]["stream"]["lost"]
        last_heartbeat_timestamp = heartbeat_message["data"][0]["data"]["stream"][
            "last_heartbeat_timestamp"
        ]

        try:
            await self.remote.evt_heartbeat.next(
                flush=True, timeout=self.heartbeat_timeout
            )
            heartbeat_lost = 0
            last_heartbeat_timestamp = datetime.datetime.now().timestamp()
        except asyncio.TimeoutError:
            self.log.debug("Timeout waiting for hearbeat.")
            heartbeat_lost += 1
        except Exception as e:
            self.log.exception("Error waiting for heartbeat.")
            raise e

        return heartbeat_lost, last_heartbeat_timestamp

    def _convert_data_to_dict(self, data: Any) -> Tuple[str, dict]:
        """Convert SalObj topic data to dictionary.

        Parameters
        ----------
        data:
            SalObj topic data to convert to dictionary.

        Returns
        -------
        name: `str`
            Assigned name of the kind of data stream.
        data_as_dict: `dict`
            Dictionary with the data payload.

        """
        topic_attribute_name = self.get_topic_attribute_name(data.private_revCode)
        _, topic_name = topic_attribute_name.split("_", maxsplit=1)

        data_stream = copy.deepcopy(
            self._template_manager_message[topic_attribute_name]
        )
        data_vars = data.get_vars()

        for topic_attribute in data_vars:
            data_stream[topic_attribute]["value"] = data_vars[topic_attribute]

        payload = (
            data_stream
            if topic_attribute_name in self.periodic_data
            else [
                data_stream,
            ]
        )

        data_as_dict = dict(
            csc=self.remote.salinfo.name,
            salindex=self.remote.salinfo.index,
            data=dict(
                [
                    (topic_name, payload),
                ],
            ),
        )
        return topic_attribute_name, data_as_dict

    async def close(self):
        self.done_task.set_result(0)

        try:
            await self._heartbeat_monitor_task
        except asyncio.CancelledError:
            self.log.exception("Heartbeat monitor task cancelled.")
        except Exception as e:
            self.log.exception("Exception in heartbeat monitor task.")
            raise e
        finally:
            await self.remote.close()

    @property
    def reply_names(self) -> str:
        return {self.remote.salinfo.name}
