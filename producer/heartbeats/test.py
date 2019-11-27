import logging
import datetime
import asyncio
import asynctest
from asynctest.mock import patch
from lsst.ts import salobj
from heartbeats.producer import HeartbeatProducer

STD_TIMEOUT = 5  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class TestHeartbeatsMessages(asynctest.TestCase):

    async def setUp(self):
        # Arrange
        index = next(index_gen)
        self.csc = salobj.TestCsc(index=index, config_dir=None, initial_state=salobj.State.ENABLED)

        self.message_queue = asyncio.Queue()

        async def callback(msg):
            await self.message_queue.put(msg)
        self.callback = callback
        self.heartbeat_producer = None

    async def tearDown(self):
        # cleanup
        if self.heartbeat_producer is not None:
            for remote in self.heartbeat_producer.remotes:
                await remote.close()
        await self.csc.close()

    @patch('heartbeats.producer.datetime')
    async def test_heartbeat_received(self, mock_datetime):
        self.heartbeat_producer = HeartbeatProducer(domain=self.csc.domain,
                                                    send_heartbeat=self.callback,
                                                    csc_list=[('Test', self.csc.salinfo.index)])
        mock_datetime.datetime.now.return_value = datetime.datetime(2019, 1, 1)

        # Act
        self.heartbeat_producer.start()
        message = await self.message_queue.get()

        # Assert:
        expected_message = {
            "category": "event",
            "data": [
                {
                    "csc": "Heartbeat",
                    "salindex": 0,
                    "data": {
                        "stream": {
                            "csc": "Test",
                            "salindex": self.csc.salinfo.index,
                            "lost": 0,
                            "last_heartbeat_timestamp": mock_datetime.datetime.now().timestamp(),
                            "max_lost_heartbeats": 5
                        }
                    }
                }
            ]
        }
        self.assertEqual(expected_message, message)

    async def test_heartbeat_not_received(self):
        # Arrange
        wrong_index = next(index_gen)
        self.heartbeat_producer = HeartbeatProducer(domain=self.csc.domain,
                                                    send_heartbeat=self.callback,
                                                    csc_list=[('Test', wrong_index)])

        # Act
        self.heartbeat_producer.start()
        message = await self.message_queue.get()

        # Assert:
        expected_message = {
            "category": "event",
            "data": [
                {
                    "csc": "Heartbeat",
                    "salindex": 0,
                    "data": {
                        "stream": {
                            "csc": "Test",
                            "salindex": wrong_index,
                            "lost": 1,
                            "last_heartbeat_timestamp": -1,
                            "max_lost_heartbeats": 5
                        }
                    }
                }
            ]
        }
        self.assertEqual(expected_message, message)