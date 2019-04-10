FROM lsst/queue:latest

WORKDIR /usr/src/love
COPY producer/requirements.txt .
RUN source /opt/lsst/software/stack/loadLSST.bash && pip install -r requirements.txt

COPY producer .
RUN find . | grep -E "(_pycache_|\.pyc|\.pyo$)" | xargs rm -rf

WORKDIR /home/saluser
ENTRYPOINT ["/usr/src/love/start-daemon.sh"]
