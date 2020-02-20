"""Main executable of the LOVE-producer."""
import asyncio
from telemetries.client import main as telemetries
from events.client import main as events
from scriptqueue.client import main as scriptqueue
from heartbeats.client import main as heartbeats
from command_receiver.client import main as command_receiver
import os

TELEMETRIES = "TELEMETRIES"
EVENTS = "EVENTS"
CSC_HEARTBEATS = "CSC_HEARTBEATS"
SCRIPTQUEUE = "SCRIPTQUEUE"
COMMANDS = "COMMANDS"

if __name__ == '__main__':
    producers = os.environ.get('LOVE_PRODUCERS').split(':')
    if len(producers) == 0:
        producers = [TELEMETRIES, EVENTS, CSC_HEARTBEATS, SCRIPTQUEUE, COMMANDS]
        
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
    if COMMANDS in producers:
        print(f'creating {COMMANDS} producer')
        loop.create_task(command_receiver())
    loop.run_forever()
