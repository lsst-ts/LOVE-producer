FROM oboberg/opsim4_fbs_py3:latest

COPY --chown=opsim ./sal_libs /home/opsim/sal_libs

COPY --chown=opsim ./start.sh /home/opsim/start.sh
COPY --chown=opsim ./start-daemon.sh /home/opsim/start-daemon.sh


RUN cp /home/opsim/sal_libs/* dds/lib/

ENV PYTHONPATH "${PYTHONPATH}:/home/opsim/tsrepos/ts_salobj/python"
ENV LD_LIBRARY_PATH "/root/tsrepos/lib:/opt/rh/devtoolset-6/root/usr/lib64:/opt/rh/devtoolset-6/root/usr/lib:/opt/rh/devtoolset-6/root/usr/lib64:/opt/rh/devtoolset-6/root/usr/lib:${LD_LIBRARY_PATH}"
ENV WEBSOCKET_HOST "localhost:8000/ws/subscription"
ENV REDIS_HOST "127.0.0.1"
ENV AUTH_LDAP_SERVER_URI "ldap://45.79.13.50:389"
ENV PATH="/home/opsim/stack/python/miniconda3-4.5.4/bin:${PATH}"
ENV LSST_CONDA_ENV_NAME="${LSST_CONDA_ENV_NAME:-lsst-scipipe-fcd27eb}"

RUN mkdir -p /home/opsim/inria/producer

COPY --chown=opsim ./producer/requirements.txt /home/opsim/inria/producer/requirements.txt

WORKDIR /home/opsim/inria/producer

RUN pip install -r requirements.txt

# COPY --chown=opsim ./producer /home/opsim/inria/producer



ENTRYPOINT [ "/home/opsim/start-daemon.sh" ]
# ENTRYPOINT [ "bash" ]