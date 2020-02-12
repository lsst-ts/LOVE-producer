#!/usr/bin/env bash

. ~/.setup.sh
. ~/.bashrc

export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer/

python -u /usr/src/love/producer/love_csc/client.py