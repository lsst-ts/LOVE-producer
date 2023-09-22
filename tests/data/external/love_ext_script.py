#!/usr/bin/env python
# This file is part of LOVE-producer.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by Inria Chile and
# the LSST Project (https://www.lsst.org).
#
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

__all__ = ["LoveExtScript"]

import yaml
import asyncio

from lsst.ts.salobj import BaseScript


class LoveExtScript(BaseScript):
    """A dummy external script script to test love interaction with
    the queue.

    Parameters
    ----------
    index : `int`
        Index of Script SAL component.

    Wait for the specified time, then exit. See `configure` for details.
    """

    __test__ = False  # stop pytest from warning that this is not a test

    def __init__(self, index):
        super().__init__(index=index, descr="Love test external script.")

        self.sleep_time = 0.0

    @classmethod
    def get_schema(cls):
        schema_yaml = """
$schema: http://json-schema.org/draft-07/schema#
$id: https://github.com/lsst-ts/LOVE-producer/blob/develop/tests/data/external/love_ext_script.py
title: LoveExtScript v1
description: Configuration for LoveExtScript.
type: object
properties:
    sleep_time:
        description: How long to sleep for.
        type: number
        default: 0.0
additionalProperties: false
        """
        return yaml.safe_load(schema_yaml)

    async def configure(self, config):
        """Configure the script."""

        self.log.info("Configure started")

        self.sleep_time = config.sleep_time

        self.log.info("Configure completed")

    def set_metadata(self, metadata):
        """Fill in metadata information.

        Parameters
        ----------
        metadata

        """
        metadata.duration = self.sleep_time

    async def run(self):
        self.log.info("Run started")
        await self.checkpoint("start")

        await asyncio.sleep(self.sleep_time)

        await self.checkpoint("end")
        self.log.info("Run succeeded")


if __name__ == "__main__":
    asyncio.run(LoveExtScript.amain())
