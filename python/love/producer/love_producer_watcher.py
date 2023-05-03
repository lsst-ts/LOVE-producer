# This file is part of LOVE-producer.
#
# Developed for Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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

__all__ = ["LoveProducerWatcher"]

import logging
from typing import Any, Optional
from lsst.ts.salobj import Domain

from . import LoveProducerCSC


class LoveProducerWatcher(LoveProducerCSC):
    """Specialized LOVE producer to deal with the Watcher CSC."""

    def __init__(self, domain: Domain, log: Optional[logging.Logger] = None, **kwargs) -> None:
        kwargs_reformatted = kwargs.copy()
        if "csc" in kwargs_reformatted:
            kwargs_reformatted.pop("csc")

        super().__init__(
            domain=domain,
            csc="Watcher",
            log=log,
            remote_readonly=False,
            **kwargs_reformatted,
        )

        self.alarms_state = []
        
        self._non_topic_data_stream = {"stream"}

        self.register_additional_action(
            "evt_alarm", self.handle_event_watcher_alarm
        )

        self.register_asynchronous_data_category("stream", "_stream")
        self.store_samples(_stream=self.alarms_state_message_data)

    async def handle_event_watcher_alarm(self, event: Any) -> None:
        """Handle the Watcher_logevent_alarm event.

        Parameters
        ----------
        event : `Watcher_logevent_script`
            Watcher_logevent_script event data.
        
        Notes
        -----
        This method is registered as an additional action for the
        Watcher_logevent_alarm event. It stores alarms in the
        `alarms_state` attribute and sends them to the LOVE manager.
        """
        new_alarm = dict()
        new_alarm["name"] = event.name
        new_alarm["severity"] = event.severity
        new_alarm["max_severity"] = event.maxSeverity
        self.alarms_state.append(new_alarm)
        self.store_samples(_stream=self.alarms_state_message_data)
        await self.send_watcher_alarms()

    async def send_watcher_alarms(self) -> None:
        """Send the watcher alarms to the LOVE manager."""
        await self.send_message(self.get_alarms_state_as_json())
    
    def get_alarms_state_as_json(self) -> str:
        """Get the alarms state as a JSON string."""
        return self._love_manager_message.get_message_category_as_json(
            category="event",
            data=self.alarms_state_message_data,
        )
    
    @property
    def alarms_state_message_data(self) -> dict:
        """Get the alarms state as a dictionary."""
        data = dict(
            alarms=self.alarms_state,
        )
        return dict(
            csc="Watcher",
            salindex=self.remote.salinfo.index,
            data=dict(stream=data),
        )

