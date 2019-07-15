import asyncio
import datetime
import json
import threading
from lsst.ts import salobj
from utils import NumpyEncoder


class HeartbeatProducer:

    def __init__(self, loop, domain, send_heartbeat, csc_list):
        self.loop = loop
        self.send_heartbeat = send_heartbeat
        self.domain = domain
        self.csc_list = csc_list
        self.heartbeat_params = json.loads(
            open('/usr/src/love/heartbeats/config.json').read())

    def start(self):
        for i in range(len(self.csc_list)):
            sal_lib_params = self.csc_list[i]
            sal_lib_name = sal_lib_params[0]
            index = 0
            print('- Listening to heartbeats from CSC: ', sal_lib_params)
            if len(sal_lib_params) > 1:
                [sal_lib_name, index] = sal_lib_params
            index = int(index)
            t = threading.Thread(target=self.add_remote_in_thread, args=[
                                 self.loop, index, sal_lib_name])
            t.start()

    def add_remote_in_thread(self, loop, index, sal_lib_name):
        asyncio.set_event_loop(loop)

        domain = self.domain
        remote = salobj.Remote(domain=domain, name=sal_lib_name, index=index)
        self.run(self.monitor_remote_heartbeat(remote))

    def run(self, task):
        if(asyncio.iscoroutine(task)):
            asyncio.run_coroutine_threadsafe(task, self.loop)
        elif asyncio.isfuture(task):
            asyncio.gather(task, loop=self.loop, return_exceptions=True)
        else:
            print('Unknown task type: ', task)

    def get_heartbeat_message(self, remote_name, salindex, nlost_subsequent, timestamp):
        heartbeat = {
            'csc': remote_name,
            'salindex': salindex,
            'lost': nlost_subsequent,
            'last_heartbeat_timestamp': timestamp,
            'max_lost_heartbeats': self.heartbeat_params[remote_name]
        }

        message = {
            'category': 'event',
            'csc': 'Heartbeat',
            'salindex': -1,            
            'data': json.dumps(heartbeat, cls=NumpyEncoder)
        }
        return message

    async def monitor_remote_heartbeat(self, remote):
        nlost_subsequent = 0
        remote_name = remote.salinfo.name
        salindex = remote.salinfo.index
        timeout = self.heartbeat_params[remote_name]

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
            self.send_heartbeat(msg)
