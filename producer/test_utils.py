import asynctest
from asynctest import mock
import asyncio
import websockets
import os

STD_TIMEOUT = 15  # timeout for command ack


class WSClientTestCase(asynctest.TestCase):
    """ Class to run tests with a mock-up ws server"""

    @mock.patch.dict(os.environ, {'WEBSOCKET_HOST': '0.0.0.0:9999', 'PROCESS_CONNECTION_PASS': ''})
    async def harness(self, act_assert=None, arrange=None, cleanup=None):
        """ Runs the `act_assert` coroutine callback after starting a websockets server.
        Asynchronously it first runs the arrange and cleanup coroutines before
        and after the act_assert finishes.

        act_assert will receive (websocket, path) from the websockets.serve function.
        """
        if act_assert is None:
            act_assert = asyncio.sleep(0)
        if arrange is None:
            arrange = asyncio.sleep(0)
        if cleanup is None:
            cleanup = asyncio.sleep(0)

        test_finished = asyncio.Future()

        async def act_assert_wrapper(*args, **kwargs):
            await act_assert(*args, **kwargs)
            test_finished.set_result(True)

        async with websockets.serve(act_assert_wrapper, '0.0.0.0', 9999):
            await arrange()
            await asyncio.wait_for(test_finished, timeout=STD_TIMEOUT*2)
            await cleanup()
