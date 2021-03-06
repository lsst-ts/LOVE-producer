import asyncio
import datetime
import json
import os
import threading
from lsst.ts import salobj

MAX_LOST_HEARTBEATS_DEFAULT = 5
HEARTBEAT_TIMEOUT_DEFAULT = 15
NEVER_RECEIVED_TIMESTAMP = -1
NO_HEARTBEAT_EVENT_TIMESTAMP = -2
HEARTBEATS_CONFIG_PATH = "config.json"


class HeartbeatProducer:
    def __init__(self, domain, send_heartbeat, csc_list, remote=None):
        """Monitor CSC heartbeats and produces messages for the LOVE manager.

        It has a default configuration for the monitoring parameters which are overriden by
        a specific config.json file.

        Parameters
        ----------
        domain: salobj Domain object to create salobj Remotes
        send_heartbeat: callback coroutine that receives the message dictionary msg, to be sent later to the LOVE-manager
        csc_list: List of  (csc, salindex) pairs
        remote: Optional salobj.Remote object, to avoid creating duplicates
        """
        self.send_heartbeat = send_heartbeat
        self.domain = domain
        self.csc_list = csc_list
        self.remote = remote
        self.last_heartbeat_event = None

        # params to replace the defaults later
        path = os.path.join(os.path.dirname(__file__), HEARTBEATS_CONFIG_PATH)
        with open(path) as config_file:
            self.heartbeat_params = json.loads(config_file.read())

        self.remotes = []  # for cleanup

    def start(self):
        """Start the producer."""
        if not self.remote:
            for i in range(len(self.csc_list)):
                sal_lib_params = self.csc_list[i]
                print("- Listening to heartbeats from CSC: ", sal_lib_params)
                [sal_lib_name, index] = sal_lib_params

                asyncio.get_event_loop().create_task(
                    self.monitor_remote_heartbeat(sal_lib_name, index)
                )
        else:
            asyncio.get_event_loop().create_task(
                self.monitor_remote_heartbeat_callbacks(
                    self.remote.salinfo.name, self.remote.salinfo.index
                )
            )

    def get_heartbeat_message(self, remote_name, salindex, nlost_subsequent, timestamp):
        """Generates a message with the heartbeat info of a CSC in dictionary format.

        Parameters
        ----------
        remote_name: str
            Name of the CSC
        salindex: int
            Salindex of the CSC
        nlost_subsequent:
            Number of subsequent or consecutive lost heartbeats since last observed heartbeat
        timestamp: float
            Timestamp of the last observed heartbeat.

        Returns
        -------
        dict
            Dictionary that, converted to string, is compatible with the LOVE-manager message format.

        """

        # find the first element that matches the csc/salindex and use it instead of the default value
        max_lost_heartbeats = MAX_LOST_HEARTBEATS_DEFAULT
        if remote_name in self.heartbeat_params:
            max_lost_heartbeats = next(
                (
                    el["max_lost_heartbeats"]
                    for el in self.heartbeat_params[remote_name]
                    if el["index"] == salindex
                ),
                MAX_LOST_HEARTBEATS_DEFAULT,
            )

        if salindex is None:
            salindex = 0

        heartbeat = {
            "csc": remote_name,
            "salindex": salindex,
            "lost": nlost_subsequent,
            "last_heartbeat_timestamp": timestamp,
            "max_lost_heartbeats": max_lost_heartbeats,
        }
        message = {
            "category": "event",
            "data": [
                {"csc": "Heartbeat", "salindex": 0, "data": {"stream": heartbeat}}
            ],
        }

        return message

    async def monitor_remote_heartbeat(self, remote_name, salindex):
        """Continuously monitor the heafrtbeat of a given remote

        Parameters
        ----------
        remote_name: string
            Name fo the remote to monitor
        salindex: int
            Sal index of the remote to monitor
        """
        domain = self.domain
        if not self.remote:
            remote = salobj.Remote(domain=domain, name=remote_name, index=salindex)
        else:
            remote = self.remote
        self.remotes.append(remote)
        await remote.start_task
        nlost_subsequent = 0

        # find the first element that matches the csc/salindex and use it instead of the default value
        timeout = HEARTBEAT_TIMEOUT_DEFAULT
        if remote_name in self.heartbeat_params:
            timeout = next(
                (
                    el["heartbeat_timeout"]
                    for el in self.heartbeat_params[remote_name]
                    if el["index"] == salindex
                ),
                HEARTBEAT_TIMEOUT_DEFAULT,
            )

        timestamp = NEVER_RECEIVED_TIMESTAMP

        while True:
            try:
                if not hasattr(remote, "evt_heartbeat"):
                    timestamp = NO_HEARTBEAT_EVENT_TIMESTAMP
                    msg = self.get_heartbeat_message(
                        remote_name, salindex, nlost_subsequent, timestamp
                    )
                    await self.send_heartbeat(msg)
                    await asyncio.sleep(2)
                    continue
                await remote.evt_heartbeat.next(flush=True, timeout=timeout)
                nlost_subsequent = 0
                timestamp = datetime.datetime.now().timestamp()
            except asyncio.TimeoutError:
                nlost_subsequent += 1
            msg = self.get_heartbeat_message(
                remote_name, salindex, nlost_subsequent, timestamp
            )
            await self.send_heartbeat(msg)

    def set_heartbeat(self, heartbeat_event):
        """Sets the internal value for the latest hearbeat event received

        Parameters
        ----------
        heartbeat_event: salobj.Event
            salobj heartbeat event (evt_heartbeat)
        """
        self.last_heartbeat_event = heartbeat_event

    async def monitor_remote_heartbeat_callbacks(self, remote_name, salindex):
        """Continuously compare the latest heartbeat value and send messages to the manager

        Parameters
        ----------
        remote_name: string
            Name fo the remote to monitor
        salindex: int
            Sal index of the remote to monitor
        """
        domain = self.domain
        remote = self.remote
        self.remotes.append(remote)
        await remote.start_task
        nlost_subsequent = 0

        # find the first element that matches the csc/salindex and use it instead of the default value
        timeout = HEARTBEAT_TIMEOUT_DEFAULT
        if remote_name in self.heartbeat_params:
            timeout = next(
                (
                    el["heartbeat_timeout"]
                    for el in self.heartbeat_params[remote_name]
                    if el["index"] == salindex
                ),
                HEARTBEAT_TIMEOUT_DEFAULT,
            )

        timestamp = NEVER_RECEIVED_TIMESTAMP
        last_heartbeat_tested = None
        while True:
            try:
                if not self.last_heartbeat_event:
                    timestamp = NO_HEARTBEAT_EVENT_TIMESTAMP
                    msg = self.get_heartbeat_message(
                        remote_name, salindex, nlost_subsequent, timestamp
                    )
                    await self.send_heartbeat(msg)
                    await asyncio.sleep(2)
                    continue
                # await remote.evt_heartbeat.next(flush=True, timeout=timeout)
                await asyncio.sleep(timeout)
                if last_heartbeat_tested == self.last_heartbeat_event:
                    raise asyncio.TimeoutError
                last_heartbeat_tested = self.last_heartbeat_event
                nlost_subsequent = 0
                timestamp = datetime.datetime.now().timestamp()
            except asyncio.TimeoutError:
                nlost_subsequent += 1
            msg = self.get_heartbeat_message(
                remote_name, salindex, nlost_subsequent, timestamp
            )
            await self.send_heartbeat(msg)


if __name__ == "__main__":
    csc_list = [("ATDome", 1), ("ScriptQueue", 1), ("ScriptQueue", 2)]
    domain = salobj.Domain()
    loop = asyncio.get_event_loop()
    hb = HeartbeatProducer(domain, lambda m: print(m), csc_list)
    hb.start()
    loop.run_forever()
