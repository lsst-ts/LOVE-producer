import unittest
import logging
import asyncio
from lsst.ts import salobj
from .producer import InitialStateProducer

STD_TIMEOUT = 5  # timeout for command ack
SHOW_LOG_MESSAGES = True

index_gen = salobj.index_generator()


class Harness:
    def __init__(self, initial_state, config_dir=None, CscClass=salobj.TestCsc, index=next(index_gen)):
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

    def test_default_initial_summaryState(self):
        """
        Test it can produce the default summaryState message correctly
        when the producer starts after the event was triggered
        """

        async def doit():
            async with Harness(initial_state=salobj.State.ENABLED) as harness:
                # Arrange
                initial_state = await harness.remote.evt_summaryState.next(flush=False)

                producer = InitialStateProducer(domain=harness.csc.domain, csc_list=[
                    ('Test', harness.csc.salinfo.index)])

                # Act

                produced_message = await producer.process_message({
                    "category": "initial_state",
                    "data": [{
                        "csc": "Test",
                        "salindex": harness.csc.salinfo.index,
                        "stream": {
                                "event_name": "summaryState"
                        }
                    }]
                })

                to_delete = ["TestID", "private_host", "private_origin", "private_rcvStamp",
                             "private_revCode", "private_seqNum", "private_sndStamp", "priority"]

                for key in to_delete:
                    if key in produced_message["data"][0]["data"]["summaryState"][0]:
                        del produced_message["data"][0]["data"]["summaryState"][0][key]

                # Assert
                expected_message = {
                    "category": "event",
                    "data": [{
                        "csc": "Test",
                        "salindex": harness.csc.salinfo.index,
                        "data": {
                            "summaryState": [{
                                "summaryState": {
                                    "value": salobj.State.ENABLED.value,
                                    "dataType": "Int"
                                }
                            }]
                        }
                    }]
                }

                self.assertEqual(produced_message, expected_message)
        asyncio.get_event_loop().run_until_complete(doit())

    def test_summaryState_change_after_producer_was_created(self):
        """
        Test it can produce the summaryState message correctly
        when a change happens after the producer hsa been created
        """

        async def doit():
            async with Harness(initial_state=salobj.State.STANDBY) as harness:
                    # Arrange
                initial_state = await harness.remote.evt_summaryState.next(flush=False)
                self.assertEqual(initial_state.summaryState, salobj.State.STANDBY.value)

                producer = InitialStateProducer(domain=harness.csc.domain, csc_list=[
                    ('Test', harness.csc.salinfo.index)])

                # Act
                await harness.remote.cmd_start.start()
                produced_message = await producer.process_message({
                    "category": "initial_state",
                    "data": [{
                        "csc": "Test",
                        "salindex": harness.csc.salinfo.index,
                        "stream": {
                            "event_name": "summaryState"
                        }
                    }]
                })
                # Assert

                second_state = await harness.remote.evt_summaryState.next(flush=False)

                to_delete = ["TestID", "private_host", "private_origin", "private_rcvStamp",
                             "private_revCode", "private_seqNum", "private_sndStamp", "priority"]

                for key in to_delete:
                    if key in produced_message["data"][0]["data"]["summaryState"][0]:
                        del produced_message["data"][0]["data"]["summaryState"][0][key]

                # Assert
                expected_message = {
                    "category": "event",
                    "data": [{
                        "csc": "Test",
                        "salindex": harness.csc.salinfo.index,
                        "data": {
                            "summaryState": [{
                                "summaryState": {
                                    "value": salobj.State.DISABLED.value,
                                    "dataType": "Int"
                                }
                            }]
                        }
                    }]
                }
                self.assertEqual(produced_message, expected_message)
        asyncio.get_event_loop().run_until_complete(doit())

    # def test_csc_created_after_producer(self):
    #     """
    #     Test it can produce the summaryState message correctly
    #     when the producer is created before the CSC
    #     """

    #     async def doit():
    #         index = next(index_gen)
    #         producer = InitialStateProducer(domain=salobj.Domain(), csc_list=[('Test', index)])
    #         harness =  Harness(initial_state=salobj.State.STANDBY)
    #         await harness.csc.start_task

    #         # Act
    #         produced_message = await producer.process_message({
    #             "category": "initial_state",
    #             "data": [{
    #                 "csc": "Test",
    #                 "salindex": index,
    #                 "data": {
    #                     "stream": {
    #                         "event_name": "summaryState"
    #                     }
    #                 }
    #             }]
    #         })
    #         # Assert
    #         to_delete = ["TestID", "private_host", "private_origin", "private_rcvStamp",
    #                         "private_revCode", "private_seqNum", "private_sndStamp", "priority"]

    #         for key in to_delete:
    #             if key in produced_message["data"][0]["data"]["summaryState"][0]:
    #                 del produced_message["data"][0]["data"]["summaryState"][0][key]

    #         # Assert
    #         expected_message = {
    #             "category": "event",
    #             "data": [{
    #                 "csc": "Test",
    #                 "salindex": index,
    #                 "data": {
    #                     "summaryState": [{
    #                         "summaryState": {
    #                             "value": salobj.State.STANDBY.value,
    #                             "dataType": "Int"
    #                         }
    #                     }]
    #                 }
    #             }]
    #         }
    #         self.assertEqual(produced_message, expected_message)
    #     asyncio.get_event_loop().run_until_complete(doit())


if __name__ == '__main__':
    unittest.main()
