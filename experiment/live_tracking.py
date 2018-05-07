#! /usr/bin/env python

import time
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

db_url = os.environ.get('MONGO_DB', 'mongodb://mongodb')
print('db_url: %s' % db_url)

client = MongoClient('mongodb://mongodb', serverSelectionTimeoutMS=5)
db = client.bitcoin

node = bitcoin.rpc.Proxy('bitcoin_0.15')
if os.environ.get('TESTNET'):
    bitcoin.SelectParams('testnet')

current_mempool = []
delay = 60 # Not currently used


def check_services_are_up(testnet=False):
    """
    We need to check that Bitcoin 0.14, 0.15 and Mongo are all up and ready
    This will stay in an infinite loop until we have successfully connected to all three
    :return: 
    """

    port_014 = 18432 if testnet else 8432
    port_015 = 18332 if testnet else 8332
    node_014 = bitcoin.rpc.Proxy(service_port=port_014)
    node_015 = bitcoin.rpc.Proxy(service_port=port_015)
    while True:
        try:
            time.sleep(5)
            client.server_info()
            # We don't need Bitcoin 0.14
            # node_014.getinfo()
            node_015.getinfo()

            return True
        except Exception as err:
            print(err)


if __name__ == '__main__':
    # Check all services are up:
    check_services_are_up()
    print('Services are up')
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
        if len(current_mempool) % 100 == 0:
            log.info('Size of current mempool: %d' % len(current_mempool))






