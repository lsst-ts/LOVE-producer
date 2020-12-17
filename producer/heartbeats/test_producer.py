import logging
import datetime
import asyncio
import asynctest
from asynctest.mock import patch
from lsst.ts import salobj
from heartbeats.producer import HeartbeatProducer

STD_TIMEOUT = 5  # timeout for command ack
MSG_TIMEOUT = 20  # timeout to wait for heartbeat messages
index_gen = salobj.index_generator()


class TestHeartbeatsMessages(asynctest.TestCase):

    async def setUp(self):
        # Arrange
        index = next(index_gen)
        self.csc = salobj.TestCsc(index=index, config_dir=None, initial_state=salobj.State.ENABLED)

        self.message_queue = asyncio.Queue()

        async def callback(msg):
            await asyncio.wait_for(self.message_queue.put(msg), MSG_TIMEOUT)
        self.callback = callback
        self.heartbeat_producer = None
        await self.csc.start_task

    async def tearDown(self):
        # cleanup
        if self.heartbeat_producer is not None:
            for remote in self.heartbeat_producer.remotes:
                await asyncio.wait_for(remote.close(), STD_TIMEOUT)
        await asyncio.wait_for(self.csc.close(), STD_TIMEOUT)

    @patch('heartbeats.producer.datetime')
    async def test_heartbeat_received(self, mock_datetime):
        """Test that heartbeats messages are generated correctly when received,
        and with timestamp obtained from datetime.now()"""
        self.heartbeat_producer = HeartbeatProducer(domain=self.csc.domain,
                                                    send_heartbeat=self.callback,
                                                    csc_list=[('Test', self.csc.salinfo.index)])
        mock_datetime.datetime.now.return_value = datetime.datetime(2019, 1, 1)

        # Act
        self.heartbeat_producer.start()
        message = await asyncio.wait_for(self.message_queue.get(), MSG_TIMEOUT)

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
        """Test that heartbeats messages are generated correctly when heartbeat is 
        not received"""
        # Arrange
        wrong_index = next(index_gen)
        self.heartbeat_producer = HeartbeatProducer(domain=self.csc.domain,
                                                    send_heartbeat=self.callback,
                                                    csc_list=[('Test', wrong_index)])

        # Act
        self.heartbeat_producer.start()
        message = await asyncio.wait_for(self.message_queue.get(), MSG_TIMEOUT*3)

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

    @patch('heartbeats.producer.datetime')
    async def test_heartbeat_received_with_existing_remote(self, mock_datetime):
        """Test that heartbeats messages are generated correctly when received,
        and with timestamp obtained from datetime.now()"""
        remote = salobj.Remote(domain=self.csc.domain, name="Test", index=self.csc.salinfo.index)
        self.heartbeat_producer = HeartbeatProducer(domain=self.csc.domain,
                                                    send_heartbeat=self.callback,
                                                    csc_list=[],
                                                    remote=remote)
        mock_datetime.datetime.now.return_value = datetime.datetime(2019, 1, 1)

        # Act
        self.heartbeat_producer.start()
        message = await asyncio.wait_for(self.message_queue.get(), MSG_TIMEOUT)

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
                            "last_heartbeat_timestamp": -2,
                            "max_lost_heartbeats": 5
                        }
                    }
                }
            ]
        }
        self.assertEqual(expected_message, message)
        self.heartbeat_producer.set_heartbeat("test")
        message = await asyncio.wait_for(self.message_queue.get(), MSG_TIMEOUT)
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