import logging
from .receiver import Receiver
import asyncio
from lsst.ts import salobj
import json
import unittest
from utils import NumpyEncoder

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


class TestCommandsFromMessages(unittest.TestCase):
    def setUp(self):
        salobj.set_random_lsst_dds_domain()
        self.maxDiff = None

    def test_command_ack(self):
        async def doit():
            async with Harness(initial_state=salobj.State.ENABLED) as harness:
                # Arrange
                cmd_data_sent = harness.csc.make_random_cmd_scalars()
                cmd_receiver = Receiver(domain=harness.csc.domain, csc_list=[('Test', harness.csc.salinfo.index)])
                cmd_message = {
                    "category": "cmd",
                    "data": [
                        {
                            "csc": "Test",
                            "salindex": harness.csc.salinfo.index,
                            "data": {
                                "stream": {
                                    "cmd": "cmd_setScalars",
                                    "params": dict(cmd_data_sent.get_vars())
                                }
                            }
                        }
                    ]
                }

                # Act
                answer = await cmd_receiver.process_message(json.dumps(cmd_message, cls=NumpyEncoder))

                # Assert
                expected_answer = cmd_message.copy()
                expected_answer["category"] = "ack"
                expected_answer["data"][0]["data"]["stream"]["result"] = "Done"

                self.assertEqual(expected_answer, answer)

        asyncio.get_event_loop().run_until_complete(doit())


if __name__ == '__main__':
    unittest.main()
