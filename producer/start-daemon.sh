#!/bin/bash

source .setup.sh
pip install websockets
export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer
python -u /usr/src/love/producer/main.py
