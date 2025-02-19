FROM debian:stable-slim

ENV DOCKER_CONTAINER TRUE

RUN useradd -ms /bin/bash pi
RUN useradd -ms /bin/bash looperget

COPY ./looperget/scripts/upgrade_commands.sh /home/looperget/looperget/scripts/upgrade_commands.sh

RUN /home/looperget/looperget/scripts/upgrade_commands.sh docker-create-files-directories-symlinks
RUN /home/looperget/looperget/scripts/upgrade_commands.sh update-apt
RUN /home/looperget/looperget/scripts/upgrade_commands.sh update-packages
RUN /home/looperget/looperget/scripts/upgrade_commands.sh ssl-certs-generate
RUN /home/looperget/looperget/scripts/upgrade_commands.sh install-docker

COPY ./install/requirements.txt /home/looperget/install

RUN /home/looperget/looperget/scripts/upgrade_commands.sh docker-update-pip
RUN /home/looperget/looperget/scripts/upgrade_commands.sh docker-update-pip-packages

COPY . /home/looperget
WORKDIR /home/looperget/looperget

RUN /home/looperget/looperget/scripts/upgrade_commands.sh docker-compile-translations
RUN /home/looperget/looperget/scripts/upgrade_commands.sh compile-looperget-wrapper
