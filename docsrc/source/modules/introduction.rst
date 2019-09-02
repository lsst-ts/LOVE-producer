Overview
===============

.. image:: ../assets/Producer-overview.png

The LOVE-producer is a python module that uses salobj and websockets to produce messages between SAL and the LOVE-manager. "Messages" can be understood without distinction as events, telemetries, commands parameters and their acknowledgements.

The LOVE-producer (or just the Producer) is part of the LSST Operations and Visualization Environment (L.O.V.E).


Configuration
-------------

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
