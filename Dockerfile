FROM lsstts/develop-env:salobj4_b30

WORKDIR /usr/src/love
COPY producer/requirements.txt .
RUN source /opt/lsst/software/stack/loadLSST.bash && pip install -r requirements.txt

COPY producer .
WORKDIR /home/saluser
CMD ["/usr/src/love/start-daemon.sh"]
