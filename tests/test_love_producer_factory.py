# This file is part of ts_salobj.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by Inria Chile and
# the LSST Project (https://www.lsst.org).
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

import unittest

from love.producer import LoveProducerFactory, LoveProducerBase


class TestLoveProducerFactory(unittest.IsolatedAsyncioTestCase):
    async def test_get_love_producer_from_type_base(self):
        base_love_producer = LoveProducerFactory.get_love_producer_from_type("base")

        self.assertIsInstance(base_love_producer, LoveProducerBase)

    async def test_get_love_producer_from_type_unspecified(self):
        with self.assertRaises(RuntimeError):
            LoveProducerFactory.get_love_producer_from_type("unspecified")

    async def test_get_love_producer_from_name(self):
        component_name = "UnitTest1"

        love_producer = LoveProducerFactory.get_love_producer_from_name(component_name)

        self.assertIsInstance(love_producer, LoveProducerBase)
        self.assertEqual(component_name, love_producer.component_name)


if __name__ == "__main__":
    unittest.main()
