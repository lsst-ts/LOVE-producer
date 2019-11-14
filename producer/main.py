"""Main executable of the LOVE-producer."""
import asyncio
from telemetries_events.main import main as telemetries_events
from scriptqueue.main import main as scriptqueue
from heartbeats.main import main as heartbeats
from command_receiver.main import main as command_receiver

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(telemetries_events())
    loop.create_task(scriptqueue())
    loop.create_task(heartbeats())
    loop.create_task(command_receiver())
    loop.run_forever()