import time
import threading
from lsst.ts import salobj
import asyncio
import SALPY_ScriptQueue

from producer_scriptqueue import ScriptQueueProducer
import pprint
import json

loop = asyncio.get_event_loop()
t = threading.Thread(
    target = lambda : loop.run_forever())
t.start()

def send(x):
    print(10*'\ns')
    pprint.pprint(json.loads(x['data']['ScriptQueueState']))
sqp = ScriptQueueProducer(
    loop, 
    send
)

while True:
    time.sleep(2)