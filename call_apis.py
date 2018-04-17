#! /usr/bin/python3

import time
import datetime
import requests
from pymongo import MongoClient
import bitcoin

db = MongoClient('mongodb://mongo').bitcoin

import logging
log = logging.getLogger('__name__')
log.setLevel(logging.DEBUG)


def insert_to_database(js, api):
    try:
        db.apis.insert(js)
        log.info('Successfully inserted %s into database' % api)
    except:
        log.exception('Error inserting %s into database' % (str(js)))


def call_api(url, api):
    try:
        js = requests.get(url).json()
        js['service'] = api
        log.info('Successfully called %s at ' % api)
        return js
    except:
        log.exception('Error calling %s at %s' % (url))


def call_bitcoinfees_recommended():
    url = 'https://bitcoinfees.earn.com/api/v1/fees/recommended'
    call_api(url, 'bitcoinfees_recommended')


def call_bitcoinfees_summary():
    url = ''
    call_api(url, 'bitcoinfees_summary')


def call_rpc():
    try:
        import bitcoin.rpc
        bitcoin.SelectParams('testnet')
        node = bitcoin.rpc.Proxy()
        for i in range(1, 26):
            js = node.estimatesmartfee(i)
            js['time'] = datetime.datetime.now()
            insert_to_database(js, 'estimatesmartfee %d' % i)
    except:
        log.exception('Failed calling Bitcoin RPC')


def call_apis():
    try:
        insert_to_database(call_bitcoinfees_recommended())
        insert_to_database(call_bitcoinfees_summary())
        call_rpc()
    except:
        log.exception('Error with call_apis. This really should be handled somewhere else...')

if __name__ == '__main__':
    start_time = time.time()
    print('Start time: %f' % start_time)
    delay = 600

    call_rpc()
    # while True:
      # time.sleep(delay - ((time.time() - start_time) % delay))
      # print('time: %f' % time.time())
