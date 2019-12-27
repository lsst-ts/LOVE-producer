import asyncio
import os
import websockets
import asynctest
from asynctest.mock import patch

from base_ws_client import BaseWSClient

WS_HOST = "ASDF"
WS_PASS = "ZXCV"

ENVIRON = {
    "WEBSOCKET_HOST": WS_HOST,
    "PROCESS_CONNECTION_PASS": WS_PASS
}

@asynctest.mock.patch.dict(os.environ, ENVIRON)
class BaseCientTestCase(asynctest.TestCase):
    async def test_constructor(self):
        client = BaseWSClient('TestClient')
        self.assertEqual(client.url, "ws://{}/?password={}".format(WS_HOST, WS_PASS))
