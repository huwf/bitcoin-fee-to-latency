#!/usr/bin/env bash

echo "Executing run_compose.sh"
delay=3600
while getopts 'd:' flag; do
    case "${flag}" in
        d) delay="${OPTARG}" ;;
        e) end="${OPTARG}" ;;
    esac
done

# Use this if you want to prune the blockchain for 0.15 on the external volume
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#docker exec -ti bitcoin_0.15 bitcoin-cli -prune=4096


docker stop bitcoin_0.15 && docker rm bitcoin_0.15
docker stop bitcoin_0.14 && docker rm bitcoin_0.14

#export ROOT_PATH=${SCRIPT_PATH}/blockchain

docker-compose up -d

sleep ${delay}
echo "About to run call_apis.py..."
docker exec -dt experiment ./call_apis.py
