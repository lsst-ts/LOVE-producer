ARG dev_cycle=develop
FROM lsstts/develop-env:${dev_cycle}

WORKDIR /usr/src/love
COPY . .

USER root
RUN chown -R saluser:saluser /usr/src/love
USER saluser

RUN source /home/saluser/.setup_dev.sh && \
	pip install -r requirements.txt && \
	pip install /usr/src/love

WORKDIR /home/saluser
CMD ["/usr/src/love/docker/start-daemon.sh"]
