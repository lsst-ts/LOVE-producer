import asyncio
import os
from lsst.ts import salobj
from lsst.ts import scriptqueue
from lsst.ts.idl.enums.ScriptQueue import Location

# Create the CSC and a remote to wait for events
salobj.set_random_lsst_dds_domain()
datadir = "/home/saluser/repos/ts_scriptqueue/tests/data"
standardpath = os.path.join(datadir, "standard")
externalpath = os.path.join(datadir, "external")
queue = scriptqueue.ScriptQueue(index=1,
                                standardpath=standardpath,
                                externalpath=externalpath,
                                verbose=True)
await queue.start_task
remote = salobj.Remote(domain=queue.domain, name="ScriptQueue", index=1)
await remote.start_task
await remote.cmd_start.start(timeout=30)
await remote.cmd_enable.start(timeout=30)

# Add a script
ack = await remote.cmd_add.set_start(isStandard=True,
                                          path="script1",
                                          config="wait_time: 0.1",
                                          location=Location.LAST,
                                          locationSalIndex=0,
                                          descr="test_add", timeout=5)
script_index = int(ack.result)
# Wait for it to reach the pastQueue
while True:
    state = await remote.evt_queue.next(flush=False)
    print(f"\033[92mqueue={state.salIndices[0]}, current={state.currentSalIndex}, past={state.pastSalIndices[0]}\u001b[0m")
    if state.pastSalIndices[0] == int(script_index):
        break

# Pause the queue (just in case), and wait for it to be paused
await remote.cmd_pause.start()
while True:
    state = await remote.evt_queue.next(flush=True)
    print(f'\033[92mrunning?{state.running}\u001b[0m')
    if not state.running:
        break

# Configure a remote to listen for callbacks of the evt_queue

callback_remote = salobj.Remote(domain=queue.domain, name="ScriptQueue", index=1)
await callback_remote.start_task

# the callback should save messages to a queue
message_queue = asyncio.Queue()
def callback(msg):
    asyncio.create_task(message_queue.put(msg))
callback_remote.evt_queue.callback = callback


message = asyncio.wait_for(await message_queue.get(), timeout=10)

