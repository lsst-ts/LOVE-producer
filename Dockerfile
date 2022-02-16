ARG dev_cycle=develop
FROM lsstts/develop-env:${dev_cycle}

WORKDIR /usr/src/love
COPY . .
RUN source /opt/lsst/software/stack/loadLSST.bash && \
	pip install kafkit[aiohttp] aiokafka && \
	pip install -r requirements.txt && \
	pip install /usr/src/love/ && \
	pip install /home/saluser/repos/ts_utils

WORKDIR /home/saluser
CMD ["/usr/src/love/start-daemon.sh"]
