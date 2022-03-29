FROM ubuntu:20.04 AS planner

# Dependencies
RUN apt-get update
RUN apt-get dist-upgrade -y

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    libboost-all-dev \
    pkg-config \
    python3 \
    wget \
    zlib1g-dev

# OSI
ENV OSI_VERSION Osi-0.103.0
ENV DOWNWARD_COIN_ROOT /opt/osi
RUN wget http://www.coin-or.org/download/source/Osi/$OSI_VERSION.tgz
RUN tar xvzf $OSI_VERSION.tgz
WORKDIR /$OSI_VERSION
RUN mkdir $DOWNWARD_COIN_ROOT
RUN ./configure -C --without-lapack --enable-static=no --prefix="$DOWNWARD_COIN_ROOT" --disable-bzlib
RUN make
RUN make test
RUN make install
WORKDIR /
RUN rm -rf $OSI_VERSION
RUN rm $OSI_VERSION.tgz

# Planner and VAL
ADD . /planner

# VAL
WORKDIR /planner/VAL
RUN cmake .
RUN make clean
RUN make
RUN cp ./bin/Validate /bin/validate

# Planner
WORKDIR /planner
RUN rm -rf ./builds
RUN python3 ./build.py
ENV PYTHONHASHSEED 0
