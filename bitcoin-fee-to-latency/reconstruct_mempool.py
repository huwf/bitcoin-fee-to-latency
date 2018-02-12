try:
    from .client import client
except:
    from client import client
from pymongo import MongoClient
from bson.son import SON
import datetime

db = MongoClient('mongodb://localhost:27017').bitcoin


def get_all_blocks(max_page=0, offset=0):
    current_page = 1 + offset
    per_page = 200
    total = 999999
    output = []
    while (current_page * per_page) < total:
        if max_page:
            if current_page > max_page:
                break
        kwargs = {"page": current_page, "limit": per_page}
        js = client.client.make_api_call(client.client.all_blocks, kwargs=kwargs)
        output = js['data']
        db.blocks.insert_many(output)
        print(output)
        # i += 1
        total = js['total']
        current_page += 1

    return output


def get_blocks_in_period(start_date, end_date, hours_before=4):
    """    
    :param start_date: A datetime object indicating the earliest period to be searched for.
      Results will be returned for 4 hours earlier
    :param end_date: A datetime object specifying the end of the period to be searched for
    :param hours_before: An int which specifies the housr before the period to search
    :return: A list of transaction IDs
    :rtype list
    """
    # Take earlier transaction into account, so we can construct mempool at the earliest time
    start_date = start_date - datetime.timedelta(hours=hours_before)
    # HACK: Can't get datetime to work, so converting to strings
    # Dates format is YYYY-MM-DD, so this still works
    start_date = datetime.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')

    end_date = datetime.datetime.strftime(end_date, '%Y-%m-%dT%H:%M:%S')
    query = {"$and": [{"block_time": {"$gte": start_date}}, {"block_time": {"$lt": end_date}}]}
    return list(db.blocks.find(query, {"hash": 1, "block_time": 1, "_id": 0}))


def get_transactions_for_period(start_date, end_date, limit=200):
    for b in get_blocks_in_period(start_date, end_date):
        print('processing block: %s' % b['hash'])
        current_page = 0
        # Temp value until we find out what it actually is
        total = 99999
        while limit * current_page < total:
            current_page += 1
            kwargs = {'block': b['hash'], 'limit': limit, 'page': current_page}
            transactions = client.make_api_call(client.block_transactions, kwargs)
            total = transactions['total']
            insert_trans = []
            for t in transactions['data']:
                hash = t['hash']
                tran = client.make_api_call(client.transaction, {'txhash': hash})
                if tran is not None:
                    insert_trans.append(tran)
                else:
                    print('tran is None for hash %s' % hash)
                    db.nonetypes.insert_one({'hash': hash})
                # try:
                #     db.transactions.insert_one(SON(tran))
                # except:
                #     print('Something went wrong!')
            if insert_trans:
                try:
                    db.transactions.insert_many(insert_trans, bypass_document_validation=True)
                except TypeError as err:
                    print('something went wrong...')


def generate_mempool(mempool_time):
    '''
    Simulates the mempool at a given time from transactions stored in the database
    :param mempool_time: A datetime object that we need the time for.
    :return: 
    '''
    query = {
        '$and': [{"first_seen_at": {'$lte': mempool_time}}, {'block_time': {'$gt': mempool_time}}]
    }
    db.transactions.find(query)