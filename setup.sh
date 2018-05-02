#!/usr/bin/env bash

#if [ "$(whoami)" != "root" ]; then
#    echo "You do not have the privileges to run this script.  Run as root, or with sudo"
#    exit 1
#fi

SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# This is where the blockchain will be stored once it's fully downloaded
mkdir -p ${SCRIPT_PATH}/blockchain/0.14
mkdir -p ${SCRIPT_PATH}/blockchain/0.15

#cp -R ${SCRIPT_PATH}/config experiment/.bitcoin
#docker build -t huwf/experiment ${SCRIPT_PATH}/experiment

echo "Specify root directory (absolute path) for the blockchain to be stored. Default: ${SCRIPT_PATH}/blockchain"
read ROOT_PATH

if [[ ${ROOT_PATH} == "" ]]
then
    ROOT_PATH="${SCRIPT_PATH}/blockchain"
    echo "ROOT_PATH = ${ROOT_PATH}"
fi

echo "Setting up data directory"
export ROOT_PATH=${ROOT_PATH}
#mkdir -p ${ROOT_PATH}/0.14
mkdir -p ${ROOT_PATH}/0.15

cp bitcoin.conf ${SCRIPT_PATH}/blockchain/0.14/bitcoin.conf
cp bitcoin.conf ${ROOT_PATH}/0.15/bitcoin.conf

docker run -dt --name=bitcoin_0.14 -v -p 8333:8332 -p 18333:18332 ${SCRIPT_PATH}/0.14/:/home/bitcoin/.bitcoin ruimarinho/bitcoin-core:0.14-alpine -prune=4096
docker run -dt --name=bitcoin_0.15 -v -p 8332:8332 -p 18332:18333 ${ROOT_PATH}/0.15/:/home/bitcoin/.bitcoin ruimarinho/bitcoin-core:0.15-alpine
