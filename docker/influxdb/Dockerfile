FROM influxdb:1.8.10

ENV DOCKER_CONTAINER TRUE

RUN mkdir -pv /var/influxdb/data

COPY ./docker/influxdb/run.sh /home/looperget/docker/influxdb/run.sh
RUN chmod +x /home/looperget/docker/influxdb/run.sh

ENV PRE_CREATE_DB looperget_db
ENV ADMIN_USER looperget
ENV PASS mmdu77sj3nIoiajjs

EXPOSE 8086

CMD /home/looperget/docker/influxdb/run.sh
