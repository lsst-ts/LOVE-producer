import asynctest
import logging
from .csc import LOVECsc
import asyncio
from lsst.ts import salobj
import utils

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestLOVECsc(asynctest.TestCase):
    async def setUp(self):
        salobj.set_random_lsst_dds_domain()
        self.csc = LOVECsc()
        self.remote = salobj.Remote(domain=self.csc.domain, name="LOVE")

    async def tearDown(self):
        await asyncio.wait_for(self.csc.close(), STD_TIMEOUT)
        await asyncio.wait_for(self.remote.close(), STD_TIMEOUT)

    async def test_produced_message_with_event_arrays(self):
        # Arrange
        # Setup the producer and the data

        # Act

        # Assert
        self.assertEqual(True, True)
