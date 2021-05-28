"""Test the Client"""
import json

import asyncio
from lsst.ts import salobj

from love.producer import test_utils
from love.producer import producer_utils
from love.producer.csc.client import CSCWSClient

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestCSCClient(test_utils.WSClientTestCase):
    """Test suite for the Client."""

    async def test_valid_remote_not_in_config(self):
        async def arrange():

            salobj.set_random_lsst_dds_partition_prefix()
            self.index = next(index_gen)
            self.csc = salobj.TestCsc(
                index=self.index, config_dir=None, initial_state=salobj.State.ENABLED
            )
            self.remote = salobj.Remote(
                domain=self.csc.domain, name="Test", index=self.index
            )
            await self.remote.start_task
            await self.csc.start_task

            self.client = CSCWSClient(csc_list=[("Test", self.index)])
            self.client_task = asyncio.create_task(self.client.start_ws_client())

        async def act_assert(websocket, path):
            # ARRANGE wait for the client to connect to initial_state group
            # this ensures the harness will run the arrange() first
            initial_subscription = await websocket.recv()
            self.assertEqual(
                json.loads(initial_subscription),
                {
                    "option": "subscribe",
                    "category": "initial_state",
                    "csc": "all",
                    "salindex": "all",
                    "stream": "all",
                },
            )

            # ARRANGE: fill in some data
            cmd_data_sent = self.csc.make_random_cmd_scalars()
            await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)

            # wait for the scalars event to be sent
            while True:
                response = await websocket.recv()
                message = json.loads(response)
                if "heartbeat" in message:
                    continue
                stream_exists = producer_utils.check_event_stream(
                    message, "event", "Test", self.index, "scalars"
                )
                print("stream_exists", stream_exists, flush=True)
                if stream_exists:
                    stream = producer_utils.get_event_stream(
                        message, "event", "Test", self.index, "scalars"
                    )[0]
                    break

            del stream["private_rcvStamp"]

            # build expected data
            evt_scalars = await self.remote.evt_scalars.next(
                flush=False, timeout=STD_TIMEOUT
            )
            evt_parameters = evt_scalars._member_attributes

            expected_stream = {
                p: {
                    "value": getattr(evt_scalars, p),
                    "dataType": producer_utils.get_data_type(getattr(evt_scalars, p)),
                    "units": f"{self.remote.evt_scalars.metadata.field_info[p].units}",
                }
                for p in evt_parameters
                if p != "private_rcvStamp"
            }

            self.assertEqual(stream, expected_stream)

        async def cleanup():
            # cleanup
            self.client.retry = False
            await self.csc.close()
            await self.remote.close()
            if not self.client_task.done():
                self.client_task.cancel()
            await self.client.close()

        await asyncio.wait_for(
            self.harness(act_assert, arrange, cleanup), timeout=STD_TIMEOUT*3
        )
