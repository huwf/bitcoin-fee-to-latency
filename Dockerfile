#FROM python:3.5
FROM cdecker/bitcoin-dev
ADD . /bitcoin-fee-to-latency
WORKDIR /bitcoin-fee-to-latency
RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip3 install -r requirements.txt

ENV BTC_APP_HOME "/bitcoin-fee-to-latency"
ENV BTC_TIME "2017-12-04T12:00:00"

WORKDIR /
RUN git clone https://github.com/huwf/bitcoin
WORKDIR /bitcoin
RUN ./autogen.sh
RUN ./configure --disable-tests

RUN apt-get install libssl-dev
RUN apt-get install vim
RUN pip3 install -e git+https://github.com/petertodd/python-bitcoinlib


CMD git pull && /bin/bash