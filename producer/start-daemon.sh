#!/bin/bash
. /home/saluser/.setup_sal_env.sh

export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer

python -u /usr/src/love/producer/main.py
