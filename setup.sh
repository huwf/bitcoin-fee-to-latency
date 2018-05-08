#!/usr/bin/env bash

if [ "$(whoami)" != "root" ]; then
    echo "You do not have the privileges to run this script.  Run as root, or with sudo"
    exit 1
fi



# How to parse bash flags:
# https://stackoverflow.com/questions/7069682/how-to-get-arguments-with-flags-in-bash-script
prune=4096
testnet='-testnet'
mongodb="mongodb://mongodb"
move=0
# Delay is the delay from collecting the mempool to calling APIs
delay=3600.0

#while [ ! $# -eq 0 ]
#do
#    shift
#    case "$1" in
#
#        -testnet)
#        testnet="-testnet"
#        shift
#            ;;
#    esac
#done

export PRUNE=${prune}
export TESTNET=${testnet}
export MONGO_DB=${mongodb}

while getopts 'p:d:' flag; do
    echo "Hello? ${flag}"
    case "${flag}" in
        -p)
            prune="${OPTARG}"
            ;;
        d) delay="${OPTARG}"
        ;;
    esac
done

echo "Prune: $prune"
echo "Delay: $delay"


SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# This is where the blockchain will be stored once it's fully downloaded
mkdir -p ${SCRIPT_PATH}/blockchain/0.14
mkdir -p ${SCRIPT_PATH}/blockchain/0.15


echo "Specify root directory (ROOT_PATH) (absolute path) for the blockchain to be stored. Default: ${SCRIPT_PATH}/blockchain"
echo "This should probably be a volume rather than a local directory, unless you have a really big disk"
echo "If you want to move the data away from the volume (to save money) after pruning, then you will need to set a ROOT_PATH which is different to ${SCRIPT_PATH}/blockchain"
read ROOT_PATH

if [[ ${ROOT_PATH} == "" ]]
then
    ROOT_PATH="${SCRIPT_PATH}/blockchain"
fi

echo "ROOT_PATH = ${ROOT_PATH}"

if [[ ${ROOT_PATH} != "${SCRIPT_PATH}/blockchain" ]]; then
    ${move}=1
    echo "ROOT_PATH is different to SCRIPT_PATH/blockchain. Setting move=1"
fi


echo "Setting up data directory"
export PRUNE=${prune}
export ROOT_PATH=${ROOT_PATH}
export TESTNET=${testnet}
mkdir -p ${ROOT_PATH}/0.14
mkdir -p ${ROOT_PATH}/0.15

cp bitcoin.conf ${ROOT_PATH}/0.14/bitcoin.conf
cp bitcoin.conf ${ROOT_PATH}/0.15/bitcoin.conf
# Hack for the experiment container
# Needs to have two separate config filess to allow connection to the two different bitcoind instances
cp bitcoin.conf ${SCRIPT_PATH}/bitcoin.conf.014
if [[ ${testnet} != '' ]]; then
    $rpcport=18332
fi
echo "rpcconnect=bitcoin_014
rpcport=${rpcport}" >> bitcoin.conf ${SCRIPT_PATH}/bitcoin.conf.014
cp bitcoin.conf ${SCRIPT_PATH}/bitcoin.conf.015

if [[ ${testnet} != '' ]]; then
    $rpcport=18332
fi
echo "rpcconnect=bitcoin_015
rpcport=${rpcport}" >> bitcoin.conf ${SCRIPT_PATH}/bitcoin.conf.015

# This downloads two instances of the blockchain, one for 0.14 and one for 0.15.
# We will want to use txindex for 0.15 to call getrawtransaction so can't prune
# 0.14 we don't need to worry about this, so can save space
# Internal ports should work as usual without config, but externally map to other ports
# Since the ports are exposed with EXPOSE in the Dockerfile, docker exec also shouldn't need config

docker run -dt --name=bitcoin_014 -p 8432:8332 -p 8433:8333 -p 18432:18332 -p 18433:18333 -v ${SCRIPT_PATH}/0.14/:/home/bitcoin/.bitcoin ruimarinho/bitcoin-core:0.14 \
bitcoind ${testnet} -prune=${prune} -printtoconsole -debug

# Bitcoin 0.15 is running on the standard ports,so by default RPC queries should go here
docker run -dt --name=bitcoin_015 -p 8333:8333 -p 8332:8332 -p 18333:18333 -p 18332:18332 -v ${ROOT_PATH}/0.15/:/home/bitcoin/.bitcoin ruimarinho/bitcoin-core:0.15 \
bitcoind ${testnet} -debug -printtoconsole

# Check for when they are properly synced
echo "Waiting for the two instances of Bitcoin to be synced, will check every 5 minutes"
echo "Will check the blockexplorer API getblockcount and compare with local results from bitcoin-cli"
echo "Once this has completed, will stop the two containers, and start up docker-compose.yml"
echo "testnet: ${testnet}"
sleep_time=30.0



url="https://blockchain.info/q/getblockcount"
while true ; do
    if [ ${testnet} == "-testnet" ]; then
        url="https://testnet.blockchain.info/q/getblockcount"
    fi
    # If blockchain.info is down, try this
#    explorer=$(wget -q -O- ${url} | python3 -c "import json; import sys; print(json.load(sys.stdin)['blockcount'])")
    explorer=$(wget -q -O- ${url})
    explorer=${explorer//[ $'\001'-$'\037'[:space:]]/}
    block_count_014=$(docker exec -it -u bitcoin bitcoin_014 bitcoin-cli ${testnet} getblockcount)
    block_count_014=${block_count_014//[ $'\001'-$'\037'[:space:]]/}
    block_count_015=$(docker exec -it -u bitcoin bitcoin_015 bitcoin-cli ${testnet} getblockcount)
    block_count_015=${block_count_015//[ $'\001'-$'\037'[:space:]]/}

    echo "API: ${explorer}"
    echo "block_count_014: ${block_count_014}"
    echo "block_count_014: ${block_count_014}" | od -c
    echo "block_count_015: ${block_count_015}"

    echo "Block Explorer: $explorer Bitcoin 0.14: $block_count_014 Bitcoin 0.15: $block_count_015"

    if (( "${block_count_015}" >= "${explorer}" )) && (( "${block_count_014}" >= "${explorer}" )); then
        echo "About to run run_compose.sh"
        ${SCRIPT_PATH}/run_compose.sh
        exit 0
    fi
    echo "About to sleep for ${sleep_time} seconds"
    sleep $sleep_time
done
