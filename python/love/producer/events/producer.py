import asyncio
import logging

from astropy.time import Time

from lsst.ts import salobj

from love.producer.producer_utils import get_data_type, make_stream_message, Settings

TIMEOUT = 10


class EventsProducer:
    """ Produces messages with events coming from several CSCs """

    def __init__(
        self,
        domain,
        csc_list,
        events_callback,
        heartbeat_callback=None,
        remote=None,
        log=None,
    ):

        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.events_callback = events_callback
        self.domain = domain
        self.remote_dict = {}
        self.initial_state_data = {}
        self.auto_remote_creation = True
        self.heartbeat_callback = heartbeat_callback
        if not remote:
            for name, salindex in csc_list:
                try:
                    self.log.debug(f"Listening to events from CSC: {name}:{salindex}.")
                    new_remote = salobj.Remote(domain=domain, name=name, index=salindex)
                    self.remote_dict[(name, salindex)] = new_remote

                except Exception:
                    self.log.exception(
                        f"Could not load events remote for {name}:{salindex}."
                    )
        else:
            name = remote.salinfo.name
            salindex = remote.salinfo.index
            self.remote_dict[(name, salindex)] = remote
            self.auto_remote_creation = False

    async def setup_callbacks(self):
        """Configures a callback for each remote created"""
        tasks = []
        for (name, salindex) in self.remote_dict:
            try:
                remote = self.remote_dict[(name, salindex)]
                tasks.append(self.set_remote_evt_callbacks(remote))
            except Exception:
                self.log.exception(
                    f"Could not setup events callback for: {name}:{salindex}."
                )
        await asyncio.gather(*tasks)

    async def set_remote_evt_callbacks(self, remote):
        """Set the callbacks for the events of a given remote

        Parameters
        ----------
        remote: object
            The remote to set callbacks to
        """
        remote_name = remote.salinfo.name
        index = remote.salinfo.index
        evt_names = remote.salinfo.event_names
        await remote.start_task
        for evt in evt_names:
            evt_key = f"evt_{evt}"
            evt_object = getattr(remote, evt_key)
            # aget before setting callback
            try:
                evt_data = evt_object.get()
                self.initial_state_data[(remote_name, index, evt)] = evt_data
            except Exception:
                self.initial_state_data[(remote_name, index, evt)] = None
            if evt_object.callback is None:
                self.log.debug(
                    f"Setting callback function for {remote.salinfo.name}:{remote.salinfo.index}:{evt}."
                )
                evt_object.callback = self.make_callback(
                    remote.salinfo.name, remote.salinfo.index, evt
                )
            else:
                self.log.warning(
                    f"Callback function for {remote.salinfo.name}:{remote.salinfo.index}:{evt} "
                    "already set. Skipping..."
                )

    def make_callback(self, csc, salindex, evt_name):
        """Returns a callback that produces a message with the event data

        Parameters
        ----------
        csc: string
            name of the CSC
        salindex: int
            SAL Index of the CSC
        evt_name: string
            Name of the event

        Returns
        -------
        callback: function
            The callback
        """

        def callback(evt_data):
            if Settings.trace_timestamps():
                rcv_time = Time.now().tai.datetime.timestamp()
            if evt_name == "heartbeat" and self.heartbeat_callback:
                self.heartbeat_callback(evt_data)
                return
            evt_parameters = list(evt_data._member_attributes)
            remote = self.remote_dict[(csc, salindex)]
            remote_name = remote.salinfo.name
            index = remote.salinfo.index
            evt_object = getattr(remote, f"evt_{evt_name}")
            self.initial_state_data[(remote_name, index, evt_name)] = evt_data
            evt_result = {
                p: {
                    "value": getattr(evt_data, p),
                    "dataType": get_data_type(getattr(evt_data, p)),
                    "units": f"{evt_object.metadata.field_info[p].units}",
                }
                for p in evt_parameters
            }
            if Settings.trace_timestamps():
                evt_result["producer_rcv"] = rcv_time
            message = make_stream_message("event", csc, salindex, evt_name, evt_result)
            self.events_callback(message)

        return callback

    async def send_initial_state_data(self):
        """Send all initial state data."""

        self.log.debug(f"Sending initial data.")

        for key in self.initial_state_data:

            (csc, salindex, evt_name) = key

            evt_data = self.initial_state_data[key]

            if evt_data is None or evt_name == "heartbeat":
                continue

            evt_parameters = list(evt_data._member_attributes)
            remote = self.remote_dict[(csc, salindex)]
            evt_object = getattr(remote, f"evt_{evt_name}")
            evt_result = {
                p: {
                    "value": getattr(evt_data, p),
                    "dataType": get_data_type(getattr(evt_data, p)),
                    "units": f"{evt_object.metadata.field_info[p].units}",
                }
                for p in evt_parameters
            }
            if Settings.trace_timestamps():
                evt_result["producer_rcv"] = Time.now().tai.datetime.timestamp()

            message = make_stream_message("event", csc, salindex, evt_name, evt_result)
            self.events_callback(message)

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
            if self.auto_remote_creation or csc == "Script":
                try:
                    self.remote_dict[(csc, salindex)] = salobj.Remote(
                        self.domain, csc, salindex
                    )
                    await self.set_remote_evt_callbacks(
                        self.remote_dict[(csc, salindex)]
                    )
                except RuntimeError:
                    return
            else:
                return

        remote = self.remote_dict[(csc, salindex)]
        remote_name = remote.salinfo.name
        index = remote.salinfo.index

        # safely request event data
        try:
            # get most recent data or wait TIMEOUT seconds for the first one
            key = (remote_name, index, event_name)
            evt_data = None
            if key in self.initial_state_data:
                evt_data = self.initial_state_data[(remote_name, index, event_name)]
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
                "dataType": get_data_type(parameter_data),
            }

        message = {
            "category": "event",
            "data": [
                {"csc": csc, "salindex": salindex, "data": {event_name: [result]}}
            ],
        }
        return message
