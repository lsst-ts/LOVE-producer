#!/bin/bash
. /home/saluser/.setup_dev.sh

export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer/

python -u /usr/src/love/producer/love_csc/client.py