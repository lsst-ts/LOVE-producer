import asyncio
import datetime
import json
import threading
from lsst.ts import salobj
from utils import NumpyEncoder

MAX_LOST_HEARTBEATS_DEFAULT = 5
HEARTBEAT_TIMEOUT_DEFAULT = 15


class HeartbeatProducer:
    def __init__(self, loop, domain, send_heartbeat, csc_list):
        """Monitors CSC heartbeats and produces messages for the LOVE manager

        It has a default configuration for the monitoring parameters which are overriden by
        a specific config.json file.

        Parameters
        ----------
        loop: asyncio event loop being used
        domain: salobj Domain object to create salobj Remotes
        send_heartbeat: callback that receives one argument, the message dictionary to be sent later to the LOVE-manager
        csc_list: List of  (csc, salindex) pairs
        """
        self.loop = loop
        self.send_heartbeat = send_heartbeat
        self.domain = domain
        self.csc_list = csc_list
        self.heartbeat_params = json.loads(
            open('/usr/src/love/heartbeats/config.json').read())

        for csc, salindex in csc_list:
            if not csc in self.heartbeat_params:
                self.heartbeat_params[csc] = [{
                    {
                        "index": salindex,
                        "max_lost_heartbeats": MAX_LOST_HEARTBEATS_DEFAULT,
                        "heartbeat_timeout": HEARTBEAT_TIMEOUT_DEFAULT
                    }
                }]
                continue

            has_salindex = next((True for el in self.heartbeat_params[csc] if el["index"] == salindex), False)
            if not has_salindex:
                self.heartbeat_params[csc].append({
                    {
                        "index": salindex,
                        "max_lost_heartbeats": MAX_LOST_HEARTBEATS_DEFAULT,
                        "heartbeat_timeout": HEARTBEAT_TIMEOUT_DEFAULT
                    }
                })

    def start(self):
        for i in range(len(self.csc_list)):
            sal_lib_params = self.csc_list[i]
            sal_lib_name = sal_lib_params[0]
            index = 0
            print('- Listening to heartbeats from CSC: ', sal_lib_params)
            if len(sal_lib_params) > 1:
                [sal_lib_name, index] = sal_lib_params
            index = int(index)

            self.loop.create_task(self.monitor_remote_heartbeat(sal_lib_name, index))

    def run(self, task):
        if(asyncio.iscoroutine(task)):
            asyncio.run_coroutine_threadsafe(task, self.loop)
        elif asyncio.isfuture(task):
            asyncio.gather(task, loop=self.loop, return_exceptions=True)
        else:
            print('Unknown task type: ', task)

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

        heartbeat = {
            'csc': remote_name,
            'salindex': salindex,
            'lost': nlost_subsequent,
            'last_heartbeat_timestamp': timestamp,
            'max_lost_heartbeats': self.heartbeat_params[remote_name]['max_lost_heartbeats']
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
        nlost_subsequent = 0
        timeout = self.heartbeat_params[remote_name]['heartbeat_timeout']
        timestamp = -1
        while True:
            try:
                # if random.random() > 0.2:
                #     await asyncio.sleep(2)
                #     raise asyncio.TimeoutError('sadsa')
                await remote.evt_heartbeat.next(flush=False, timeout=timeout)
                nlost_subsequent = 0
                timestamp = datetime.datetime.now().timestamp()
            except asyncio.TimeoutError:
                nlost_subsequent += 1
            msg = self.get_heartbeat_message(
                remote_name, salindex, nlost_subsequent, timestamp)
            print(remote_name, salindex, '|', msg['data'][0]['data']['stream'])
            self.send_heartbeat(msg)
