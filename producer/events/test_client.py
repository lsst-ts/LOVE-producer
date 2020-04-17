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

            self.client = EventsWSClient()
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

            # ASSERT remote does not exist in current instance
            self.assertNotIn(('Test', 1), self.client.producer.initial_state_remote_dict)
            self.assertNotIn(('Test', 1), self.client.producer.remote_dict)

            # ARRANGE: fill in some data            
            cmd_data_sent = self.csc.make_random_cmd_scalars()
            await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)
            evt_scalars = await self.remote.evt_scalars.next(flush=False)
            
            # ACT: request initial data of a new csc
            message = utils.make_stream_message('initial_state', 'Test', 1, 'event_name', 'scalars')
            await websocket.send(json.dumps(message))

            # heartbeat events will come too, so just wait for this event
            while True:
                response = await websocket.recv()
                message = json.loads(response)
                stream_exists = utils.check_event_stream(message, 'event', 'Test', 1, 'scalars')
                print('stream_exists', stream_exists, flush=True)
                if stream_exists:
                    stream = utils.get_event_stream(message, 'event', 'Test', 1, 'scalars')[0]
                    break
                

            # ASSERT
            # the remote exists in both dicts
            self.assertIn(('Test', 1), self.client.producer.initial_state_remote_dict)
            self.assertIn(('Test', 1), self.client.producer.remote_dict)

            # ASSERT: message has the same data
            evt_parameters = evt_scalars._member_attributes
            expected_stream = {
                p: {
                    'value': getattr(evt_scalars, p),
                    'dataType': utils.getDataType(getattr(evt_scalars, p))
                }
                for p in evt_parameters if p != "private_rcvStamp"
            }
            self.maxDiff = None
            del stream['private_rcvStamp']
            self.assertEqual(stream, expected_stream)

        async def cleanup():
            # cleanup
            self.client.retry = False
            self.client_task.cancel()
            await self.client_task

            await self.csc.close()
            await self.remote.close()
            for (remote, index) in self.client.producer.initial_state_remote_dict:
                await self.client.producer.initial_state_remote_dict[(remote,index)].close()
            
            for (remote, index) in self.client.producer.initial_state_remote_dict:
                await self.client.producer.initial_state_remote_dict[(remote,index)].close()

            
        await self.harness(act_assert, arrange, cleanup)