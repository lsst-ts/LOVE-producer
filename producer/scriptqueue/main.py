"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from producer import ScriptQueueProducer
import os
import utils
CONFIG_PATH = 'config/config.json'
WS_HOST = os.environ["WEBSOCKET_HOST"]
WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]


class WebsocketProducer():
    def __init__(self):
        """ Sends ScriptQueueState produced messages through websockets to the LOVE-manager."""
        self.domain = salobj.Domain()
        self.url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
        self.salindex = 1
        self.producer = ScriptQueueProducer(self.domain, self.send_message_callback, self.salindex)

    async def start_ws_client(self):
        """ Initializes the websocket client and producer callbacks """
        
        self.websocket = await websockets.client.connect(self.url)
        print('### loaded ws')
        await self.producer.setup()
        print('### loaded producer')

    def send_message_callback(self, message):
        """Sends messages through websockets. Called after each scriptqueue event """
        print('### sending message')
        print('\n\n message', message)
        asyncio.create_task(self.websocket.send(json.dumps(message)))

    # async def handle_message_reception(self):
    #     while True:
    #         message = await self.websocket.recv()
    #         jsonmessage = json.loads(message)
    #         stream = get_stream_from_last_message(jsonmessage, 'initial_state', 'ScriptQueueState', self.salindex, 'stream')


async def main():
    wsp = WebsocketProducer()
    await wsp.start_ws_client()
    await wsp.producer.update()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
