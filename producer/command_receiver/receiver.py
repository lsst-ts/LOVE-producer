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
        self.remote_list = []
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

        self.remote_list.append(remote)
        self.remote_dict[sal_lib_name] = remote

    def process_message(self, message, ws):
        data = json.loads(message)
        try:
            cmd_name = data['cmd']
            component_name = data['component']
            params = data['params']
            remote = self.remote_dict[component_name]
            t = threading.Thread(target=lambda remote, cmd_name, params, loop:
                                 self.run(self.execute_command(remote, cmd_name, params, loop)), args=[
                                     remote, cmd_name, params, self.loop])
            t.start()
        except Exception as e:
            print('Exception')
            print(e)

    async def execute_command(self, remote, cmd_name, params, loop):
        print('\nExecuting command')
        asyncio.set_event_loop(loop)
        try:
            cmd = getattr(remote, cmd_name)
            print('cmd', cmd)
            cmd.set(**params)
            await cmd.start(timeout=10)
        except Exception as e:
            print('Exception')
            print(e)
        print('Command finished')
