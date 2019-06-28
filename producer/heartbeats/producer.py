import asyncio
import datetime
import json
import threading
from lsst.ts import salobj
from utils import NumpyEncoder


class HeartbeatProducer:

    def __init__(self, loop, send_heartbeat):
        self.loop = loop
        self.send_heartbeat = send_heartbeat
        self.heartbeat_params = json.loads(
            open('/usr/src/love/heartbeats/config.json').read())

    def start(self):
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

        domain = salobj.Domain()
        remote = salobj.Remote(domain=domain, name=sal_lib_name.split("_")[1], index=index)
        self.run(self.monitor_remote_heartbeat(remote))

    def run(self, task):
        if(asyncio.iscoroutine(task)):
            asyncio.run_coroutine_threadsafe(task, self.loop)
        elif asyncio.isfuture(task):
            asyncio.gather(task, loop=self.loop, return_exceptions=True)
        else:
            print('Unknown task type: ', task)

    def get_heartbeat_message(self, remote_name, nlost_subsequent, timestamp):
        heartbeat = {
            remote_name: {
                'lost': nlost_subsequent,
                'last_heartbeat_timestamp': timestamp,
                'max_lost_heartbeats': self.heartbeat_params[remote_name]
            }
        }

        message = {
            'category': 'event',
            'data': {
                'Heartbeat': json.dumps(heartbeat, cls=NumpyEncoder)
            }
        }
        return message

    async def monitor_remote_heartbeat(self, remote):
        nlost_subsequent = 0
        remote_name = remote.salinfo.name
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
                remote_name, nlost_subsequent, timestamp)
            self.send_heartbeat(msg)
