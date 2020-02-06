import asyncio
import json
import websockets
import traceback
import os
from lsst.ts import salobj

WS_HOST = os.environ["WEBSOCKET_HOST"]
WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]
CONFIG_PATH = 'config/config.json'


class BaseWSClient():
    path = os.path.join(os.path.dirname(__file__), CONFIG_PATH)

    def __init__(self, name):
        self.url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
        self.domain = salobj.Domain()
        self.name = name
        print(f'***** Starting {self.name} Producers *****')
        self.csc_list = self.read_config(self.path)
        print('List of CSCs to listen:', self.csc_list)

    async def handle_message_reception(self, websocket):
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it sends the latest seen value in SAL"""
        async for message in websocket:
            message = json.loads(message)
            if 'category' not in message:
                continue
            await self.on_websocket_receive(websocket, message)

    async def start_ws_client(self):
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    print(f'### {self.name} | loaded ws')

                    initial_state_subscribe_msg = {
                        'option': 'subscribe',
                        'category': 'initial_state',
                        'csc': 'all',
                        'salindex': 'all',
                        'stream': 'all'
                    }
                    await websocket.send(json.dumps(initial_state_subscribe_msg))
                    print(f'### {self.name} | subscribed to initial state')

                    await asyncio.gather(self.handle_message_reception(websocket), self.on_start_client(websocket))
            except Exception as e:
                print(f'### {self.name} | Exception {e} \n Attempting to reconnect from start_ws_client')
                print(f'### {self.name} | traceback:', traceback.print_tb(e.__traceback__))
                await self.on_websocket_error(e)
                await asyncio.sleep(3)


    async def on_websocket_receive(self, websocket, message):
        pass

    async def on_start_client(self):
        pass

    async def on_websocket_error(self):
        pass

    @staticmethod
    def read_config(path, key=None):
        """ Reads a given config file and returns the lists of CSCs to listen to.
        It can read the full file (by default), or read only a specific key

        Parameters
        ----------
        path: `string`
            The full path of the config file
        key: `string`
            optional key to read

        Returns
        -------
        csc_list: `[()]`
            The list of CSCs to run as a tuple with the CSC name and index
        """
        print('Reading config file: ', path)
        with open(path) as config_file:
            data = json.loads(config_file.read())

        # data = json.load(open(path, 'r'))
        csc_list = []
        if key:
            for csc_instance in data[key]:
                index = 0
                if 'index' in csc_instance:
                    index = csc_instance['index']
                csc_list.append((key, index))
        else:
            for csc_key, csc_value in data.items():
                for csc_instance in csc_value:
                    index = 0
                    if 'index' in csc_instance:
                        index = csc_instance['index']
                    csc_list.append((csc_key, index))
        return csc_list
