"""Test the Producer"""
import asyncio

import asynctest
from lsst.ts import salobj

from events.producer import EventsProducer
from .. import utils

STD_TIMEOUT = 15  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestEventsMessages(asynctest.TestCase):
    """Test suite for the Producer."""

    async def setUp(self):
        salobj.set_random_lsst_dds_partition_prefix()
        index = next(index_gen)
        self.csc = salobj.TestCsc(
            index=index, config_dir=None, initial_state=salobj.State.ENABLED
        )
        self.remote = salobj.Remote(domain=self.csc.domain, name="Test", index=index)

        self.message_queue = asyncio.Queue()
        self.callback = lambda message: asyncio.create_task(
            self.message_queue.put(message)
        )
        self.events_producer = None
        await self.csc.start_task

    async def tearDown(self):
        for remote in self.events_producer.remote_dict.values():
            await asyncio.wait_for(remote.close(), STD_TIMEOUT)
        await asyncio.wait_for(self.csc.close(), STD_TIMEOUT)
        await asyncio.wait_for(self.remote.close(), STD_TIMEOUT)

    async def wait_for_stream(self, stream):
        while True:
            message = await self.message_queue.get()
            if not utils.check_event_stream(
                message, "event", "Test", self.csc.salinfo.index, stream
            ):
                continue
            stream = utils.get_event_stream(
                message, "event", "Test", self.csc.salinfo.index, stream
            )[0]
            return stream

    async def test_produced_message_with_event_scalar(self):
        # Arrange
        self.events_producer = EventsProducer(
            domain=self.csc.domain,
            csc_list=[("Test", self.csc.salinfo.index)],
            events_callback=self.callback,
        )
        for r in self.events_producer.remote_dict.values():
            await r.start_task
        self.events_producer.setup_callbacks()
        cmd_data_sent = self.csc.make_random_cmd_scalars()
        await self.remote.start_task
        await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)

        # Act
        stream = await asyncio.wait_for(self.wait_for_stream("scalars"), STD_TIMEOUT)
        del stream["private_rcvStamp"]

        # Assert
        evt_scalars = await self.remote.evt_scalars.next(
            flush=False, timeout=STD_TIMEOUT
        )
        evt_parameters = evt_scalars._member_attributes
        expected_stream = {
            p: {
                "value": getattr(evt_scalars, p),
                "dataType": utils.get_data_type(getattr(evt_scalars, p)),
                "units": f"{self.remote.evt_scalars.metadata.field_info[p].units}",
            }
            for p in evt_parameters
            if p != "private_rcvStamp"
        }
        self.assertEqual(stream, expected_stream)

    async def test_produced_message_with_event_arrays(self):
        # Arrange
        self.events_producer = EventsProducer(
            domain=self.csc.domain,
            csc_list=[("Test", self.csc.salinfo.index)],
            events_callback=self.callback,
        )
        for r in self.events_producer.remote_dict.values():
            await r.start_task
        self.events_producer.setup_callbacks()
        # Setup the producer and the data
        cmd_data_sent = self.csc.make_random_cmd_arrays()
        await self.remote.start_task
        await self.remote.cmd_setArrays.start(cmd_data_sent, timeout=STD_TIMEOUT)

        # Act
        stream = await asyncio.wait_for(self.wait_for_stream("arrays"), STD_TIMEOUT)
        del stream["private_rcvStamp"]

        # Assert
        evt_arrays = await self.remote.evt_arrays.next(flush=False, timeout=STD_TIMEOUT)
        evt_parameters = evt_arrays._member_attributes
        expected_stream = {
            p: {
                "value": getattr(evt_arrays, p),
                "dataType": utils.get_data_type(getattr(evt_arrays, p)),
                "units": f"{self.remote.evt_scalars.metadata.field_info[p].units}",
            }
            for p in evt_parameters
            if p != "private_rcvStamp"
        }
        self.assertEqual(stream, expected_stream)

    async def test_produced_message_with_event_scalar_with_existing_remote(self):
        # Arrange
        remote = salobj.Remote(
            domain=self.csc.domain, name="Test", index=self.csc.salinfo.index
        )
        self.events_producer = EventsProducer(
            domain=self.csc.domain,
            csc_list=[],
            events_callback=self.callback,
            remote=remote,
        )
        for r in self.events_producer.remote_dict.values():
            await r.start_task
        self.events_producer.setup_callbacks()
        cmd_data_sent = self.csc.make_random_cmd_scalars()
        await self.remote.start_task
        await self.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)

        # Act
        stream = await asyncio.wait_for(self.wait_for_stream("scalars"), STD_TIMEOUT)
        del stream["private_rcvStamp"]

        # Assert
        evt_scalars = await self.remote.evt_scalars.next(
            flush=False, timeout=STD_TIMEOUT
        )
        evt_parameters = evt_scalars._member_attributes
        expected_stream = {
            p: {
                "value": getattr(evt_scalars, p),
                "dataType": utils.get_data_type(getattr(evt_scalars, p)),
                "units": f"{self.remote.evt_scalars.metadata.field_info[p].units}",
            }
            for p in evt_parameters
            if p != "private_rcvStamp"
        }
        self.assertEqual(stream, expected_stream)
