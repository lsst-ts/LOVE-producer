"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from .producer import HeartbeatProducer
import os
import utils


class CSCHeartbeatsWSClient():
    """Handles the websocket client connection between the Heartbeatss Producer and the LOVE-manager."""

    def __init__(self, csc_list):
        self.domain = salobj.Domain()
        self.url = "ws://{}/?password={}".format(utils.WS_HOST, utils.WS_PASS)
        self.producer = HeartbeatProducer(self.domain, self.send_heartbeat, csc_list)

    async def start_ws_client(self):
        """ Initializes the websocket client and producer callbacks """

        self.websocket = await websockets.client.connect(self.url)
        self.producer.start()
        print(f'### Telemetry&Events | subscribed initial state')

    async def send_heartbeat(self, message):
        await self.websocket.send(json.dumps(message))

async def main():
    print('***** Starting Telemetry&Event Producers *****')
    path = os.path.join(os.path.dirname(__file__), '..', utils.CONFIG_PATH)
    csc_list = utils.read_config(path)
    print('List of CSCs to listen:', csc_list)

    telev_client = CSCHeartbeatsWSClient(csc_list)
    await telev_client.start_ws_client()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
