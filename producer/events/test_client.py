import asynctest
import asyncio
import json
from lsst.ts import salobj
import test_utils
import utils

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()

class TestEventsClient(test_utils.WSClientTestCase):
    async def test_valid_remote_not_in_config(self):
        async def arrange():
            from events.client import EventsWSClient
            salobj.set_random_lsst_dds_domain()
            self.index = next(index_gen)
            self.csc = salobj.TestCsc(index=self.index, config_dir=None, initial_state=salobj.State.ENABLED)
            self.remote = salobj.Remote(domain=self.csc.domain, name="Test", index=self.index)

            self.client = EventsWSClient(csc_list=[])
            self.client_task = asyncio.create_task(self.client.start_ws_client())
        
        async def act_assert(websocket, path):
            await asyncio.sleep(5)
            pass
        async def cleanup():
            # cleanup
            self.client.retry = False
            self.client_task.cancel()
            await self.client_task

            await self.csc.close()
            await self.remote.close()

            
        await self.harness(act_assert, arrange, cleanup)