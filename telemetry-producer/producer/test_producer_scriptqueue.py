from producer_scriptqueue import ScriptQueueProducer
# from importlib import reload
# reload(producer_scriptqueue)
sqp = ScriptQueueProducer()
# sqp.do_run()
import time
while True:
    sqp.send_ws_data(1)
    time.sleep(2)

# salindex = 100005
# self.queue.state.update_script_info(self.queue.queue.evt_script.get())
# info = {**sqp.queue.state.scripts[salindex]}
# info['script_state'] = info['script_state'].name
# info['process_state'] = info['process_state'].name

# from lsst.ts.scriptqueue import ScriptProcessState
# from lsst.ts.scriptqueue.base_script import ScriptState

# statesDict = { getattr(ScriptState, state).name: getattr(ScriptState, state).value for state in dir(ScriptState) if not state.startswith('__')}

