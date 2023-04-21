*****************************
Overview and configuration
*****************************
This repository contains two software components: the LOVE Producer and the LOVE CSC. Both of these components are part of the LSST Operators Visualization Environment (L.O.V.E) and provide the necessary communication between the LOVE Manager and SAL. 

################
Producer
################

.. image:: ../assets/Producer-overview.svg

The LOVE-producer is a python module that uses salobj and websockets to produce messages between SAL and the LOVE-manager. "Messages" can be understood without distinction as events, telemetries or commands parameters and their acknowledgements.

As shown in the figure, the :code:`config.json` gives information of which SAL topics (and their indices) to read data from using the salobj library so this data can be forwarded to the LOVE-manager. Environment variables are also read to configure the communication with the SAL and the LOVE-manager. At the same time, the LOVE-manager can send commands parameters to execute commands with :code:`salobj`, returning a message acknowledging the successful reception of said command or an error message. 


Choosing SAL topics with :code:`config.json`
--------------------------------------------
The LOVE-producer reads a :code:`config.json` file (located in the :code:`producer/config/` folder) to create the instances of the :code:`salobj.Remote` class that are used to read SAL data and send commands. This file specifies each topic name and the SAL index for which messages will be produced. For example:

.. code-block:: json

    {
        "Test": [
            { "index": 1, "source": "command_sim" }
        ],
        "ScriptQueue": [
            { "index": 1, "source": "command_sim" },
            { "index": 2, "source": "command_sim" }
        ]
    }

configures the Producer to produce messages from/to the :code:`Test` CSC with index :code:`1` and the :code:`ScriptQueue` CSCs with indices :code:`1` and :code:`2`. The `source` parameter is ignored but kept for consistency in the integration with the `LOVE-simulator`.


Configuring communications with environment variables
-----------------------------------------------------
Three environment variables must be set to allow the producer communicate with the SAL and the LOVE-manager:

- :code:`LSST_DDS_DOMAIN`: Used by :code:`salobj` to filter SAL messages in the network.
- :code:`WS_HOST`: Hostname or IP adcress of the LOVE-manager.
- :code:`WS_PASS`: Password used by the LOVE-manager to allow the reception of messages from the LOVE-producer.


################
LOVE CSC
################

.. image:: ../assets/LOVE-CSC.svg

The LOVE CSC component is a python module that listens to messages (currently limited to observation logs) sent from the LOVE Manager and publishes them to SAL through :code:`salobj`.

