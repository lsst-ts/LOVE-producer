#!/bin/bash
source scl_source enable devtoolset-6
source /home/opsim/fix_salmaker/setup.env
source stack/loadLSST.bash
export LD_LIBRARY_PATH="/home/opsim/tsrepos/lib:"$LD_LIBRARY_PATH
export PYTHONPATH="/home/opsim/tsrepos/lib/python:"$PYTHONPATH
alias cdtsrepos="cd /home/opsim/tsrepos"
alias cdsaltest="cd /home/opsim/tsrepos/ts_sal/test"
/bin/bash
