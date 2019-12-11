import asyncio
import json
import threading
from lsst.ts import salobj


class Receiver:
    """
        Class that creates remote objects using the salobj library
    """

    def __init__(self, domain, csc_list):
        self.remote_dict = {}
        for name, salindex in csc_list:
            print('- Listening to commands for CSC: ', (name, salindex))
            try:
                remote = salobj.Remote(domain=domain, name=name, index=salindex)
                self.remote_dict[(name, salindex)] = remote
                if(name=='ScriptQueue' and ('Script',0) not in self.remote_dict):
                    self.remote_dict[('Script', 0)] = salobj.Remote(domain=domain, name='Script', index=0)
            except Exception as e:
                print('CSC', name, 'raised exception on Receiver:', e)
                

    async def on_message(self, data):
        try:
            if 'category' not in data:
                return
            if 'category' in data and data['category'] != 'cmd':
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

            answer = await self.execute_command(remote, cmd_name, params, data)

            return answer

        except Exception as e:
            print('Exception')
            print(e)

    async def execute_command(self, remote, cmd_name, params, data):
        print('\nExecuting command')
        try:
            # request command
            cmd = getattr(remote, cmd_name)
            cmd.set(**params)
            cmd_result = await cmd.start(timeout=10)

            # build output from input structure
            csc_data = data['data'][0]
            stream_data = csc_data['data']
            stream = list(stream_data.keys())[0]
            res = data
            res['category'] = 'ack'
            res['data'][0]['data'][stream]['result'] = cmd_result.result

            return res
        except Exception as e:
            print('Exception')
            print(e)
        print('Command finished')
