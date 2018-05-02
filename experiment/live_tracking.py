#! /usr/bin/python3

import bitcoin.rpc
from datetime import datetime
from pymongo import MongoClient
import logging
import os
logging.basicConfig(
        level=os.environ.get('logging', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('__main__')
#import logging
#log = logging.getLogger('__name__')
#log.setLevel(logging.DEBUG)


db = MongoClient('mongodb://127.0.0.1').bitcoin

node = bitcoin.rpc.Proxy()
current_mempool = []
delay = 60 # Not currently used

import time
starttime=time.time()

if __name__ == '__main__':
    while True:
        mempool = node.getrawmempool(True)
        block_height = node.getblockheader(node.getbestblockhash(), True)['height']
        new_mempool = []
        for id, m in mempool.items():
            if id not in current_mempool:
                m['block_height'] = block_height
                m['tx_id'] = id
                m['db_insert_time'] = datetime.now()
                m['fee'] = str(m['fee'])
                m['modifiedfee'] = str(m['modifiedfee'])
#               print(m)
                tx = db.mempool.insert(m)
#            print('Added txid with hash %s to mempool database with _id: %s' % (str(id), str(tx)))
            new_mempool.append(id)
        current_mempool = new_mempool
        if len(current_mempool) % 100  == 0:
            log.info('Size of current mempool: %d' % len(current_mempool))
#        print('About to sleep for 10 seconds')
#        time.sleep(10)
#    time.sleep(delay - ((time.time() - start_time) % delay))




