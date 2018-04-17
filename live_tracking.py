#! /usr/bin/python3

import bitcoin.rpc
from datetime import datetime
from pymongo import MongoClient

db = MongoClient('mongodb://mongo').bitcoin

node = bitcoin.rpc.Proxy()
current_mempool = []


import time
starttime=time.time()


if __name__ == '__main__':
    mempool = node.getrawmempool(True)
    new_mempool = []
    for id, m in mempool:
        if id not in current_mempool:
            m['db_insert_time'] = datetime.now()
            tx = db.mempool.insert(m)
            print('Added txid with hash %s to mempool database with _id: %s' % (str(id), str(tx)))
            new_mempool.append(tx)
            current_mempool = new_mempool





