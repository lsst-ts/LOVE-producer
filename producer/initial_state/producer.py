import asyncio
import json
import numpy as np
from utils import NumpyEncoder, getDataType
from lsst.ts import salobj


class InitialStateProducer:
    def __init__(self, domain, csc_list):
        self.remote_dict = {}
        for (csc, salindex) in csc_list:
            try:
                self.remote_dict[(csc, salindex)] = salobj.Remote(domain, csc, salindex)
                print('- Loaded InitialState Remote for', csc, salindex)
            except Exception as e:
                print('InitialStateProducer could not load Remote for', csc, salindex)

    async def process_message(self, message):
        """ Tries to obtain the current data for an event with salobj """
        request_data = message["data"][0]
        csc = request_data["csc"]
        salindex = int(request_data["salindex"])
        event_name = request_data["stream"]["event_name"]
        if((csc, salindex) not in self.remote_dict):
            return
        remote = self.remote_dict[(csc, salindex)]
        evt_object = getattr(remote, "evt_{}".format(event_name))
        try:
            # check latest seen data, if not available then "request" it
            evt_data = evt_object.get(flush=False)
            if evt_data is None:
                evt_data = await evt_object.next(flush=False, timeout=60)
        except Exception as e:
            print('InitialStateProducer failed to obtain data from {}-{}-{}'.format(csc, salindex, event_name))
            print(e)
            return
        result = {}
        for parameter_name in evt_data._member_attributes:
            result[parameter_name] = getattr(evt_data, parameter_name)
            parameter_data = getattr(evt_data, parameter_name)
            result[parameter_name] = {
                'value': parameter_data,
                'dataType': getDataType(parameter_data)
            }

        message = {
            "category": "event",
            "data": [{
                "csc": csc,
                "salindex": salindex,
                "data": {event_name: [result]}
            }]
        }
        return message
