import asyncio
import importlib
import json
import numpy as np
import threading
from utils import NumpyEncoder
from lsst.ts import salobj


class Producer:
    """
        Class that creates remote and controller objects using the salobj library
        emitting fake telemetry and event data which is then sent over with websockets
    """

    def __init__(self, loop):
        self.loop = loop
        self.remote_list = []
        self.controller_list = []

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
            sal_lib = importlib.import_module(sal_lib_name)
            t = threading.Thread(target=self.add_remote_in_thread, args=[
                                 sal_lib, self.loop, index])
            t.start()

    def add_remote_in_thread(self, sal_lib, loop, index):
        asyncio.set_event_loop(loop)
        remote, controller = self.create_remote_and_controller(sal_lib, index)
        self.remote_list.append(remote)
        self.controller_list.append(controller)

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
        tel_names = remote.salinfo.manager.getTelemetryNames()
        values = {}
        for tel in tel_names:
            tel_remote = getattr(remote, "tel_" + tel)
            data = tel_remote.get()
            if data is None:
                continue
            tel_parameters = [x for x in dir(data) if not x.startswith('__')]
            tel_result = {p: {'value': getattr(data, p), 'dataType': self.getDataType(
                getattr(data, p))} for p in tel_parameters}
            values[tel] = tel_result
        return values

    def get_remote_event_values(self, remote):
        evt_names = remote.salinfo.manager.getEventNames()
        values = {}
        for evt in evt_names:
            evt_remote = getattr(remote, "evt_" + evt)
            evt_results = []
            while True:
                data = evt_remote.get_oldest()
                if data is None:
                    break
                evt_parameters = [x for x in dir(
                    data) if not x.startswith('__')]
                evt_result = {p: {'value': getattr(data, p), 'dataType': self.getDataType(
                    getattr(data, p))} for p in evt_parameters}
                evt_results.append(evt_result)
            if len(evt_results) == 0:
                continue
            values[evt] = evt_results
        return values

    def create_remote_and_controller(self, sallib, index):
        """

        """
        print("\n make remote", sallib)
        remote = salobj.Remote(sallib, index)
        print("make controller", sallib)
        controller = salobj.Controller(sallib, index)
        return remote, controller

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
