"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from producer import ScriptQueueProducer
import os
import utils

class ScriptQueueWSClient():
    """Handles the websocket client connection between the ScriptQueue Producer and the LOVE-manager."""

    def __init__(self, salindex):
        self.domain = salobj.Domain()
        self.url = "ws://{}/?password={}".format(utils.WS_HOST, utils.WS_PASS)
        self.salindex = salindex
        self.producer = ScriptQueueProducer(self.domain, self.send_message_callback, self.salindex)

    async def start_ws_client(self):
        """ Initializes the websocket client and producer callbacks """

        self.websocket = await websockets.client.connect(self.url)
        print(f'### ScriptQueue-{self.salindex} | loaded ws')
        initial_state_subscribe_msg = {
            'option': 'subscribe',
            'category': 'initial_state',
            'csc': 'all',
            'salindex': 'all',
            'stream': 'all'
        }
        await self.websocket.send(json.dumps(initial_state_subscribe_msg))
        print(f'### ScriptQueue-{self.salindex} | subscribed initial state')
        await self.producer.setup()
        print(f'### ScriptQueue-{self.salindex} | loaded producer')

        asyncio.create_task(self.handle_message_reception())

    def send_message_callback(self, message):
        """Sends messages through websockets. Called after each scriptqueue event """
        print(f'### ScriptQueue-{self.salindex} | ### sending message')
        asyncio.create_task(self.websocket.send(json.dumps(message)))

    async def handle_message_reception(self):
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it triggers the producer.update() coro"""
        while True:
            message = await self.websocket.recv()
            message = json.loads(message)
            print(message)
            try:
                if message['category'] is not None:
                    stream = utils.get_stream_from_last_message(
                        message, 'initial_state', 'ScriptQueueState', f"{self.salindex}", 'event_name')
                print(f'### ScriptQueue-{self.salindex} | found it!!')
                print(stream)
                await self.producer.update()
            except Exception as e:
                print(f'### ScriptQueue-{self.salindex} | exception\n', e)
                print(f'### ScriptQueue-{self.salindex} | message:', message)


async def init_client(salindex):
    sqclient = ScriptQueueWSClient(salindex)
    await sqclient.start_ws_client()
    await sqclient.producer.update()


async def main():
    print('***** Starting Scriptqueue Producers *****')
    path = os.path.join(os.path.dirname(__file__), '..', utils.CONFIG_PATH)
    sq_list = utils.read_config(path, 'ScriptQueue')

    print('List of Script Queues to listen:', sq_list)
    for name, salindex in sq_list:
        asyncio.create_task(init_client(salindex))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
