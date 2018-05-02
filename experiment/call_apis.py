#! /usr/bin/python3
from subprocess import Popen, PIPE
import time
import datetime
import requests
from pymongo import MongoClient
import json
# import bitcoin
import os
db = MongoClient('mongodb://127.0.0.1').bitcoin

import logging

logging.basicConfig(
        level=os.environ.get('logging', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('__main__')


def insert_to_database(js, api):
    js['api'] = api
    try:
        db.apis.insert(js)
        log.info('Successfully inserted %s into database' % api)
    except:
        log.exception('Error inserting %s into database' % (str(js)))


def call_api(url, api):
    try:
        print('api:', api)
        js = requests.get(url).json()
        # js['service'] = api
        log.info('Successfully called %s at ' % api)
        return js
    except:
        log.exception('Error calling %s at %s' % (url))


def call_bitcoinfees_recommended():
    url = 'https://bitcoinfees.earn.com/api/v1/fees/recommended'
    return call_api(url, 'bitcoinfees_recommended')


def call_bitcoinfees_summary():
    url = 'https://bitcoinfees.earn.com/api/v1/fees/list'
    return call_api(url, 'bitcoinfees_summary')


def call_bitgo_api():
    try:
        current_time = datetime.datetime.now()
        url = 'https://www.bitgo.com/api/v1/tx/fee?numBlocks='
        js_obj = {'time': current_time}
        js_list = []
        js = call_api('%s%s' % (url, '2'), 'bitgo') #requests.get().json()
        keys = js['feeByBlockTarget'].keys()
        del js['feeByBlockTarget']
        js_list.append(js)
        for i in keys:
            if int(i) <= 1:
                continue
            js = call_api('%s%s' % (url, i), 'bitgo')
            # js = requests.get('%s%s' % (url, i)).json()
            try:
                del js['feeByBlockTarget']
            except:
                log.exception('error deleting feeByBlockTarget')
            js_list.append(js)
            time.sleep(2)

        js_obj['data'] = js_list
        return js_obj
    except:
        log.exception('Error calling Bitgo API')


def _estimate_smart_fee(i, mode='CONSERVATIVE', rpc_command='estimatesmartfee'):
#    if not rpc_command in ['estimatesmartfee', 'estimatefee']:
#        raise Exception('Can only use this function for estimatefee and estimatesmartfee')
#    if rpc_command != 'estimatesmartfee':
#        mode = ''
    p = Popen(['bitcoin-cli', 'estimatesmartfee', '%d' % i, mode], stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    output = output.decode('ascii')
    # print(output, err.decode('ascii'))
    js = json.loads(output)
    js['time'] = datetime.datetime.now()
    js['mode'] = mode.lower()
    return js
#    insert_to_database(js, 'estimatesmartfee %d' % i)


def _estimate_fee(i):
#    if rpc_command != 'estimatesmartfee':
#        mode = ''
    p = Popen(['bitcoin-cli', 'estimatefee', '%d' % i], stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    output = output.decode('ascii')
    # print(output, err.decode('ascii'))
    js = {'feerate': output, 'blocks': i}
#    js = json.loads(output)
    js['time'] = datetime.datetime.now()
#    js['api'] = 'estimatefee'
    js['mode'] = 'estimatefee'
    return js
#    insert_to_database(js, 'estimatesmartfee %d' % i)


def call_rpc():
    try:
        # TODO: Use python-bitcoinlib when they support estimatesmartfee
        # Or,
        # We don't need to check all the way up to 1008
        # Do the first 25 (excluding 1), after which it should tail off (1 causes error)
        # The range for estimatefee is 2 - 25 according to the documentation
        # Then double each time to catch the higher latency transactions
        # js_obj = {}
        js_list = []
        for i in range(2, 26):
            js_list.append(_estimate_smart_fee(i))
            js_list.append(_estimate_smart_fee(i, 'ECONOMICAL'))
            js_list.append(_estimate_fee(i))
        for i in [40, 80, 160, 320, 640, 1008]:
            js_list.append(_estimate_smart_fee(i))
            js_list.append(_estimate_smart_fee(i, 'ECONOMICAL'))
    except:
        log.exception('Failed calling Bitcoin RPC')
    return {'data': js_list}


def call_apis():
    try:
        insert_to_database(call_rpc(), 'rpc_call')
        insert_to_database(call_bitcoinfees_recommended(), 'bitcoinfees_recommended')
        summary = call_bitcoinfees_summary()
        summary['time'] = datetime.datetime.now()
        insert_to_database(summary, 'bitcoinfees_summary')
        insert_to_database(call_bitgo_api(), 'bitgo')
    except:
        log.exception('Error with call_apis. This really should be handled somewhere else...')

if __name__ == '__main__':
    start_time = time.time()
    print('Start time: %f' % start_time)
    delay = 600
    now = datetime.datetime.now()
    # HACK: want it to start on the hour
#   while datetime.datetime.now().minute > 0:
#        time.sleep(1)
    log.info('Application starting: %d:%d' % (datetime.datetime.now().hour, datetime.datetime.now().minute))
    while True:
#        now = datetime.datetime.now()
        log.info('Calling the local RPC and calling APIs:')
        call_apis()
        time.sleep(delay - ((time.time() - start_time) % delay))

