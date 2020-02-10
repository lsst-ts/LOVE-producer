import asynctest
import asyncio
from lsst.ts import salobj
import websockets
from .csc import LOVECsc

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
        self.csc.add_observing_log('an user','a message')
        print(result)
        import pdb; pdb.set_trace()
        
        # Assert
        result = await self.remote.evt_observingLog.next(flush=False)
        self.assertEqual(result.user, 'an user')
        self.assertEqual(result.message, 'a message')

        # clean up
        await self.csc.close()
        await self.remote.close()

class TestWebsocketsClient(asynctest.TestCase):

    async def test_response(self):
        async def hello_server(websocket, path):
            name = await websocket.recv()
            print(f"< {name}")

            greeting = f"Hello {name}!"

            await websocket.send(greeting)
            print(f"> {greeting}")    
            
        async def hello():
            uri = "ws://0.0.0.0:9999"
            async with websockets.connect(uri) as websocket:
                name = 'name'

                await websocket.send(name)
                print(f"> {name}")

                greeting = await websocket.recv()
                print(f"< {greeting}")
        
        
        async with websockets.serve(hello_server, '0.0.0.0', 9999) as server:
            await hello()
        
        # async wi
