#!/usr/bin/env python
try:
    from . import reconstruct_mempool
except:
    import reconstruct_mempool
import client
import sys
import logging
from datetime import datetime
import argparse
from pymongo import MongoClient
import os

db = MongoClient('mongodb://localhost:27017').bitcoin


parser = argparse.ArgumentParser(description='')
parser.add_argument('--setup', help='Download the blocks for the blockchain', action='store_true')
parser.add_argument('--transactions', help='Download the transactions for period.  Must have either'
                                           '`start` or `recovery` to work', action='store_true')
parser.add_argument('--start', help='Datetime in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format to start analysis')
parser.add_argument('--recovery', help='If you want to continue from the last transaction date until'
                                       'the end date use this flag', action='store_true')
parser.add_argument('--end', help='Datetime in YYYY-MM-DD  or YYYY-MM-DD HH:MM:SS format to end analysis',
                    default=datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'))
parser.add_argument('--logging', help='Logging level DEBUG, INFO, WARNING, ERROR', default='INFO')
parser.add_argument('--reconstruct', help='Set the date to reconstruct the mempool from in YYYY-MM-DDTHH:MM:SS')
args = parser.parse_args()



os.environ['logging'] = args.logging

logging.basicConfig(
        level=os.environ.get('logging', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('__main__')

log.info('Logging level set to %s' % args.logging)


if __name__ == '__main__':
    start_time = datetime.now()
    if args.setup:
        print('args.setup')
        # reconstruct_mempool.get_all_blocks()
    else:
        pass
    if args.reconstruct:
        try:
            reconstruct = datetime.strptime(args.reconstruct, '%Y-%m-%dT%H:%M:%S')
            mempool = reconstruct_mempool.generate_mempool(reconstruct)
            print('Amount of transactions in mempool at %s: %d' % (args.reconstruct, mempool.count()))
        except Exception as e:
            log.exception(e)
            log.exception('Date missing, or incorrect date format, should be YYYY-MM-DDTHH:MM:SS')
            sys.exit(1)
    # sys.exit(0)
    start_date = None
    end_date = None
    if args.transactions:
        if args.start:
        #'2017-12-02 11:00:00'
            start_date = datetime.strptime(args.start, '%Y-%m-%dT%H:%M:%S')
        elif args.recovery:
            cursor = db.transactions.aggregate([{'$group': {'_id': None, 'max': {'$max': '$block_time'}}}])
            start_date = next(cursor)['max']
            start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S+0000')
        end_date = datetime.strptime(args.end, '%Y-%m-%dT%H:%M:%S')
        log.info('args.transactions %s %s' % (str(start_date), str(end_date)))
        reconstruct_mempool.get_transactions_for_period(start_date, end_date, recovery=True)
    # start_date = cursor = db.transactions.aggregate([{'$group': {'_id': None, 'max': {'$max': '$block_time'}}}])
    # start_date = datetime.strptime('2017-12-01 11:23:00', '%Y-%m-%d %H:%M:%S')
    # end_date =
    # listy = reconstruct_mempool.get_blocks_in_period(,
    #                                          )
    # print(listy)

    # for c in cursor:
    #     start_date = datetime.strptime(c['max'], '%Y-%m-%dT%H:%M:%S+0000')

    #
    # print(len(listy))
    print('Time taken to run query: ', datetime.now() - start_time)