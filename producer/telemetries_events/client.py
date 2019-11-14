"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from .producer import Producer
import os
import utils


class TelemetryEventsWSClient():
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self, csc_list):
        self.domain = salobj.Domain()
        self.url = "ws://{}/?password={}".format(utils.WS_HOST, utils.WS_PASS)
        self.producer = Producer(self.domain, csc_list)
        self.message_getters = [
            self.producer.get_telemetry_message,
            self.producer.get_events_message
        ]

    async def start_ws_client(self):
        """ Initializes the websocket client and producer callbacks """

        self.websocket = await websockets.client.connect(self.url)
        print(f'### Telemetry&Events | loaded ws')
        initial_state_subscribe_msg = {
            'option': 'subscribe',
            'category': 'initial_state',
            'csc': 'all',
            'salindex': 'all',
            'stream': 'all'
        }
        await self.websocket.send(json.dumps(initial_state_subscribe_msg))
        print(f'### Telemetry&Events | subscribed initial state')
        asyncio.create_task(self.send_messages_after_timeout())
        asyncio.create_task(self.handle_message_reception())

    async def send_messages_after_timeout(self):
        while True:
            for get_message in self.message_getters:
                message = get_message()
                print('send before 2', message, 'asdf')
                await self.websocket.send(json.dumps(message))
                print('wait 2')
            await asyncio.sleep(2)

    async def handle_message_reception(self):
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it sends the latest seen value in SAL"""
        while True:
            message = await self.websocket.recv()
            message = json.loads(message)
            try:
                if message['category'] is None:
                    continue
                if 'data' not in message:
                    continue
                if len(message['data']) == 0:
                    continue

                answer = await self.producer.process_message(message)
                if answer is None:
                    continue
                dumped_answer = json.dumps(answer, cls=utils.NumpyEncoder)
                asyncio.create_task(self.websocket.send(dumped_answer))
                print(f'### Telemetry&Events | found it!!')
            except Exception as e:
                print(f'### Telemetry&Events | exception\n', e)
                print(f'### Telemetry&Events | message:', message)


async def main():
    print('***** Starting Telemetry&Event Producers *****')
    path = os.path.join(os.path.dirname(__file__), '..', utils.CONFIG_PATH)
    csc_list = utils.read_config(path)
    print('List of CSCs to listen:', csc_list)

    telev_client = TelemetryEventsWSClient(csc_list)
    await telev_client.start_ws_client()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
