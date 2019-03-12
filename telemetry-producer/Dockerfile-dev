FROM lsst/queue:latest

ENV WEBSOCKET_HOST "localhost:8000/ws/subscription"
ENV REDIS_HOST "127.0.0.1"
ENV AUTH_LDAP_SERVER_URI "ldap://45.79.13.50:389"

WORKDIR /usr/src/love
COPY producer/requirements.txt .
RUN source /opt/lsst/software/stack/loadLSST.bash && pip install -r requirements.txt
RUN find . | grep -E "(_pycache_|\.pyc|\.pyo$)" | xargs rm -rf

COPY start-daemon.sh .
COPY producer .

WORKDIR /home/saluser
ENTRYPOINT ["/usr/src/love/start-daemon.sh"]
