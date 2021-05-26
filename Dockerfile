ARG dev_cycle=develop
FROM lsstts/develop-env:${dev_cycle}

WORKDIR /usr/src/love
COPY . .
RUN source /opt/lsst/software/stack/loadLSST.bash && \
	pip install kafkit[aiohttp] aiokafka && \
	pip install -r requirements.txt

WORKDIR /home/saluser
CMD ["/usr/src/love/producer/start-daemon.sh"]
