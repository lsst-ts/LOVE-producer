How it works
===============

.. image:: ../assets/Producer-details.svg
The LOVE-Producer consists of several python classes (:code:`Telemetries and Events`, :code:`Heartbeats`, :code:`ScriptQueue State` and :code:`Command Receiver`) each refered to as "a Producer", and a python script :code:`main.py`. Each Producer provides an interface to extract specific information from the SAL parsed into a message in JSON format with a fixed schema. These messages are given to/requested by the :code:`main.py` script which is the main driver of the LOVE-producer program, in charge of handling the websockets communication with the LOVE-manager and reading the `config.json` file.


The :code:`main.py` file
------------------

It uses the `websocket` library to send messages to the address :code:`ws://<WS_HOST>/?password=<WS_PASS>`, :code:`<WS_HOST>` and :code:`<WS_PASS>` are read from environment variables. It configures each Producer according to the `config.json` and extracts data by either passing  callbacks or making direct calls to :code:`get_message` functions and send a dictionary in JSON format to the specified address. This is detailed in the next sections and also on the diagram at the top of the page. The JSON schema is  consistent with the LOVE-manager and has this structure

.. code-block:json

    {
        category: 'cmd'/'ack',
        data: [{
            csc: 'ScriptQueue',
            salindex: 1,
            data: {
                stream: {
                    cmd: 'CommandPath',
                    params: {
                        'param1': 'value1',
                        'param2': 'value2',
                        ...
                    },
                }
            }
        }]
    }


Telemetries and Events producer
--------------------------------------------

It creates a :code:`salobj.Remote` object for a list of :code:`CSC, salindex` pairs(created in the :code:`main.py` from the :code:`config.json` file). It provides a :code:`get_telemetry_message` that returns a dict containing the last value of each telemetry on each :code:`salobj.Remote`, and a :code:`get_events_message` that similarly extracts all events data a The :code:`main.py`. These two methods are called by the :code:`main.py` every two seconds.


Heartbeats producer
--------------------------------------------
Reports to the :code:`main.py` through a callback message containing info about the :code:`heartbeat` (generic) event of a list of :code:`(CSC, salindex)` pairs. The information contained in a heartbeat message consists of :

- Number of consecutive heartbeat lost, i.e., count of times :code:`remote.evt_heartbeat.next` throws a :code:`Timeout` error.
- Timestamp of the last received heartbeat. Defaults to :code:`-1` (never received heartbeat) and :code:`-2` if the topic does not have a :code:`heartbeat` event.
- Maximum number of heartbeats configured to be acceptable by the frontend.


ScriptQueue State producer
--------------------------------------------

Monitors the :code:`queue` state, creating instances of the :code:`ScriptQueue` and :code:`Script` :code:`salobj.Remote` objects, storing their states. It configures several callbacks that allow to update the stored state, and reports to the :code:`main.py` with a callback that sends a message with the state whenever any of these are called. It also monitors heartbeats of each script similarly to the :code:`heartbeats` Producer. Finally, additional to callbacks, it provides an :code:`update` method that sends :code:`show` commands to the SAL for the :code:`ScriptQueue` and each `Script` remote, triggering updates of the queue state. This :code:`update` method is called every 2 seconds by the :code:`main.py` script.




Commands receiver
--------------------------------------------

It provides a :code:`process_message` function that the :code:`main.py` script calls whenever it receives a command message from the `LOVE-manager`. This method uses this information to produce a command with :code:`salobj.Remote` and then returns back to the manager an acknowledgment message if the command runs succesfuly.

