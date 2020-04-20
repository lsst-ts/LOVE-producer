import asyncio
import json
import numpy as np
from utils import NumpyEncoder, getDataType
from lsst.ts import salobj
import utils


class TelemetriesProducer:
    """  Produces messages with telemetries coming from several CSCs """

    def __init__(self, domain, csc_list):
        self.remote_list = []
        for name, salindex in csc_list:
            try:
                remote = salobj.Remote(domain=domain, name=name, index=salindex)
                self.remote_list.append(remote)

            except Exception as e:
                print('- Could not load telemetries remote for', name, salindex)
                print(e)

    def get_remote_tel_values(self, remote):
        tel_names = remote.salinfo.telemetry_names
        values = {}
        for tel in tel_names:
            tel_remote = getattr(remote, "tel_" + tel)
            data = tel_remote.get()
            if data is None:
                continue
            tel_parameters = list(data._member_attributes)
            tel_result = {
                p: {
                    'value': getattr(data, p),
                    'dataType': getDataType(getattr(data, p)),
                    'units': f"{tel_remote.metadata.field_info[p].units}"
                }
                for p in tel_parameters
            }
            values[tel] = tel_result
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
