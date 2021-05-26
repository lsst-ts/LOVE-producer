import json

from astropy.time import Time
from lsst.ts import salobj

from love.producer.producer_utils import NumpyEncoder, get_data_type, Settings


class TelemetriesProducer:
    """  Produces messages with telemetries coming from several CSCs """

    def __init__(self, domain, csc_list, remote=None):
        self.remote_list = []
        if not remote:
            for name, salindex in csc_list:
                try:
                    print("- Listening to telemetries from CSC: ", (name, salindex))
                    new_remote = salobj.Remote(domain=domain, name=name, index=salindex)
                    self.remote_list.append(new_remote)

                except Exception as e:
                    print("- Could not load telemetries remote for", name, salindex)
                    print(e)
        else:
            self.remote_list.append(remote)

    def get_remote_tel_values(self, remote):
        """Get telemetries from the Remote

        Parameters
        ----------
        remote: object
            The Remote

        Returns
        -------
        dict
            A dictionary of telemetry values indexed by telemetry
        """
        tel_names = remote.salinfo.telemetry_names
        values = {}
        for tel in tel_names:
            tel_remote = getattr(remote, "tel_" + tel)
            data = tel_remote.get()
            if Settings.trace_timestamps():
                rcv_time = Time.now().tai.datetime.timestamp()
            if data is None:
                continue
            tel_parameters = list(data._member_attributes)
            tel_result = {
                p: {
                    "value": getattr(data, p),
                    "dataType": get_data_type(getattr(data, p)),
                    "units": f"{tel_remote.metadata.field_info[p].units}",
                }
                for p in tel_parameters
            }
            if Settings.trace_timestamps():
                tel_result["producer_rcv"] = rcv_time
            values[tel] = tel_result
        return values

    def get_telemetry_message(self):
        """Return a formatted message with the telemetry data to be sent by the Client

        Returns
        -------
        dict
            The message
        """
        output_list = []
        for remote in self.remote_list:
            values = self.get_remote_tel_values(remote)
            output = json.loads(json.dumps(values, cls=NumpyEncoder))

            output_list.append(
                {
                    "csc": remote.salinfo.name,
                    "salindex": remote.salinfo.index,
                    "data": output,
                }
            )

        message = {"category": "telemetry", "data": output_list}

        return message
