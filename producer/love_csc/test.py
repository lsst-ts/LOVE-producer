import asynctest
from asynctest import mock
import os
import asyncio
from lsst.ts import salobj
import websockets
from love_csc.csc import LOVECsc
import utils
import json

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestLOVECsc(asynctest.TestCase):
    async def test_add_observing_log(self):
        """Test that logs work directly from the csc method """
        salobj.set_random_lsst_dds_domain()
        # Arrange
        self.csc = LOVECsc()
        self.remote = salobj.Remote(domain=self.csc.domain, name="LOVE")
        await self.csc.start_task
        await self.remote.start_task

        # Act: write down some logs and get the results from the event
        self.remote.evt_observingLog.flush()
        self.csc.add_observing_log('an user', 'a message')

        # Assert
        result = await self.remote.evt_observingLog.next(flush=False)
        self.assertEqual(result.user, 'an user')
        self.assertEqual(result.message, 'a message')

        # clean up
        await self.csc.close()
        await self.remote.close()


class TestWebsocketsClient(asynctest.TestCase):
    @mock.patch.dict(os.environ, {'WEBSOCKET_HOST': '0.0.0.0:9999', 'PROCESS_CONNECTION_PASS': ''})
    async def harness(self, act_assert, arrange, cleanup):
        test_finished = asyncio.Future()
        async def act_assert_wrapper(*args, **kwargs):
            await act_assert(*args, **kwargs)
            test_finished.set_result(True)

        async with websockets.serve(act_assert_wrapper, '0.0.0.0', 9999):
            await arrange()
            await asyncio.wait_for(test_finished, timeout=STD_TIMEOUT*2)
            await cleanup()

    async def test_csc_client(self):
        async def arrange():
            from love_csc.client import LOVEWSClient
            salobj.set_random_lsst_dds_domain()
            self.remote = salobj.Remote(domain=salobj.Domain(), name="LOVE")
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
            self.assertEqual(json.loads(initial_subscription), {
                'option': 'subscribe',
                'category': 'initial_state',
                'csc': 'all',
                'salindex': 'all',
                'stream': 'all'})

            # wait for the client to connect to the love_csc-love-0-observingLog group
            observingLog_subscription = await websocket.recv()
            # self.client.retry = False

            self.assertEqual(json.loads(observingLog_subscription), {
                             'option': 'subscribe',
                             'category': 'love_csc',
                             'csc': 'love',
                             'salindex': '0',
                             'stream': 'observingLog'})

            # Act
            # send observing logs form the server (manager)
            self.remote.evt_observingLog.flush()
            message = utils.make_stream_message('love_csc', 'love', 0, 'observingLog', {
                'user': 'an user',
                'message': 'a message'
            })

            await websocket.send(json.dumps(message))

            # Assert the DDS received the log message
            result = await self.remote.evt_observingLog.next(flush=False, timeout=STD_TIMEOUT)
            self.assertEqual(result.user, 'an user')
            self.assertEqual(result.message, 'a message')

        await self.harness(act_assert, arrange, cleanup)
