#!/bin/bash

source .setup.sh
source /opt/lsst/software/stack/loadLSST.bash && setup lsst_distrib && \
    source /home/saluser/repos/ts_sal/setup.env 
pip install websockets
pip install aiomisc
export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer
if [[ $LSST_DDS_IP != *"."* ]]; then
  echo "Unset LSST_DDS_IP"
  unset LSST_DDS_IP
fi
python -u /usr/src/love/producer/main.py
