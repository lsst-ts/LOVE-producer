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

            self.client = EventsWSClient(csc_list=[("Test", self.index)])
            self.client_task = asyncio.create_task(self.client.start_ws_client())
        
        async def act_assert(websocket, path):
            # ARRANGE wait for the client to connect to initial_state group
            # this ensures the harness will run the arrange() first
            initial_subscription = await websocket.recv()
            self.assertEqual(json.loads(initial_subscription), {
                'option': 'subscribe',
                'category': 'initial_state',
                'csc': 'all',
                'salindex': 'all',
                'stream': 'all'})

            # ARRANGE: fill in some data            
            cmd_data_sent = self.csc.make_random_cmd_scalars()
            await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)

            # wait for the scalars event to be sent
            while True:
                response = await websocket.recv()
                message = json.loads(response)
                if "heartbeat" in message:
                    continue
                stream_exists = utils.check_event_stream(message, 'event', 'Test', 1, 'scalars')
                print('stream_exists', stream_exists, flush=True)
                if stream_exists:
                    stream = utils.get_event_stream(message, 'event', 'Test', self.index, 'scalars')[0]
                    break

            del stream['private_rcvStamp']

            # build expected data
            evt_scalars = await self.remote.evt_scalars.next(flush=False, timeout=STD_TIMEOUT)
            evt_parameters = evt_scalars._member_attributes

            expected_stream = {
                p: {
                    'value': getattr(evt_scalars, p),
                    'dataType': utils.getDataType(getattr(evt_scalars, p)),
                    'units': f"{self.remote.evt_scalars.metadata.field_info[p].units}"
                } for p in evt_parameters if p != "private_rcvStamp"
            }

            self.assertEqual(stream, expected_stream)

        async def cleanup():
            # cleanup
            self.client.retry = False
            self.client_task.cancel()
            await self.client_task

            await self.csc.close()
            await self.remote.close()

            for (csc, salindex) in self.client.producer.remote_dict:
                await self.client.producer.remote_dict[(csc, salindex)].close()
                await self.client.producer.initial_state_remote_dict[(csc, salindex)].close()

            
        await self.harness(act_assert, arrange, cleanup)