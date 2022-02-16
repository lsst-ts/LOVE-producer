#!/bin/bash
source .setup_dev.sh
pip install /usr/src/love/
run_love_producer $LOVE_CSC_PRODUCER --log-level 10
