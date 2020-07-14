#!/bin/bash
. /home/saluser/.setup_dev.sh
cd /usr/src/love/producer
export PYTHONPATH=$PYTHONPATH:$(pwd)
export HIDE_TRACE_TIMESTAMPS=True
pytest -p no:cacheprovider -p no:pytest_session2file
