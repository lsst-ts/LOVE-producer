#!/bin/bash
source .setup.sh
cd /usr/src/love/producer
pytest -p no:cacheprovider -p no:pytest_session2file