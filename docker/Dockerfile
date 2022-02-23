ARG dev_cycle=develop
FROM lsstts/develop-env:${dev_cycle}

WORKDIR /usr/src/love
COPY . .
COPY docker/start-daemon.sh .

RUN source /opt/lsst/software/stack/loadLSST.bash && \
	pip install -r requirements.txt && \
	pip install /usr/src/love

WORKDIR /home/saluser
CMD ["/usr/src/love/start-daemon.sh"]
