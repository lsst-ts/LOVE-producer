import asyncio
import json
import numpy as np
import threading
from utils import NumpyEncoder
from lsst.ts import salobj


class Producer:
    """
        Class that creates remote objects using the salobj library
        emitting fake telemetry and event data which is then sent over with websockets
    """

    def __init__(self, loop, domain, csc_list):
        self.loop = loop
        self.remote_list = []
        for name, salindex in csc_list:
            print('- Listening to telemetries and events from CSC: ', (name, salindex))
            self.remote_list.append(salobj.Remote(domain=domain, name=name, index=salindex))

    def getDataType(self, value):
        if isinstance(value, (np.ndarray)) and value.ndim == 0:
            return 'Array<%s>' % self.getDataType(value.item())

        if isinstance(value, (list, tuple, np.ndarray)):
            return 'Array<%s>' % self.getDataType(value[0])
        if isinstance(value, (int, np.integer)):
            return 'Int'
        if isinstance(value, float):
            return 'Float'
        if isinstance(value, str):
            return 'String'
        return 'None'

    def get_remote_tel_values(self, remote):
        tel_names = remote.salinfo.telemetry_names
        values = {}
        for tel in tel_names:
            tel_remote = getattr(remote, "tel_" + tel)
            data = tel_remote.get()
            if data is None:
                continue
            tel_parameters = list(data._member_attributes)
            tel_result = {p: {'value': getattr(data, p), 'dataType': self.getDataType(
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
                evt_result = {p: {'value': getattr(data, p), 'dataType': self.getDataType(
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
