FROM lsstts/develop-env:latest
WORKDIR /home/saluser/repos/ts_sal
RUN source /opt/lsst/software/stack/loadLSST.bash && setup lsst_distrib && \
    source /home/saluser/repos/ts_sal/setup.env && \
    eups declare -r . ts_sal -t current && \
    setup ts_sal -t current && \
    scons && \
    make_salpy_libs.py ATDome ATMCS

WORKDIR /usr/src/love
COPY producer/requirements.txt .
RUN source /opt/lsst/software/stack/loadLSST.bash && pip install -r requirements.txt

COPY producer .
RUN find . | grep -E "(_pycache_|\.pyc|\.pyo$)" | xargs rm -rf

WORKDIR /home/saluser
ENTRYPOINT ["/usr/src/love/start-daemon.sh"]
