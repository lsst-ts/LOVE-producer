import asynctest
from lsst.ts import salobj

import producer_utils
from telemetries.producer import TelemetriesProducer

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestTelemetryMessages(asynctest.TestCase):
    async def setUp(self):
        salobj.set_random_lsst_dds_partition_prefix()
        index = next(index_gen)
        self.csc = salobj.TestCsc(
            index=index, config_dir=None, initial_state=salobj.State.ENABLED
        )
        self.remote = salobj.Remote(domain=self.csc.domain, name="Test", index=index)
        await self.remote.start_task
        await self.remote.salinfo.start_task
        await self.csc.start_task

    async def tearDown(self):
        for remote in self.telemetry_producer.remote_list:
            await remote.close()
        await self.csc.close()

    async def test_produced_message_with_telemetry_scalar(self):
        # Arrange
        self.telemetry_producer = TelemetriesProducer(
            domain=self.csc.domain, csc_list=[("Test", self.csc.salinfo.index)]
        )
        for r in self.telemetry_producer.remote_list:
            await r.start_task

        cmd_data_sent = self.csc.make_random_cmd_scalars()

        # Act
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

        # extracting the message should be made synchronously
        message = self.telemetry_producer.get_telemetry_message()
        stream = producer_utils.get_event_stream(
            message, "telemetry", "Test", self.csc.salinfo.index, "scalars"
        )

        # Assert

        # private_rcvStamp is generated on read and seems unpredictable now
        del stream["private_rcvStamp"]

        self.assertEqual(stream, expected_stream)

    async def test_produced_message_with_telemetry_scalar_with_existing_remote(self):
        # Arrange
        remote = salobj.Remote(
            domain=self.csc.domain, name="Test", index=self.csc.salinfo.index
        )
        await remote.start_task
        self.telemetry_producer = TelemetriesProducer(
            domain=None, csc_list=[], remote=remote
        )

        cmd_data_sent = self.csc.make_random_cmd_scalars()

        # Act
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

        # extracting the message should be made synchronously
        message = self.telemetry_producer.get_telemetry_message()
        stream = producer_utils.get_event_stream(
            message, "telemetry", "Test", self.csc.salinfo.index, "scalars"
        )

        # Assert

        # private_rcvStamp is generated on read and seems unpredictable now
        del stream["private_rcvStamp"]

        self.assertEqual(stream, expected_stream)
