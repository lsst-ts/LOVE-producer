"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from .receiver import Receiver
import os
import utils

class CommandWSClient():
    """Handles the websocket client connection between the Commands Receiver and the LOVE-manager."""

    def __init__(self, csc_list):
        self.domain = salobj.Domain()
        self.url = "ws://{}/?password={}".format(utils.WS_HOST, utils.WS_PASS)
        self.csc_list = csc_list
        self.receiver = Receiver(self.domain, self.csc_list)

    async def start_ws_client(self):
        """ Initializes the websocket client and producer callbacks """

        self.websocket = await websockets.client.connect(self.url)
        print(f'### Receiver | loaded ws')

        cmd_subscribe_msg = {
            'option': 'subscribe',
            'category': 'cmd',
            'csc': 'all',
            'salindex': 'all',
            'stream': 'all'
        }
        await self.websocket.send(json.dumps(cmd_subscribe_msg))
        print(f'### Receiver | subscribed commands')
        asyncio.create_task(self.handle_message_reception())

    async def handle_message_reception(self):
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it triggers the producer.update() coro"""
        while True:
            message = await self.websocket.recv()
            message = json.loads(message)
            print(message)
            try:
                if message['category'] is not None:
                    answer = await self.receiver.process_message(message)
                    if answer is None:
                        continue
                    dumped_answer = json.dumps(answer, cls=utils.NumpyEncoder)
                    asyncio.create_task(self.websocket.send(dumped_answer))
                print(f'### Receiver | found it!!')
            except Exception as e:
                print(f'### Receiver | exception\n', e)
                print(f'### Receiver | message:', message)


async def main():
    print('***** Starting Command Receivers *****')
    path = os.path.join(os.path.dirname(__file__), '..', utils.CONFIG_PATH)
    csc_list = utils.read_config(path)
    print('List of CSCs to listen:', csc_list)

    commands_client = CommandWSClient(csc_list)
    await commands_client.start_ws_client()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
