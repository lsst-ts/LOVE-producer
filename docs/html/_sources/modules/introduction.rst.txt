Introduction
===============

The LOVE-producer is part of the LSST Operation and Visualization Environment (L.O.V.E.) project.
It is written in Python.

The LOVE-producer is an intermediary between the LOVE-manager and SAL.
It handles communication to SAL components and communicates through websocket messages with the LOVE-manager.

The LOVE-producer :code:`main` module is the main point of execution, where the code for the different producers is run. The different producers are split into 4 different modules:

* :code:`command_receiver`:
* :code:`heartbeats`:
* :code:`scriptqueue`:
* :code:`telemetries_events`:
