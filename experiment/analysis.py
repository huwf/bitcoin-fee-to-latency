import time
from pymongo import MongoClient
import bitcoin.rpc
from bs4 import BeautifulSoup
import requests
import json
import logging
from decimal import Decimal
import csv
logging.basicConfig(
        level='INFO',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('__main__')


bitcoin.SelectParams('testnet')
node = bitcoin.rpc.Proxy()
db = MongoClient().bitcoin

SATOSHIS_PER_BTC = 100000000


def btc_kb_sat_b(n):
    return n * SATOSHIS_PER_BTC / 1024


def get_min_block_height():
    cursor = db.mempool.aggregate(
        [
            {
                "$group": {"_id": None, "minBlock": { "$min": "$block_height"} }
            }
        ]
    )
    return next(cursor)['minBlock']


def get_tx_by_id(txid):
    return db.mempool.find_one({'tx_id': txid})


def get_transactions(transactions):
    query = {
        'tx_id': {'$in': transactions}
    }
    return db.mempool.find(query)


def get_block(height):

    try:
        node.getblock(node.getblockhash(height))
    except:
        # For testing, or if something really goes wrong, we can use chainquery.com

        base_url = 'http://chainquery.com/bitcoin-api/'
        block_hash_url = '%sgetblockhash/%d' % (base_url, height)
        html = requests.get(block_hash_url).text
        soup = BeautifulSoup(html, 'lxml')

        block_hash = json.loads(soup.find('pre').text)

        block_info_url = '%sgetblock/%s/true' % (base_url, block_hash['result'])
        html = requests.get(block_info_url).text
        soup = BeautifulSoup(html, 'lxml')
        return json.loads(soup.find('pre').text)['result']


def get_inserted_block_for_all_transactions(min=get_min_block_height()):
    """
    This starts from the min block height, and goes through all blocks, until 
    there are no more left
    :return: 
    """
    i = min
    while True:
        block = get_block(i)
        log.info('Processing block with hash: %s' % block['hash'])
        transactions = list(get_transactions(block['tx']))
        log.info('%d transactions found' % len(transactions))
        for tran in transactions:
            # tran = get_tx_by_id(txid)
            if tran:
                tran['blockchain_block_height'] = block['height']
                tran['mempool_block_height'] = tran['height']
                tran['latency'] = tran['blockchain_block_height'] - tran['mempool_block_height']
                # This was a mistake, so let's delete it
                db.mempool.update({'_id': tran['_id']}, tran)
                del tran['block_height']
                log.debug('tran: ', tran)
                # break
        if len(transactions) > 0:
            db.processed_mempool.insert_many(transactions)
        i += 1


# def set_fee_size_ratio(transactions, update_db=True):
#     """
#     With the given list transactions, this will return the size/fee
#     It will also update in the database if flag selected
#     :param transactions: A list of mempool Tx objects
#     :return: Updated list of mempool Tx objects, with additional field
#     """
#     for m in transactions:
#         m['fee_size_ratio_satoshi'] = Decimal(m['fee']) * SATOSHIS_PER_BTC / m['size']
#         updated = db.processed_mempool.update({'_id': m['_id']}, m)
#         return updated

def get_time_bucket_start_points():
    """
    What I should do is:
    1. Get a list of api calls which are rpc_call
    2. Get all api calls within 2 minutes of this
    3. Process them all
    
    This function gets all the dates from rpc_call (was called first)
    :param api: 
    :return: A MongoDB cursor
    """
    sort = {}
    # if api == 'rpc_call':
    #     sort =  {'data.0.time': 1}
    # elif api == 'bitgo':
    #     sort = {'time': 1}
    return db.apis.aggregate([
        {
            '$match': {'api': 'rpc_call', 'data.0.time': {'$gte': datetime.datetime(2018, 4, 24, 10, 24, 11, 300000)}}
        },
        {
            '$sort': {'data.0.time': 1}
        }
    ])


def get_api_calls_in_interval(api_time):
    """
    We have found an instance of rpc_call, and want to get this and all other
    api calls within 2 minutes of this.
    :param api_time: A DateTime object, of when the first RPC call was done 
    :return: A Mongodb cursor, with all API calls within two minutes of this
    """
    plus_two = api_time + datetime.timedelta(minutes=2)

    return db.apis.find({
        '$or': [
            # RPC
            {'$and':
                [
                    {'data.0.time': {'$gte': api_time}},
                    {'data.0.time': {'$lt': plus_two}}
                ]
            },
            # Bitgo
            {'$and':
                [
                    {'time': {'$gte': api_time}},
                    {'time': {'$lt': plus_two}}
                ]
            }
        ]
    })


def loop_mempool_entries(cursor):
    '''
    The cursor is a list of the start points
    
    :param cursor: 
    :return: 
    '''
    first = next(cursor)
    for c in cursor:
        last = c
        first_date = first['data'][0]['time']
        log.info('Processing mempool transactions for %r' % first_date)
        last_date = last['data'][0]['time']
        # mempool_entries is a list of tx
        mempool_entries = get_mempool_entries(first_date, last_date)

        with open('data/%s.csv' % datetime.datetime.strftime(first_date, '%Y-%m-%dT%H:%M:%S'), 'w') as f:
            writer = csv.writer(f)
            # NOTE: The fee and ratio are converted to Satoshis
            writer.writerow(
                ['txid', 'size', 'fee', 'ratio', 'actual_blocks', 'conservative_estimate', 'economical_estimate',
                 'estimatefee', 'bitgo', 'bitgo_confidence', 'bitcoinfees_min', 'bitcoinfees_max', 'bitcoinfees_confidence'])
            for m in mempool_entries:
                for call in get_api_calls_in_interval(first_date):
                    api = call['api']
                    if api == 'bitgo':
                        m = _process_bitgo(call['data'], m)
                    elif api == 'rpc_call':
                        m = _process_rpc_call(call['data'], m)
                    elif api == 'bitcoinfees_summary':
                        m = _process_bitcoinfees(call['fees'], m)

                writer.writerow(
                    [
                        m['tx_id'], m['size'], m['fee'], m['ratio'], m['latency'], m['conservative_estimate'],
                        m['economical_estimate'], m['estimatefee'], m['bitgo'], m['bitgo_confidence'],
                        m['bitcoinfees_min'], m['bitcoinfees_max'], m['bitcoinfees_confidence']
                    ]
                )
                # loop_fee_estimates(mempool_entries, call)
        first = last


def _process_bitcoinfees(data, tx):
    '''
    This is easier, because it has a range already
    :param data: 
    :param tx: 
    :return: 
    '''
    ratio = tx['ratio']
    for d in data:
        if ratio >= d['minFee'] and ratio < d['maxFee']:
            tx['bitcoinfees_min'] = d['minDelay']
            tx['bitcoinfees_max'] = d['maxDelay']
            tx['bitcoinfees_confidence'] = 90
            return tx
    # Something wernt wrong
    tx['bitcoinfees_min'] = -1
    tx['bitcoinfees_max'] = -1
    tx['bitcoinfees_confidence'] = 0
    return tx


def _process_bitgo(data, tx):
    # This is probably how I should have done it for rpc_call as well
    # pass
    data = sorted(data, key=lambda x: x['numBlocks'])
    first = data[0]
    first['fee_per_byte'] = int(first['feePerKb'] / 1024)
    last = None
    for d in data[1:]:
        last = d
        d['fee_per_byte'] = d['feePerKb'] / 1024
        if tx['ratio'] >= first['fee_per_byte'] and tx['ratio'] < last['fee_per_byte']:
            tx['bitgo'] = last['numBlocks']
            tx['bitgo_confidence'] = last['confidence']
            return tx
    if tx['ratio'] > last['fee_per_byte']:
        tx['bitgo'] = 1
        tx['bitgo_confidence'] = 0
    else:
        # Something went wrong
        tx['bitgo'] = -1
        tx['bitgo_confidence'] = 0
    return tx


def _process_rpc_call(data, tx):
    """
    
    :param data: The data about the different feerates 
    :param mempool: The entries in the mempool at the specific time
    I.e., anything which entered the mempool when data represented the latest prediction
    :return: Updated version of the transaction including estimated details
    """
    # fees = []
    # fee_latency = {}
    data_ec, fees_ec = {}, []
    data_con, fees_con = {}, []
    data_ef, fees_ef = {}, []

    data_ec, fees_ec = get_rpc_fees_data_structures(fees_ec, data_ec, data, 'economical')
    data_con, fees_con = get_rpc_fees_data_structures(fees_con, data_con, data, 'conservative')
    data_ef, fees_ef = get_rpc_fees_data_structures(fees_ef, data_ef, data, 'estimatefee')

    tx = get_fee_estimate(fees_con, data_con, tx, 'conservative_estimate')
    tx = get_fee_estimate(fees_ec, data_ec, tx, 'economical_estimate')
    tx = get_fee_estimate(fees_ef, data_ef, tx, 'estimatefee')
    return tx


def get_rpc_fees_data_structures(fees_list, data_dict, data, mode):
    """
    This prepares data structures for get_fee_estimate
    Fees list is  
    :param fees_list: the list of fes (in order) to iterate through
    to determine which bucket the transaction falls in
    :param data_dict: A dict fee:data, to obtain the estimation for 
    the individual mempool entry
    :param data: A list of fee estimates (dicts) from the database
    :param mode: The mode of the estimation. Could be:
    conservative, economical or estimatefee (deprecated) 
    :return: 
    """
    for d in data:
        if d['mode'] == mode:
            rate = btc_kb_sat_b(Decimal(d['feerate']))
            d['feerate'] = rate
            data_dict[rate] = d
            fees_list.append(rate)
    fees_list = sorted(fees_list)
    return data_dict, fees_list


def get_fee_estimate(fees, data, m, api):
    """
    This works through the data estimates for the estimation 
    to see what the estimation would have been for the entry m.
    This only works on rpc_call
    :param fees: 
    :param data: 
    :param m: 
    :param api: 
    :return: 
    """
    log.debug(m)
    ratio = Decimal(m['fee']) * SATOSHIS_PER_BTC / m['size']
    m['ratio'] = ratio
    # updated = db.processed_mempool.update({'_id': m['_id']}, m)
    # print(updated)
    low = fees[0]
    for f in fees[1:]:
        high = f
        if ratio >= low and ratio < high:
            m[api] = data[f]['blocks']
            return m
        low = high
    if ratio >= high:
        # estimatesmartfee only goes down to 2,
        # so assume that higher would be 1
        m[api] = 1
        return m
    # If it fails, use this.
    else:
        m[api] = -1
        return m


def get_mempool_entries(start, end):
    """
    Gets the transactions which were recorded in the mempool between start and end    
    :param start: Mongo cursor from the first 
    :param end: 
    :return: 
    """
    # try:
    #     first_date = start['time']
    #     last_date = end['time']
    # except:
    # first_date = start['data'][0]['time']
    # last_date = end['data'][0]['time']

    query = {
        '$and': [{'time': {'$gte': time.mktime(start.timetuple())}},
                 {'time': {'$lt': time.mktime(end.timetuple())}}]
    }

    mempool_entries = db.processed_mempool.find(query)
    return mempool_entries
    # if start['api'] == 'bitgo':
    #     _process_bitgo(start['data'], mempool_entries, start=first_date)
    # elif start['api'] == 'rpc_call':
    #     _process_rpc_call(start['data'], mempool_entries, start=first_date)

if __name__ == '__main__':
    import datetime
    now = datetime.datetime.now()
    log.info('Starting application at %r' % now)
    # min = get_min_block_height()
    # get_inserted_block_for_all_transactions(min)

    # loop_mempool_entries(get_time_buckets('rpc_call'))
    collection_of_calls = get_time_bucket_start_points()
    # current = next(collection_of_calls)
    # for c in collection_of_calls:
    #     get_api_calls_in_interval(c['data'][0]['time'])
    loop_mempool_entries(collection_of_calls)
    end = datetime.datetime.now()
    log.info('Ending application at %r. Time taken %r' % (end, end))


