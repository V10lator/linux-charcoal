FROM archlinux:base-devel

RUN mkdir /docker
ADD docker /docker/
RUN docker/setup.sh
WORKDIR /project
