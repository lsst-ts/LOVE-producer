import asyncio
import json
import numpy as np
from astropy.time import Time
from utils import NumpyEncoder, getDataType
from lsst.ts import salobj
import utils


class EventsProducer:
    """ Produces messages with events coming from several CSCs """

    def __init__(self, domain, csc_list, events_callback):
        self.events_callback = events_callback
        self.domain = domain
        self.remote_dict = {}
        self.initial_state_remote_dict = {}
        for name, salindex in csc_list:
            try:
                print("- Listening to events from CSC: ", (name, salindex))
                remote = salobj.Remote(domain=domain, name=name, index=salindex)
                self.remote_dict[(name, salindex)] = remote
                self.initial_state_remote_dict[(name, salindex)] = salobj.Remote(
                    domain=domain, name=name, index=salindex
                )

            except Exception as e:
                print("- Could not load events remote for", name, salindex)
                print(e)

    def setup_callbacks(self):
        """Configures a callback for each remote created"""
        for (name, salindex) in self.remote_dict:
            try:
                remote = self.remote_dict[(name, salindex)]
                self.set_remote_evt_callbacks(remote)
            except Exception as e:
                print("- Could not setup events callback for", name, salindex)
                print(e)

    def set_remote_evt_callbacks(self, remote):
        evt_names = remote.salinfo.event_names
        for evt in evt_names:
            evt_object = getattr(remote, "evt_" + evt)
            evt_object.callback = self.make_callback(
                remote.salinfo.name, remote.salinfo.index, evt
            )

    def make_callback(self, csc, salindex, evt_name):
        """ Returns a callback that produces a message with the event data"""

        def callback(evt_data):
            rcv_time = Time.now().tai.datetime.timestamp()
            evt_parameters = list(evt_data._member_attributes)
            remote = self.remote_dict[(csc, salindex)]
            evt_object = getattr(remote, f"evt_{evt_name}")
            evt_result = {
                p: {
                    "value": getattr(evt_data, p),
                    "dataType": utils.getDataType(getattr(evt_data, p)),
                    "units": f"{evt_object.metadata.field_info[p].units}",
                }
                for p in evt_parameters
            }
            evt_result["producer_rcv"] = rcv_time
            message = utils.make_stream_message(
                "event", csc, salindex, evt_name, evt_result
            )
            self.events_callback(message)

        return callback

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
        event_name = request_data["data"]["event_name"]
        if (csc, salindex) not in self.remote_dict:
            try:
                self.remote_dict[(csc, salindex)] = salobj.Remote(
                    self.domain, csc, salindex
                )
                self.initial_state_remote_dict[(csc, salindex)] = salobj.Remote(
                    domain=self.domain, name=csc, index=salindex
                )
                self.set_remote_evt_callbacks(self.remote_dict[(csc, salindex)])
            except RuntimeError:
                return

        remote = self.initial_state_remote_dict[(csc, salindex)]
        evt_object = getattr(remote, "evt_{}".format(event_name))
        try:
            # check latest seen data, if not available then "request" it
            # evt_data = evt_object.get(flush=False)
            evt_data = await evt_object.aget()
            if evt_data is None:
                return
        except Exception as e:
            print(
                "InitialStateProducer failed to obtain data from {}-{}-{}".format(
                    csc, salindex, event_name
                )
            )
            print(e)
            return
        result = {}
        for parameter_name in evt_data._member_attributes:
            result[parameter_name] = getattr(evt_data, parameter_name)
            parameter_data = getattr(evt_data, parameter_name)
            result[parameter_name] = {
                "value": parameter_data,
                "dataType": getDataType(parameter_data),
            }

        message = {
            "category": "event",
            "data": [
                {"csc": csc, "salindex": salindex, "data": {event_name: [result]}}
            ],
        }
        return message
