#!/bin/bash
. /home/saluser/.setup_dev.sh
cd /usr/src/love/producer
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest -p no:cacheprovider -p no:pytest_session2file