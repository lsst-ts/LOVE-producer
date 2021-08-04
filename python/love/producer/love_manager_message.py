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

__all__ = ["NumpyEncoder", "LoveManagerMessage"]

import json

import numpy as np

from typing import Any


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> json.JSONEncoder:
        if isinstance(obj, (np.bool, np.bool_)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(
            obj,
            (np.uint8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32),
        ):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


class LoveManagerMessage:
    def __init__(self, component_name: str) -> None:

        self.component_name: str = component_name
        self.metadata: dict = dict()

    def get_message_as_json(self, data: dict) -> str:
        return json.dumps(data, cls=NumpyEncoder)

    def get_message_initial_state(self) -> dict:

        return dict(
            option="subscribe",
            category="initial_state",
            csc=self.component_name,
            salindex="all",
            stream="all",
        )

    def get_message_initial_state_as_json(self) -> str:
        return self.get_message_as_json(self.get_message_initial_state())

    def get_message_telemetry(self, data: dict) -> dict:
        return dict(category="telemetry", data=data, **self.metadata)

    def get_message_telemetry_as_json(self, data: dict) -> str:
        return self.get_message_as_json(self.get_message_telemetry(data=data))

    def add_metadata(self, **kwargs) -> None:
        for key in kwargs:
            self.metadata[key] = kwargs[key]
