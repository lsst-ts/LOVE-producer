import asyncio
import os
import websockets
import asynctest
from asynctest import mock as am
import json
from base_ws_client import BaseWSClient

WS_HOST = "ASDF"
WS_PASS = "ZXCV"

ENVIRON = {
    "WEBSOCKET_HOST": WS_HOST,
    "PROCESS_CONNECTION_PASS": WS_PASS
}

CONFIG = json.dumps({
    "ATMCS": [
        {"source": "command_sim"}
    ],
    "ATDome": [
        {"source": "command_sim"}
    ],
    "Test": [
        {"index": 1, "source": "command_sim"},
        {"index": 2, "source": "command_sim"},
        {"index": 3, "source": "command_sim"}
    ],
    "ScriptQueue": [
        {"index": 1, "source": "command_sim"}
    ],
    "Watcher": [
        {"index": 0, "source": "command_sim"}
    ]
})


@am.patch.dict(os.environ, ENVIRON)
@am.patch('builtins.open', am.mock_open(read_data=CONFIG))
class BaseCientTestCase(asynctest.TestCase):
    async def test_constructor(self):
        client = BaseWSClient('TestClient')
        self.assertEqual(client.url, "ws://{}/?password={}".format(WS_HOST, WS_PASS))
