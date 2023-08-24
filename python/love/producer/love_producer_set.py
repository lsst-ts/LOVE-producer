# This file is part of LOVE-producer.
#
# Developed for Inria Chile and Vera C. Rubin Observatory Telescope
# and Site Systems.
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

__all__ = ["LoveProducerSet", "run_love_producer"]

import os
import signal
import asyncio
import logging
import argparse

from lsst.ts import salobj

from . import LoveManagerClient

logging.basicConfig(level=logging.DEBUG)


class LoveProducerSet:
    """Container class to configure and host a list of LOVE producers."""

    def __init__(self, components, log_level=logging.INFO) -> None:
        self.log = logging.getLogger()

        if not self.log.hasHandlers():
            self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(log_level)

        self.love_manager_client = LoveManagerClient(
            log=self.log,
        )

        self.domain = salobj.Domain()

        self.love_manager_client.create_producers(
            components=components,
            domain=self.domain,
            log=self.log,
        )

        self.standard_timeout = 5.0

        self._wait_forever_task = None

    async def run_producer(self):
        start_task = asyncio.create_task(
            self.love_manager_client.handle_connection_with_manager()
        )

        loop = asyncio.get_running_loop()
        for signal_value in (
            signal.SIGTERM,
            signal.SIGINT,
            signal.SIGHUP,
        ):
            loop.add_signal_handler(signal_value, self.signal_handler)

        self._wait_forever_task = asyncio.Future()

        for task in asyncio.as_completed(
            [
                self._wait_forever_task,
                start_task,
            ]
        ):
            try:
                await task
            except Exception:
                self.log.exception("Error in execution task.")
            finally:
                break

        self.log.warning("Terminating...")

        await self.love_manager_client.close()
        await self.domain.close()

    def signal_handler(self):
        self.log.warning(f"ComponentProducerSet.signal_handler for pid={os.getpid()}")
        self._wait_forever_task.set_result(None)

    @classmethod
    async def amain(cls):
        """Parse command line arguments, create and run a
        `LoveManagerClient`.
        """
        parser = cls.make_argument_parser()
        args = parser.parse_args()

        logging.basicConfig(level=args.log_level)

        if len(args.components) == 0:
            raise RuntimeError(
                "At least one component must be provided. "
                "See `--help` for more information."
            )

        love_producer_set = cls(
            components=args.components,
            log_level=args.log_level,
        )

        await love_producer_set.run_producer()

    @classmethod
    def make_argument_parser(cls):
        """Make command line arguments."""

        parser = argparse.ArgumentParser(
            description="Produce DDS messages to LOVE for one or more SAL components.",
        )

        parser.add_argument(
            "components",
            nargs="*",
            help="Names of SAL components, e.g. ATDome, ATDomeTrajectory, MTHexapod:1.",
        )

        parser.add_argument(
            "--log-level",
            type=int,
            dest="log_level",
            default=logging.INFO,
            help="Logging level; INFO=20 (default), DEBUG=10",
        )

        return parser


def run_love_producer():
    """Run love producer."""
    asyncio.run(LoveProducerSet.amain())
