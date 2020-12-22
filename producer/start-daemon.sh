#!/bin/bash
. /home/saluser/.setup_dev.sh

export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer
if [[ $LSST_DDS_IP != *"."* ]]; then
  echo "Unset LSST_DDS_IP"
  unset LSST_DDS_IP
fi
/home/saluser/repos/ts_sal/bin/make_idl_files.py LOVE
python -u /usr/src/love/producer/main.py
