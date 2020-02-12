"""Main executable of the LOVE-producer."""
import asyncio
from telemetries.client import main as telemetries
from events.client import main as events
from scriptqueue.client import main as scriptqueue
from heartbeats.client import main as heartbeats
from command_receiver.client import main as command_receiver


if __name__ == '__main__':
    # with entrypoint(MemoryTracer(interval=10, top_results=10)) as loop:
    def exception_handler(loop, context):
        print("Caught the following exception")
        print(context)

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    loop.set_debug(True)
    loop.create_task(telemetries())
    loop.create_task(events())
    loop.create_task(heartbeats())
    loop.create_task(scriptqueue())
    loop.create_task(command_receiver())
    loop.run_forever()
