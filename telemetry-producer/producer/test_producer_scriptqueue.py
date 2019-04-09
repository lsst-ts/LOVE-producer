import time
import threading
from lsst.ts import salobj
import asyncio
import SALPY_ScriptQueue

from producer_scriptqueue import ScriptQueueProducer
import pprint
import json




from lsst.ts.scriptqueue.base_script import HEARTBEAT_INTERVAL





loop = asyncio.get_event_loop()
t = threading.Thread(
    target = lambda : loop.run_forever())
t.start()

sqp = ScriptQueueProducer(loop, lambda x:x)



print('will start loop')

while True:
    time.sleep(2)