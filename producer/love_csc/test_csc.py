import json
import asyncio

import asynctest
from lsst.ts import salobj

from love_csc.csc import LOVECsc
from .. import test_utils

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestLOVECsc(asynctest.TestCase):
    observing_log_username = "a user"
    observing_log_message = "a message"

    async def test_add_observing_log(self):
        """Test that logs work directly from the csc method """

        # Arrange
        salobj.set_random_lsst_dds_partition_prefix()
        self.csc = LOVECsc()
        self.remote = salobj.Remote(domain=self.csc.domain, name="LOVE")
        await self.csc.start_task
        await self.remote.start_task

        # Act: write down some logs and get the results from the event
        self.remote.evt_observingLog.flush()
        self.csc.add_observing_log(self.observing_log_username, "a message")

        # Assert
        result = await self.remote.evt_observingLog.next(flush=False)
        self.assertEqual(result.user, self.observing_log_username)
        self.assertEqual(result.message, self.observing_log_message)

        # clean up
        await self.csc.close()
        await self.remote.close()


class TestWebsocketsClient(test_utils.WSClientTestCase):
    async def test_csc_client(self):
        async def arrange():
            from love_csc.client import LOVEWSClient

            salobj.set_random_lsst_dds_partition_prefix()
            self.remote = salobj.Remote(domain=salobj.Domain(), name="LOVE")
            await self.remote.start_task
            self.client = LOVEWSClient()
            self.client_task = asyncio.create_task(self.client.start_ws_client())

        async def cleanup():
            # cleanup
            self.client.retry = False
            self.client_task.cancel()
            await self.client_task

            await self.client.csc.close()
            await self.remote.close()

        async def act_assert(websocket, path):
            """Server-ready callback. Runs the test actions and assertions"""
            # wait for the client to connect to initial_state group
            initial_subscription = await websocket.recv()
            self.assertEqual(
                json.loads(initial_subscription),
                {
                    "option": "subscribe",
                    "category": "initial_state",
                    "csc": "all",
                    "salindex": "all",
                    "stream": "all",
                },
            )

            # wait for the client to connect to the love_csc-love-0-observingLog group
            observing_log_subscription = await websocket.recv()
            self.assertEqual(
                json.loads(observing_log_subscription),
                {
                    "option": "subscribe",
                    "category": "love_csc",
                    "csc": "love",
                    "salindex": "0",
                    "stream": "observingLog",
                },
            )

            # Act
            # send observing logs form the server (manager)
            # self.remote.evt_observingLog.flush()
            # message = utils.make_stream_message(
            #     "love_csc",
            #     "love",
            #     0,
            #     "observingLog",
            #     {
            #         "user": self.observing_log_username,
            #         "message": self.observing_log_message,
            #     },
            # )

            # await websocket.send(json.dumps(message))

            # Assert the DDS received the log message
            # result = await self.remote.evt_observingLog.next(
            #     flush=False, timeout=STD_TIMEOUT
            # )
            # self.assertEqual(result.user, self.observing_log_username)
            # self.assertEqual(result.message, self.observing_log_message)

        await self.harness(act_assert, arrange, cleanup)
