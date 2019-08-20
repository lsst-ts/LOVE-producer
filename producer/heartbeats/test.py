import unittest
import logging
from .producer import HeartbeatProducer
import asyncio
from lsst.ts import salobj

STD_TIMEOUT = 5  # timeout for command ack
SHOW_LOG_MESSAGES = False

index_gen = salobj.index_generator()


class Harness:
    def __init__(self, initial_state, config_dir=None, CscClass=salobj.TestCsc):
        index = next(index_gen)
        self.csc = CscClass(index=index, config_dir=config_dir, initial_state=initial_state)
        if SHOW_LOG_MESSAGES:
            handler = logging.StreamHandler()
            self.csc.log.addHandler(handler)
        self.remote = salobj.Remote(domain=self.csc.domain, name="Test", index=index)

    async def __aenter__(self):
        await self.csc.start_task
        await self.remote.start_task
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.remote.close()
        await self.csc.close()


class TestTelemetryMessages(unittest.TestCase):
    def setUp(self):
        salobj.set_random_lsst_dds_domain()

    def test_heartbeat_received(self):
        """When monitoring the right (csc,salindex) it should report 0 lost heartbeat"""

        callback_future = asyncio.Future()

        def heartbeat_callback(message):
            callback_future.set_result(message)

        async def doit():
            async with Harness(initial_state=salobj.State.ENABLED) as harness:
                # Arrange
                heartbeat_producer = HeartbeatProducer(domain=harness.csc.domain, send_heartbeat=heartbeat_callback, csc_list=[
                                                       ('Test', harness.csc.salinfo.index)])

                # Act
                heartbeat_producer.start()
                message = await callback_future

                # Assert:
                #
                # Timestamp seems unpredictable so just copy it for now
                timestamp = message["data"][0]["data"]["stream"]["last_heartbeat_timestamp"]
                expected_message = {
                    "category": "event",
                    "data": [
                        {
                            "csc": "Heartbeat",
                            "salindex": 0,
                            "data": {
                                "stream": {
                                    "csc": "Test",
                                    "salindex": harness.csc.salinfo.index,
                                    "lost": 0,
                                    "last_heartbeat_timestamp": timestamp,
                                    "max_lost_heartbeats": 5
                                }
                            }
                        }
                    ]
                }
                self.assertEqual(expected_message, message)

                # cleanup
                for remote in heartbeat_producer.remotes:
                    await remote.close()

    def test_heartbeat_not_received(self):
        """When monitoring the wrong (csc,salindex) it should report 1 lost heartbeat"""

        callback_future = asyncio.Future()

        def heartbeat_callback(message):
            callback_future.set_result(message)

        async def doit():
            async with Harness(initial_state=salobj.State.ENABLED) as harness:
                # Arrange
                wrong_index = next(index_gen)
                heartbeat_producer = HeartbeatProducer(domain=harness.csc.domain, send_heartbeat=heartbeat_callback, csc_list=[
                                                       ('Test', wrong_index)])

                # Act
                heartbeat_producer.start()
                message = await callback_future

                # Assert:
                #
                # Timestamp seems unpredictable so just copy it for now
                timestamp = message["data"][0]["data"]["stream"]["last_heartbeat_timestamp"]
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
                                    "last_heartbeat_timestamp": timestamp,
                                    "max_lost_heartbeats": 5
                                }
                            }
                        }
                    ]
                }
                self.assertEqual(expected_message, message)

                # cleanup
                for remote in heartbeat_producer.remotes:
                    await remote.close()
        asyncio.get_event_loop().run_until_complete(doit())


if __name__ == '__main__':
    unittest.main()
