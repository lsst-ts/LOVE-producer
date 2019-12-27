import logging
from command_receiver.receiver import Receiver
import asyncio
from lsst.ts import salobj
import json
import asynctest
import utils

index_gen = salobj.index_generator()

TIMEOUT = 15

class TestCommandsFromMessages(asynctest.TestCase):
    async def test_command_ack(self):
        salobj.set_random_lsst_dds_domain()
        index = next(index_gen)
        csc = salobj.TestCsc(index=index, config_dir=None, initial_state=salobj.State.ENABLED)
        remote = salobj.Remote(domain=csc.domain, name="Test", index=index)
        await asyncio.wait_for(asyncio.gather(csc.start_task, remote.start_task), TIMEOUT)

        # Arrange
        cmd_data_sent = csc.make_random_cmd_scalars()
        cmd_receiver = Receiver(domain=csc.domain, csc_list=[('Test', csc.salinfo.index)])
        cmd_message = {
            "category": "cmd",
            "data": [
                {
                    "csc": "Test",
                    "salindex": csc.salinfo.index,
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
        answer = await asyncio.wait_for(cmd_receiver.on_message(cmd_message), TIMEOUT)

        # Assert
        expected_answer = cmd_message.copy()
        expected_answer["category"] = "ack"
        expected_answer["data"][0]["data"]["stream"]["result"] = "Done"

        self.assertEqual(expected_answer, answer)
        await asyncio.wait_for(asyncio.gather(remote.close(), csc.close()), TIMEOUT)
