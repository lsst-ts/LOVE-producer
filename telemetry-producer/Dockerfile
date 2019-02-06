FROM oboberg/opsim4_fbs_py3:latest

COPY --chown=opsim ./sal_libs /home/opsim/sal_libs

COPY --chown=opsim ./start.sh /home/opsim/start.sh
COPY --chown=opsim ./start-daemon.sh /home/opsim/start-daemon.sh

COPY --chown=opsim ./producer /home/opsim/inria/producer

RUN cp /home/opsim/sal_libs/* dds/lib/

WORKDIR /home/opsim/inria/producer

ENV PYTHONPATH "${PYTHONPATH}:/home/opsim/tsrepos/ts_salobj/python"
ENV LD_LIBRARY_PATH "/root/tsrepos/lib:/opt/rh/devtoolset-6/root/usr/lib64:/opt/rh/devtoolset-6/root/usr/lib:/opt/rh/devtoolset-6/root/usr/lib64:/opt/rh/devtoolset-6/root/usr/lib:${LD_LIBRARY_PATH}"
ENV WEBSOCKET_HOST "localhost:8000/manager/ws/subscription"

ENTRYPOINT [ "/home/opsim/start-daemon.sh" ]
