import asyncio
import json
import threading
from lsst.ts import salobj


class Receiver:
    """
        Class that creates remote objects using the salobj library
    """

    def __init__(self, loop, domain, csc_list):
        self.loop = loop
        self.remote_dict = {}

        for i in range(len(csc_list)):
            sal_lib_params = csc_list[i]
            sal_lib_name = sal_lib_params[0]
            index = 0
            if len(sal_lib_params) > 1:
                [sal_lib_name, index] = sal_lib_params
            index = int(index)
            t = threading.Thread(target=self.add_remote_in_thread, args=[
                                 self.loop, index, sal_lib_name, domain])
            t.start()

    def run(self, task):
        if(asyncio.iscoroutine(task)):
            asyncio.run_coroutine_threadsafe(task, self.loop)
        elif asyncio.isfuture(task):
            asyncio.gather(task, loop=self.loop, return_exceptions=True)
        else:
            print('Unknown task type: ', task)

    def add_remote_in_thread(self, loop, index, sal_lib_name, domain):
        asyncio.set_event_loop(loop)
        remote = salobj.Remote(domain=domain, name=sal_lib_name, index=index)

        self.remote_dict[(sal_lib_name, index)] = remote

    def process_message(self, message, ws):
        data = json.loads(message)
        print('\n**** data: ', data)
        try:
            if data['category'] != 'cmd':
                return
            csc_data = data['data'][0]
            csc = csc_data['csc']
            salindex = csc_data['salindex']
            stream_data = csc_data['data']
            stream = list(stream_data.keys())[0]
            cmd_data = stream_data[stream]
            cmd_name = cmd_data['cmd']
            params = cmd_data['params']
            remote = self.remote_dict[(csc, salindex)]
            t = threading.Thread(target=lambda remote, cmd_name, params, loop, ws:
                                 self.run(self.execute_command(remote, cmd_name, params, data, loop, ws)),
                                 args=[remote, cmd_name, params, self.loop, ws])
            t.start()
        except Exception as e:
            print('Exception')
            print(e)

    async def execute_command(self, remote, cmd_name, params, data, loop, ws):
        print('\nExecuting command')
        asyncio.set_event_loop(loop)
        try:
            cmd = getattr(remote, cmd_name)
            cmd.set(**params)
            cmd_result = await cmd.start(timeout=10)
            csc_data = data['data'][0]
            stream_data = csc_data['data']
            stream = list(stream_data.keys())[0]
            res = data
            res['category'] = 'ack'
            res['data'][0]['data'][stream]['result'] = cmd_result.result
            ws.send(json.dumps(res))
        except Exception as e:
            print('Exception')
            print(e)
        print('Command finished')
