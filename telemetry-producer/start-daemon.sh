#!/bin/bash

# source scl_source enable devtoolset-6; source /home/opsim/stack/loadLSST.bash

# bits from run_and_config.sh
# NEW_UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
# export LSST_DDS_DOMAIN=SOCS-DOCKER-${HOSTNAME}-${NEW_UUID}

# make the libraries from salmaker available
# export LD_LIBRARY_PATH="/home/opsim/tsrepos/lib:"$LD_LIBRARY_PATH
# export PYTHONPATH="/home/opsim/tsrepos/lib/python:/home/opsim/tsrepos/ts_salobj/python:"$PYTHONPATH
# export PYTHONPATH="/home/opsim/tsrepos/ts_scriptqueue/python/lsst/ts/scriptqueue/ui":$PYTHONPATH
# export PYTHONPATH="/home/opsim/tsrepos/ts_scriptqueue/python/lsst":$PYTHONPATH

# alias cdtsrepos="cd /home/opsim/tsrepos"

# avoid running the myriad tests
# /bin/bash --rcfile /home/opsim/.opsim4_profile_fbs

# source /home/opsim/.opsim4_profile_fbs

# cd /home/opsim/tsrepos/ts_salobj
# setup -r .
# scons
# scons install declare

# cd /home/opsim/inria/producer
# pip install -r requirements.txt

# sleep 1000000000000000000000000000
# source /home/saluser/.setup.sh

# Source this file when starting the container to set it up
echo "#"
echo "# Loading LSST Stack"
. /opt/lsst/software/stack/loadLSST.bash
setup lsst_distrib
echo "#"
echo "# Loading sal environment"
. /home/saluser/repos/ts_sal/setup.env
echo "#"
echo "# Setting up sal, salobj and scriptqueue"

setup ts_xml -t current
setup ts_sal -t current
setup ts_salobj -t current
setup ts_scriptqueue -t current

/bin/bash --rcfile /home/saluser/.bashrc
          

python -u main.py
