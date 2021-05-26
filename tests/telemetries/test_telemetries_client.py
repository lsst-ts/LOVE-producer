import json
import asyncio

from lsst.ts import salobj

from love.producer import test_utils
from love.producer import producer_utils

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestTelemetriesClient(test_utils.WSClientTestCase):
    maxDiff = None

    async def test_produced_message_with_telemetry_scalar(self):
        async def arrange():
            from love.producer.telemetries.client import TelemetriesClient

            salobj.set_random_lsst_dds_partition_prefix()
            self.index = next(index_gen)
            self.csc = salobj.TestCsc(
                index=self.index, config_dir=None, initial_state=salobj.State.ENABLED
            )
            await self.csc.start_task
            self.remote = salobj.Remote(
                domain=self.csc.domain, name="Test", index=self.index
            )
            await self.remote.start_task

            csc_list = [("Test", self.index)]

            # with patch("builtins.open", mock_open(read_data=json.dumps(config))) :
            self.client = TelemetriesClient(csc_list=csc_list, sleep_duration=0.5)
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
            tel_scalars = await self.remote.tel_scalars.next(
                flush=False, timeout=STD_TIMEOUT
            )
            tel_parameters = tel_scalars._member_attributes
            expected_stream = {
                p: {
                    "value": getattr(tel_scalars, p),
                    "dataType": producer_utils.get_data_type(getattr(tel_scalars, p)),
                    "units": f"{self.remote.tel_scalars.metadata.field_info[p].units}",
                }
                for p in tel_parameters
                if p != "private_rcvStamp"
            }

            while True:
                response = await websocket.recv()
                message = json.loads(response)
                stream_exists = producer_utils.check_event_stream(
                    message, "telemetry", "Test", self.index, "scalars"
                )
                if stream_exists:
                    stream = producer_utils.get_event_stream(
                        message, "telemetry", "Test", self.index, "scalars"
                    )
                    break

            del stream["private_rcvStamp"]

            self.assertEqual(stream, expected_stream)

        async def cleanup():
            # cleanup
            self.client.retry = False

            await self.csc.close()
            await self.remote.close()
            for remote in self.client.producer.remote_list:
                await remote.close()

            self.client_task.cancel()
            await self.client_task

        await self.harness(act_assert, arrange, cleanup)

    async def test_produced_message_with_telemetry_scalar_with_existing_remote(self):
        async def arrange():
            from love.producer.telemetries.client import TelemetriesClient

            salobj.set_random_lsst_dds_partition_prefix()
            self.index = next(index_gen)
            self.csc = salobj.TestCsc(
                index=self.index, config_dir=None, initial_state=salobj.State.ENABLED
            )
            await self.csc.start_task
            self.remote = salobj.Remote(
                domain=self.csc.domain, name="Test", index=self.index
            )
            await self.remote.start_task

            # csc_list = [("Test", self.index)]

            # with patch("builtins.open", mock_open(read_data=json.dumps(config))) :
            remote = salobj.Remote(
                domain=salobj.Domain(), name="Test", index=self.index
            )
            self.client = TelemetriesClient(
                csc_list=[], sleep_duration=0.5, remote=remote
            )
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
                    "csc": "Test",
                    "salindex": "all",
                    "stream": "all",
                },
            )

            # ARRANGE: fill in some data
            cmd_data_sent = self.csc.make_random_cmd_scalars()
            await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)
            tel_scalars = await self.remote.tel_scalars.next(
                flush=False, timeout=STD_TIMEOUT
            )
            tel_parameters = tel_scalars._member_attributes
            expected_stream = {
                p: {
                    "value": getattr(tel_scalars, p),
                    "dataType": producer_utils.get_data_type(getattr(tel_scalars, p)),
                    "units": f"{self.remote.tel_scalars.metadata.field_info[p].units}",
                }
                for p in tel_parameters
                if p != "private_rcvStamp"
            }

            while True:
                response = await websocket.recv()
                message = json.loads(response)
                stream_exists = producer_utils.check_event_stream(
                    message, "telemetry", "Test", self.index, "scalars"
                )
                if stream_exists:
                    stream = producer_utils.get_event_stream(
                        message, "telemetry", "Test", self.index, "scalars"
                    )
                    break

            del stream["private_rcvStamp"]

            self.assertEqual(stream, expected_stream)

        async def cleanup():
            # cleanup
            self.client.retry = False

            await self.csc.close()
            await self.remote.close()
            for remote in self.client.producer.remote_list:
                await remote.close()

            self.client_task.cancel()
            await self.client_task

        await self.harness(act_assert, arrange, cleanup)
