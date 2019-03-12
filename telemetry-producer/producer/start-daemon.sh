#!/bin/bash

source /home/saluser/.setup.sh

run_script_queue.py 1 ~/repos/ts_scriptqueue/tests/data/standard/ ~/repos/ts_scriptqueue/tests/data/external/ &

python -u /usr/src/love/main.py
