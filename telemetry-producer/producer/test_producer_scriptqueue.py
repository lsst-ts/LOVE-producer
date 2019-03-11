from producer_scriptqueue import ScriptQueueProducer
import time
sqp = ScriptQueueProducer()


while True:
    message = sqp.parse_queue_state()


    print('finished',{
        script['index']: script['expected_duration'] for script in message['finished_scripts'] if script['expected_duration'] != 'UNKNOWN'
    })

    print('waiting',{
        script['index']: script['expected_duration'] for script in message['waiting_scripts'] if script['expected_duration'] != 'UNKNOWN'
    })
   
    time.sleep(1)

