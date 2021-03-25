#!/bin/bash
. /home/saluser/.setup_sal_env.sh

export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer
if [[ $LSST_DDS_IP != *"."* ]]; then
  echo "Unset LSST_DDS_IP"
  unset LSST_DDS_IP
fi

python -u /usr/src/love/producer/main.py &

pid="$!"

wait ${pid}
