# Bitcoin Fee to latency

Scripts for our paper.

Should have MongoDB running on localhost.  I'm running 3.4 on docker.  From the root directory:

    docker run -dt -p 27017:27017 -v $(pwd):/db:/data/db
    
This uses the blocktrail API, in order to get the information from their mempool.  You will need to add account credentials in the `bitcoin-fee-to-latency/credentials` in the format `API_KEY|API_SECRET`, or add `API_KEY` and `API_SECRET` as environment variables.

Install dependencies with `pip` (from root):

    pip install --no-cache-dir -r requirements.txt

To set up, you will need to first download all the blocks, from that, we iterate through each block and transaction.  You can do this with 

    bin/setup
    
To download the transactions for a relevant period, run

    bin/download_transactions --start YYYY-MM-DDTHH:MM:SS --end YYYY-MM-DDTHH:MM:SS 
    
Sorry about the date format.  `--end` is optional, will default to `datetime.now()`.  To carry on where you finished before, use `--recovery` instead of start, which will set the start to the last stored transaction.

The amount of transactions in the mempool at any time can be obtained through

    bin/reconstruct_mempool YYYY-MM-DDTHH:MM:SS

This will `find()` all transactions whose `first_seen` date is before the argument, and whose `block_time` is after the argument.  It outputs the `count()` of the cursor, but obviously stores the data as a list of dicts. 
    
## Known limitations 

* Does not work properly in Docker, since Mongo appears to refuse connections by default
* On my computer I cannot get pip to run on the correct version of Python to run from terminal
* API rate limit is 300 per minute