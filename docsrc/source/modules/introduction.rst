*****************************
Overview
*****************************

Introduction
------------
The LOVE-producer is part of the LSST Operators Visualization Environment (L.O.V.E). It provides the necessary communication between the LOVE Manager and SAL.

.. image:: ../assets/Producer-overview.svg

It is written in Python and uses the `salobj` library to communicate with SAL and websockets to communicate with the LOVE Manager.
It reads telemetries and events from SAL and publishes them to the LOVE-manager.

Each CSC has its own producer. The producer is configured with the CSC name and the SAL index of the CSC in order to connect to the respective `salobj.Remote`.


Configurations
--------------
Three environment variables must be set to allow the producer communicate with the SAL and the LOVE-manager:

- :code:`LSST_DDS_PARTITION_PREFIX`: Used by :code:`salobj` to filter SAL messages in the network.
- :code:`PROCESS_CONNECTION_PASS`: Password used by the LOVE-manager to allow the reception of messages from the LOVE-producer.
- :code:`LOVE_CSC_PRODUCER`: Password used by the LOVE-manager to allow the reception of messages from the LOVE-producer.
- :code:`WEBSOCKET_HOST`: Hostname or IP address of the LOVE-manager service.
