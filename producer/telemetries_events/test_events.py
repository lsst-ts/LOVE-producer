import asynctest
import logging
from .producer import Producer
import asyncio
from lsst.ts import salobj
import utils

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()



class TestEventsMessages(asynctest.TestCase):
    async def setUp(self):
        salobj.set_random_lsst_dds_domain()
        index = next(index_gen)
        self.csc = salobj.TestCsc(index=index, config_dir=None, initial_state=salobj.State.ENABLED)
        self.remote = salobj.Remote(domain=self.csc.domain, name="Test", index=index)

    async def tearDown(self):
        for self.remote in self.telemetry_events_producer.remote_list:
            await asyncio.wait_for(self.remote.close(), STD_TIMEOUT)
        await asyncio.wait_for(self.csc.close(), STD_TIMEOUT)

    async def test_produced_message_with_event_scalar(self):
        # Arrange
        # Setup the producer and the data
        self.telemetry_events_producer = Producer(domain=self.csc.domain,
                                                  csc_list=[('Test', self.csc.salinfo.index)])
        cmd_data_sent = self.csc.make_random_cmd_scalars()

        # Act
        # Fill the evt with data and read it with the producer
        await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)
        evt_scalars = await self.remote.evt_scalars.next(flush=False, timeout=STD_TIMEOUT)
        evt_parameters = evt_scalars._member_attributes
        expected_stream = {
            p: {
                'value': getattr(evt_scalars, p),
                'dataType': utils.getDataType(getattr(evt_scalars, p))
            }
            for p in evt_parameters if p != "private_rcvStamp"
        }

        # extracting the message should be made synchronously
        message = self.telemetry_events_producer.get_events_message()
        stream = utils.get_event_stream(message, 'event', 'Test', self.csc.salinfo.index, 'scalars')[0]

        # private_rcvStamp apparently is different from one remote to another
        del stream['private_rcvStamp']


        # Assert
        self.assertEqual(stream, expected_stream)

    async def test_produced_message_with_event_arrays(self):
        # Arrange
        # Setup the producer and the data
        self.telemetry_events_producer = Producer(domain=self.csc.domain,
                                                  csc_list=[('Test', self.csc.salinfo.index)])
        cmd_data_sent = self.csc.make_random_cmd_arrays()

        # Act
        # Fill the evt with data and read it with the producer
        await self.remote.cmd_setArrays.start(cmd_data_sent, timeout=STD_TIMEOUT)
        evt_arrays = await self.remote.evt_arrays.next(flush=False, timeout=STD_TIMEOUT)
        evt_parameters = evt_arrays._member_attributes
        expected_stream = {
            p: {
                'value': getattr(evt_arrays, p),
                'dataType': utils.getDataType(getattr(evt_arrays, p))
            } for p in evt_parameters if p != "private_rcvStamp"
        }

        # extracting the message should be made synchronously
        message = self.telemetry_events_producer.get_events_message()
        stream = utils.get_event_stream(message, 'event', 'Test', self.csc.salinfo.index, 'arrays')[0]

        # private_rcvStamp apparently is different from one remote to another
        del stream["private_rcvStamp"]

        # Assert
        self.assertEqual(stream, expected_stream)
