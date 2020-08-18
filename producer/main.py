"""Main executable of the LOVE-producer."""

import asyncio
from telemetries.client import main as telemetries
from events.client import main as events
from scriptqueue.client import main as scriptqueue
from heartbeats.client import main as heartbeats
import os

TELEMETRIES = "TELEMETRIES"
EVENTS = "EVENTS"
CSC_HEARTBEATS = "CSC_HEARTBEATS"
SCRIPTQUEUE = "SCRIPTQUEUE"

   
def main():
    """
        Reads the LOVE_PRODUCERS environment variable and launches one or more
        producers depending on its content.
        LOVE_PRODUCERS must be a string of values separated by ":".
        If LOVE_PRODUCERS is None or '' all producers will be launched.
        Allowed values are:
            - TELEMETRIES 
            - EVENTS 
            - CSC_HEARTBEATS 
            - SCRIPTQUEUE 
        Examples:
        export LOVE_PRODUCERS=TELEMETRIES:EVENTS #loads telemetries and events producers
        export LOVE_PRODUCERS=TELEMETRIES #loads telemetries producer
        export LOVE_PRODUCERS= #loads all producers
        - 
    """
    LOVE_PRODUCERS = os.environ.get('LOVE_PRODUCERS')
    if LOVE_PRODUCERS is None:
        producers = [TELEMETRIES, EVENTS, CSC_HEARTBEATS, SCRIPTQUEUE]
    else:
        producers = LOVE_PRODUCERS.split(':')
    
    # with entrypoint(MemoryTracer(interval=10, top_results=10)) as loop:
    def exception_handler(loop, context):
        print("Caught the following exception")
        print(context)

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    # loop.set_debug(True)
    if TELEMETRIES in producers:
        print(f'creating {TELEMETRIES} producer')
        loop.create_task(telemetries())
    if EVENTS in producers:
        print(f'creating {EVENTS} producer')
        loop.create_task(events())
    if CSC_HEARTBEATS in producers:
        print(f'creating {CSC_HEARTBEATS} producer')
        loop.create_task(heartbeats())
    if SCRIPTQUEUE in producers:
        print(f'creating {SCRIPTQUEUE} producer')
        loop.create_task(scriptqueue())
    loop.run_forever()

if __name__ == '__main__':
    main()
