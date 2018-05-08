# Bitcoin Fee to latency

Scripts for our paper.

## Setting up Bitcoin nodes

The Bitcoin nodes are Docker containers, which can be run at the same time.  Running `. setup.sh` (note leading `.`) will run these two images and mount the data to the host.  Once they have finished downloading the blockchain, then the two will stop, and the application will be started with Docker Compose.

You do not need to use the `setup.sh` file, but if you don't you will need to set up some environment variables manually which are in the docker-compose file.  These are:

* `SCRIPT_PATH`: This can be `$(pwd)` from the git directory
* `TESTNET`: This should either be empty, or `-testnet` as it is used to decide whether to run mainnet or testnet.  If it runs testnet then the ports used will be 18332 rather than 8332.
* `MONGO_DB`: Will probably be `mongodb://mongodb`, but you can specify.  Docker Compose gives local DNS to containers on the same network, with the container name as the domain.  If you wish to use it somewhere else you can do that, but remember Docker Compose uses a different network.
* `PRUNE`: Not implemented, but this will set the size to prune 0.14 to.  Defaults to 4096.  

### Feesim (not fully implemented)
There is a container to be built in `feesim/` contained within docker-compose, but this is not working properly yet.  Running it on its own as 

    docker build -t huwf/feesim feesim/
    docker run -dt -p 8350:8350  huwf/feesim
    
will start it as a service through which you can run `feesim estimatefee 1`.  So far, it only works locally, so will have to use `docker exec -it $container_name feesim estimatefee 1`.  Full documentation on feesim is at: https://github.com/bitcoinfees/feesim

Notes about Feesim:
* It will crash if it tries to run and can't access a Bitcoin node
* The config file is hardcoded to the testnet port (18332)
* On bitcoin >= 0.16 it will require further development, which is why I use 0.15.  This is because it uses `getinfo` to check the status of Bitcoin, which is removed in 0.16.  Changing the source itself seems to be only a single line of code, but many references are hardcoded to the `github.com/bitcoinfees/feesim` library, and I don't know Go well enough to get it to work.



## Experiment

There are two main scripts for the experiment:

* `experiment/live_tracking.py` - Saves the mempool entries into the Mongo database
* `experiment/call_apis.py` - Calls different APIs for the experiment, and stores them in the database

These assume that they are running within `docker-compose`.  The `live_tracking` one should run first, as this will check to see that both Bitcoin 0.14 and Bitcoin 0.15 are up.  

The two files `bitcoin.conf.014` and `bitcoin.conf.015` are in the main directory, are mounted to `/root/.bitcoin/` in docker-compose.  Since we're changing the `rpcconnect` to the different container, the Python Bitcoin library does not parse the username and password automatically, so we need to have two separate config files.  By default, it will connect to `0.15`, the `btc_config_path` arg for `0.14` is specified and seems to connect okay to that.

### Analysis



## Reconstructing Mempool and Blockchain

If we wish to perform this analysis on a different period of time, then I have tried to create a script which will set the blockchain back to within a certain period.  I suggest at first, simply cutting off earlier, but later look at how we could use prune to reduce the size further to only include the specific period.

There is some code I've tried in `bitcoin-fee-to-latency/python-bitcoin-blockchain-parser/blockchain_parser/blockchain.py` where I added `def fake_blockchain`, and an implementation in `__main__`, but it is not finished or properly documented.

This is a work in progress, but the essential process is as follows:
* Use an API to download transactions between the target times.  This needs to be done by an API rather than RPC call, since that will show the time it entered the mempool.  I previously used blocktrail, but that API is obsolete since they were bought by btc.com.
* Extract the information from the blockchain database and parse the block information
* Create a new database directory (outside of Bitcoin `datadir`)to store the files in (BTC uses leveldb)
* Use your choice of logic (for new transactions) to decide whether or not to make a copy, and write to the new database
* Set up a new instance of Bitcoin specifying `datadir=$the_dir_you_stored_blockchain_in`

