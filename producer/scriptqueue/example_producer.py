import asyncio
import json
import pprint
import time
import threading
from lsst.ts.scriptqueue import ScriptProcessState, ScriptState
from scriptqueue.producer import ScriptQueueProducer
# from lsst.ts import salobj
# import SALPY_ScriptQueue

loop = asyncio.get_event_loop()
t = threading.Thread(target=lambda: loop.run_forever())
t.start()


def send(x):
    pprint.pprint(json.loads(x["data"]["ScriptQueueState"]))


sqp = ScriptQueueProducer(loop, send)


async def coro():
    result = await sqp.queue.evt_script.next(flush=True)
    print('\n\n\n')
    print('salIndex', result.salIndex)
    print('cmdId', result.cmdId)
    print('isStandard', result.isStandard)
    print('path', result.path)
    print('priority', result.priority)
    print('processState', ScriptProcessState(result.processState))
    print('scriptState', ScriptState(result.scriptState))
    print('timestampConfigureEnd', result.timestampConfigureEnd)
    print('timestampConfigureStart', result.timestampConfigureStart)
    print('timestampProcessEnd', result.timestampProcessEnd)
    print('timestampProcessStart', result.timestampProcessStart)
    print('timestampRunStart', result.timestampRunStart)

while True:
    loop.run_until_complete(coro())
    time.sleep(1)

# sqp = ScriptQueueProducer(loop, lambda x:x)

# import os
# import websocket
# WS_HOST = os.environ["WEBSOCKET_HOST"]
# WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]
# # websocket.enableTrace(True)
# url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
# ws = websocket.WebSocketApp(url,
#                         on_message = main.on_ws_message,
#                         on_error = main.on_ws_error,
#                         on_close = main.on_ws_close)

# ws.on_open = lambda ws:print('asd')


# while True:
#     time.sleep(2)
