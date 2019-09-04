import asyncio
import json
import numpy as np
from utils import NumpyEncoder, getDataType
from lsst.ts import salobj


class InitialStateProducer:
    def __init__(self, domain, csc_list):
        pass

    async def process_message(self, message):
        """ Tries to obtain the current data for an event with salobj """

        message = {
            "category": "event",
            "data": [{
                "csc": '',
                "salindex": 0,
                "data": {"summaryState": []}
            }]
        }
        return message
