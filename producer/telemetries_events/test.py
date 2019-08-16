import unittest
import logging
from .producer import Producer
import asyncio
from lsst.ts import salobj
from pprint import pprint

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


class TestTelemetries(unittest.TestCase):
    def setUp(self):
        salobj.set_random_lsst_dds_domain()

    def test_produced_message_with_telemetry_scalar(self):
        async def doit():
            async with Harness(initial_state=salobj.State.ENABLED) as harness:
                # Arrange
                heartbeat_producer = Producer(loop=asyncio.get_event_loop(
                ), domain=harness.csc.domain, csc_list=[('Test', harness.csc.salinfo.index)])
                cmd_data_sent = harness.csc.make_random_cmd_scalars()

                # Act
                await harness.remote.cmd_setScalars.start(cmd_data_sent, timeout=STD_TIMEOUT)

                # Assert
                tel_scalars = await harness.remote.tel_scalars.next(flush=False, timeout=STD_TIMEOUT)
                tel_parameters = tel_scalars._member_attributes
                expected_data = {p: {'value': getattr(tel_scalars, p), 'dataType': heartbeat_producer.getDataType(
                    getattr(tel_scalars, p))} for p in tel_parameters}
                expected_message = {
                    "category": "telemetry",
                    "data": [
                        {
                            "csc": "Test",
                            "salindex": harness.csc.salinfo.index,
                            "data": {
                                "scalars": expected_data
                            }
                        }
                    ]
                }

                message = heartbeat_producer.get_telemetry_message()

                # private_rcvStamp is generated on read and seems unpredictable now
                del message["data"][0]["data"]["scalars"]["private_rcvStamp"]
                del expected_message["data"][0]["data"]["scalars"]["private_rcvStamp"]
                self.assertEqual(message, expected_message)

                # clean up
                for remote in heartbeat_producer.remote_list:
                    await remote.close()

        asyncio.get_event_loop().run_until_complete(doit())



if __name__ == '__main__':
    unittest.main()
