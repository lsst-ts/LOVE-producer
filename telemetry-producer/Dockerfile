FROM oboberg/opsim4_fbs_py3:latest

COPY --chown=opsim ./sal_libs /home/opsim/sal_libs

COPY --chown=opsim ./start.sh /home/opsim/start.sh
COPY --chown=opsim ./start-daemon.sh /home/opsim/start-daemon.sh

COPY --chown=opsim ./producer /home/opsim/inria/producer

RUN cp /home/opsim/sal_libs/* dds/lib/

WORKDIR /home/opsim/inria/producer

CMD [ "/home/opsim/start-daemon.sh" ]