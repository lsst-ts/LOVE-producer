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


@mock.patch.dict(os.environ, {'WEBSOCKET_HOST': '0.0.0.0:9999', 'PROCESS_CONNECTION_PASS': ''})
class TestWebsocketsClient(asynctest.TestCase):
    async def test_csc_client(self):
        from love_csc.client import LOVEWSClient

        salobj.set_random_lsst_dds_domain()
        # Arrange
        test_finished = asyncio.Future()
        self.remote = salobj.Remote(domain=salobj.Domain(), name="LOVE")

        async def server_callback(websocket, path):
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
            test_finished.set_result(True)

        # Create server (LOVE-manager mock) and handle it with `server_callback`
        async with websockets.serve(server_callback, '0.0.0.0', 9999):
            # connect client (producer)
            client = LOVEWSClient()
            self.client = client
            client_task = asyncio.create_task(client.start_ws_client())

            # Finished resolves after asserts are ok
            await asyncio.wait_for(test_finished, timeout=STD_TIMEOUT*2)

            # cleanup
            client.retry = False
            client_task.cancel()
            await client_task

            await client.csc.close()
            await self.remote.close()
