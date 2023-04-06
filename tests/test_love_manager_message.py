# This file is part of ts_salobj.
#
# Developed for the Rubin Observatory Telescope and Site System.
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

import json
import logging
import unittest

from love.producer import LoveManagerMessage


class TestLoveManagerMessage(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger(__name__)

    def setUp(self):
        self.component_name = "UnitTest"
        self.love_manager_message = LoveManagerMessage(
            component_name=self.component_name
        )
        self.sample_telemetry = dict(
            test_value_int=10,
            test_value_string="test",
            test_value_float=1.0 / 3.0,
        )

    def test_get_message_initial_state(self):
        initial_state_message = self.love_manager_message.get_message_initial_state()

        self.assert_initial_state_message(initial_state_message, self.component_name)

    def test_get_message_category(self):
        telemetry = self.love_manager_message.get_message_category(
            category="telemetry", data=self.sample_telemetry
        )

        self.assert_data_category(telemetry, "telemetry")

    def test_get_message_initial_state_as_json(self):
        initial_state_json = (
            self.love_manager_message.get_message_initial_state_as_json()
        )

        self.assert_initial_state_message(
            json.loads(initial_state_json), self.component_name
        )

    def test_get_message_category_as_json_empty_data(self):
        telemetry_json = self.love_manager_message.get_message_category_as_json(
            category="telemetry", data=dict()
        )

        self.assert_data_category(json.loads(telemetry_json), "telemetry")

    def test_get_message_category_as_json(self):
        telemetry_json = self.love_manager_message.get_message_category_as_json(
            category="telemetry", data=self.sample_telemetry
        )

        self.assert_data_category(json.loads(telemetry_json), "telemetry")

    def test_add_metadata(self):
        self.love_manager_message.add_metadata(new_metadata="test_value")

        telemetry_json = self.love_manager_message.get_message_category_as_json(
            category="telemetry", data=self.sample_telemetry
        )

        self.log.debug(f"{telemetry_json}")
        telemetry_data = json.loads(telemetry_json)

        self.assert_data_category(telemetry_data, "telemetry")
        self.assertIn("new_metadata", telemetry_data)
        self.assertEqual("test_value", telemetry_data["new_metadata"])

    def assert_initial_state_message(self, initial_state_message, component_name):
        for key, value in [
            ("option", "subscribe"),
            ("category", "initial_state"),
            ("csc", component_name),
            ("salindex", "all"),
            ("stream", "all"),
        ]:
            self.assertIn(key, initial_state_message)
            self.assertEqual(initial_state_message[key], value)

    def assert_data_category(self, data, category):
        for key in {"category", "data"}:
            self.assertIn(key, data)

        self.assertEqual(data["category"], category)


if __name__ == "__main__":
    unittest.main()
