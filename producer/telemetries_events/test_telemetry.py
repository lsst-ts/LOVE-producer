import asynctest
import logging
from .producer import Producer
import asyncio
from lsst.ts import salobj
import utils

STD_TIMEOUT = 5  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestTelemetryMessages(asynctest.TestCase):
    async def setUp(self):
        salobj.set_random_lsst_dds_domain()
        index = next(index_gen)
        self.csc = salobj.TestCsc(index=index, config_dir=None, initial_state=salobj.State.ENABLED)
        self.remote = salobj.Remote(domain=self.csc.domain, name="Test", index=index)

    async def tearDown(self):
        for self.remote in self.telemetry_events_producer.remote_list:
            await self.remote.close()
        await self.csc.close()

    async def test_produced_message_with_telemetry_scalar(self):
        # Arrange
        self.telemetry_events_producer = Producer(domain=self.csc.domain,
                                                  csc_list=[('Test', self.csc.salinfo.index)])
        cmd_data_sent = self.csc.make_random_cmd_scalars()

        # Act
        await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)

        tel_scalars = await self.remote.tel_scalars.next(flush=False, timeout=STD_TIMEOUT)
        tel_parameters = tel_scalars._member_attributes
        expected_stream = {
            p: {
                'value': getattr(tel_scalars, p),
                'dataType': utils.getDataType(getattr(tel_scalars, p))
            } for p in tel_parameters if p != "private_rcvStamp"
        }

        # extracting the message should be made synchronously
        message = self.telemetry_events_producer.get_telemetry_message()
        stream = utils.get_event_stream(message, 'telemetry', 'Test', self.csc.salinfo.index, 'scalars')

        # Assert

        # private_rcvStamp is generated on read and seems unpredictable now
        del stream['private_rcvStamp']

        self.assertEqual(stream, expected_stream)

    async def test_produced_message_with_telemetry_array(self):
        # Arrange
        self.telemetry_events_producer = Producer(domain=self.csc.domain,
                                                  csc_list=[('Test', self.csc.salinfo.index)])
        cmd_data_sent = self.csc.make_random_cmd_arrays()

        # Act
        await self.remote.cmd_setArrays.start(cmd_data_sent, timeout=STD_TIMEOUT)

        tel_arrays = await self.remote.tel_arrays.next(flush=False, timeout=STD_TIMEOUT)
        tel_parameters = tel_arrays._member_attributes
        expected_stream = {
            p: {
                'value': getattr(tel_arrays, p),
                'dataType': utils.getDataType(getattr(tel_arrays, p))
            } for p in tel_parameters if p != "private_rcvStamp"
        }

        # extracting the message should be made synchronously
        message = self.telemetry_events_producer.get_telemetry_message()
        stream = utils.get_event_stream(message, 'telemetry', 'Test', self.csc.salinfo.index, 'arrays')

        # Assert

        # private_rcvStamp is generated on read and seems unpredictable now
        del stream['private_rcvStamp']

        self.assertEqual(stream, expected_stream)