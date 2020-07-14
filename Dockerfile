FROM lsstts/develop-env:b101

WORKDIR /usr/src/love
COPY producer/requirements.txt .
RUN source /opt/lsst/software/stack/loadLSST.bash && pip install -r requirements.txt
RUN source /opt/lsst/software/stack/loadLSST.bash \
    && source /home/saluser/repos/ts_sal/setup.env \
    && setup ts_sal -t current \
    && /home/saluser/repos/ts_sal/bin/make_idl_files.py Watcher \
    && /home/saluser/repos/ts_sal/bin/make_idl_files.py Environment

COPY producer ./producer
WORKDIR /home/saluser
CMD ["/usr/src/love/producer/start-daemon.sh"]
