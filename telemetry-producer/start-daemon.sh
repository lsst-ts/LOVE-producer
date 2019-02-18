#!/bin/bash

source scl_source enable devtoolset-6; source /home/opsim/stack/loadLSST.bash

# bits from run_and_config.sh
NEW_UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
export LSST_DDS_DOMAIN=SOCS-DOCKER-${HOSTNAME}-${NEW_UUID}

# make the libraries from salmaker available
export LD_LIBRARY_PATH="/home/opsim/tsrepos/lib:"$LD_LIBRARY_PATH
export PYTHONPATH="/home/opsim/tsrepos/lib/python:/home/opsim/tsrepos/ts_salobj/python:"$PYTHONPATH

#export WEBSOCKET_HOST="echo.websocket.org:80"
export WEBSOCKET_HOST="localhost:8000/ws/subscription"

alias cdtsrepos="cd /home/opsim/tsrepos"

# avoid running the myriad tests
# /bin/bash --rcfile /home/opsim/.opsim4_profile_fbs

source /home/opsim/.opsim4_profile_fbs

# cd /home/opsim/tsrepos/ts_salobj
# setup -r .
# scons
# scons install declare

cd /home/opsim/inria/producer
# pip install -r requirements.txt

python scheduler.py