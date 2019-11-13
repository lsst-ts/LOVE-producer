import asyncio
import json
import numpy as np
from utils import NumpyEncoder, getDataType
from lsst.ts import salobj


class Producer:
    """
        Class that creates remote objects using the salobj library
        emitting fake telemetry and event data which is then sent over with websockets
    """

    def __init__(self, domain, csc_list):
        self.remote_list = []
        for name, salindex in csc_list:
            print('- Listening to telemetries and events from CSC: ', (name, salindex))
            self.remote_list.append(salobj.Remote(domain=domain, name=name, index=salindex))
    
    def get_remote_tel_values(self, remote):
        tel_names = remote.salinfo.telemetry_names
        values = {}
        for tel in tel_names:
            tel_remote = getattr(remote, "tel_" + tel)
            data = tel_remote.get()
            if data is None:
                continue
            tel_parameters = list(data._member_attributes)
            tel_result = {p: {'value': getattr(data, p), 'dataType': getDataType(
                getattr(data, p))} for p in tel_parameters}
            values[tel] = tel_result
        return values

    def get_remote_event_values(self, remote):
        evt_names = remote.salinfo.event_names
        values = {}
        for evt in evt_names:
            evt_remote = getattr(remote, "evt_" + evt)
            evt_results = []
            while True:
                data = evt_remote.get_oldest()
                if data is None:
                    break
                evt_parameters = list(data._member_attributes)
                evt_result = {p: {'value': getattr(data, p), 'dataType': getDataType(
                    getattr(data, p))} for p in evt_parameters}
                evt_results.append(evt_result)
            if len(evt_results) == 0:
                continue
            values[evt] = evt_results
        return values

    def get_telemetry_message(self):
        output_list = []
        for remote in self.remote_list:
            values = self.get_remote_tel_values(remote)
            output = json.loads(json.dumps(values, cls=NumpyEncoder))

            output_list.append({
                'csc': remote.salinfo.name,
                'salindex': remote.salinfo.index,
                'data': output
            })

        message = {
            "category": "telemetry",
            "data": output_list
        }

        return message

    def get_events_message(self):
        output_list = []
        for i in range(len(self.remote_list)):
            remote = self.remote_list[i]
            values = self.get_remote_event_values(remote)
            output = json.loads(json.dumps(values, cls=NumpyEncoder))
            output_list.append({
                'csc': remote.salinfo.name,
                'salindex': remote.salinfo.index,
                'data': output
            })

        message = {
            "category": "event",
            "data": output_list
        }
        return message


    async def process_message(self, message):
            """ 
            Tries to obtain the current data for an event with salobj.

            Parameters
            ----------
            message: dictionary with the LOVE-schema see example:

            Returns
            -------
            answer: a dictionary such as those delivered by the Telemetries_Events producer

            Example
            ------

            message = {
                "category": "initial_state",
                "data": [{
                    "csc": "Test",
                    "salindex": 1,
                    "stream": {
                            "event_name": "summaryState"
                    }
                }]
            }
            answer = await producer.process_message(message)
            
            # {
            #     "category": "event",
            #     "data": [{
            #         "csc": "Test",
            #         "salindex": 1,
            #         "data": {
            #             "summaryState": [{
            #                 "summaryState": {
            #                     "value": 1,
            #                     "dataType": "Int"
            #                 }
            #             }]
            #         }
            #     }]
            # }


            """
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