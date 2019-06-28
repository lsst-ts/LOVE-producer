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

    def __init__(self, loop):
        self.loop = loop
        self.remote_list = []

        sal_lib_param_list = [line.rstrip('\n') for line in open(
            '/usr/src/love/sallibs.config')]
        for i in range(len(sal_lib_param_list)):
            sal_lib_params = sal_lib_param_list[i].split(' ')
            sal_lib_name = sal_lib_params[0]
            index = 0
            print(sal_lib_params)
            if len(sal_lib_params) > 1:
                [sal_lib_name, index] = sal_lib_params
            index = int(index)
            t = threading.Thread(target=self.add_remote_in_thread, args=[
                                 self.loop, index, sal_lib_name])
            t.start()

    def add_remote_in_thread(self, loop, index, sal_lib_name):
        asyncio.set_event_loop(loop)
        remote = self.create_remote(index, sal_lib_name)
        self.remote_list.append(remote)

    def getDataType(self, value):
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

    def create_remote(self, index, sal_lib_name):
        """

        """
        print("\n make remote", sal_lib_name)
        domain = salobj.Domain()
        remote = salobj.Remote(domain=domain, name=sal_lib_name.split("_")[1], index=index)
        return remote

    def get_telemetry_message(self):
        output_dict = {}
        for i in range(len(self.remote_list)):
            remote = self.remote_list[i]
            values = self.get_remote_tel_values(remote)
            output = json.dumps(values, cls=NumpyEncoder)

            output_dict[remote.salinfo.name] = output
        message = {
            "category": "telemetry",
            "data": output_dict
        }
        return message

    def get_events_message(self):
        output_dict = {}
        for i in range(len(self.remote_list)):
            remote = self.remote_list[i]
            values = self.get_remote_event_values(remote)
            output = json.dumps(values, cls=NumpyEncoder)

            output_dict[remote.salinfo.name] = output

        message = {
            "category": "event",
            "data": output_dict
        }
        return message
