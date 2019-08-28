import asyncio
import datetime
import json
import threading
from lsst.ts import salobj

MAX_LOST_HEARTBEATS_DEFAULT = 5
HEARTBEAT_TIMEOUT_DEFAULT = 15
NEVER_RECEIVED_TIMESTAMP = -1
NO_HEARTBEAT_EVENT_TIMESTAMP = -2
HEARTBEATS_CONFIG_PATH = './heartbeats/config.json'


class HeartbeatProducer:

    def __init__(self, domain, send_heartbeat, csc_list):
        """Monitor CSC heartbeats and produces messages for the LOVE manager.

        It has a default configuration for the monitoring parameters which are overriden by
        a specific config.json file.

        Parameters
        ----------
        loop: asyncio event loop being used
        domain: salobj Domain object to create salobj Remotes
        send_heartbeat: callback that receives one argument, the message dictionary to be sent later to the LOVE-manager
        csc_list: List of  (csc, salindex) pairs
        """
        self.send_heartbeat = send_heartbeat
        self.domain = domain
        self.csc_list = csc_list

        # params to replace the defaults later
        with open(HEARTBEATS_CONFIG_PATH) as config_file:
            self.heartbeat_params = json.loads(config_file.read())

        self.remotes = []  # for cleanup

    def start(self):
        for i in range(len(self.csc_list)):
            sal_lib_params = self.csc_list[i]
            sal_lib_name = sal_lib_params[0]
            index = 0
            print('- Listening to heartbeats from CSC: ', sal_lib_params)
            if len(sal_lib_params) > 1:
                [sal_lib_name, index] = sal_lib_params
            index = int(index)

            asyncio.get_event_loop().create_task(self.monitor_remote_heartbeat(sal_lib_name, index))

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
            max_lost_heartbeats = next((el["max_lost_heartbeats"]
                                        for el in self.heartbeat_params[remote_name] if el["index"] == salindex), MAX_LOST_HEARTBEATS_DEFAULT)

        heartbeat = {
            'csc': remote_name,
            'salindex': salindex,
            'lost': nlost_subsequent,
            'last_heartbeat_timestamp': timestamp,
            'max_lost_heartbeats': max_lost_heartbeats
        }
        message = {
            'category': 'event',
            'data': [{
                'csc': 'Heartbeat',
                'salindex': 0,
                'data': {
                    'stream': heartbeat
                }

            }]
        }

        return message

    async def monitor_remote_heartbeat(self, remote_name, salindex):
        domain = self.domain
        remote = salobj.Remote(domain=domain, name=remote_name, index=salindex)
        self.remotes.append(remote)
        nlost_subsequent = 0

        # find the first element that matches the csc/salindex and use it instead of the default value
        timeout = HEARTBEAT_TIMEOUT_DEFAULT
        if remote_name in self.heartbeat_params:
            timeout = next((el["heartbeat_timeout"]
                            for el in self.heartbeat_params[remote_name] if el["index"] == salindex), HEARTBEAT_TIMEOUT_DEFAULT)

        timestamp = NEVER_RECEIVED_TIMESTAMP

        while True:
            try:
                # if random.random() > 0.2:
                #     await asyncio.sleep(2)
                #     raise asyncio.TimeoutError('sadsa')
                if not hasattr(remote, 'evt_heartbeat'):
                    timestamp = NO_HEARTBEAT_EVENT_TIMESTAMP
                    msg = self.get_heartbeat_message(
                        remote_name, salindex, nlost_subsequent, timestamp)
                    self.send_heartbeat(msg)
                    await asyncio.sleep(2)
                    continue
                await remote.evt_heartbeat.next(flush=False, timeout=timeout)
                nlost_subsequent = 0
                timestamp = datetime.datetime.now().timestamp()
            except asyncio.TimeoutError:
                nlost_subsequent += 1
            msg = self.get_heartbeat_message(
                remote_name, salindex, nlost_subsequent, timestamp)
            self.send_heartbeat(msg)


if __name__ == '__main__':
    csc_list = [('ATDome', 1), ('ScriptQueue', 1), ('ScriptQueue', 2)]
    domain = salobj.Domain()
    loop = asyncio.get_event_loop()
    hb = HeartbeatProducer(domain, lambda m: print(m), csc_list)
    hb.start()
    loop.run_forever()
