#!/bin/bash
. /home/saluser/.setup_sal_env.sh

export PYTHONPATH=$PYTHONPATH:/usr/src/love/producer/

/home/saluser/repos/ts_sal/bin/make_idl_files.py LOVE
python -u /usr/src/love/producer/love_csc/client.py
