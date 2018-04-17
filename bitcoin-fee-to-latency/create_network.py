import bitcoin, bitcoin.rpc
from pymongo import MongoClient
from decimal import Decimal

SATOSHI_BTC_RATE = Decimal(0.00000001)

db = MongoClient('mongodb://localhost').bitcoin

bitcoin.SelectParams('regtest')
#'http://127.0.0.1', 18332, '/home/developer/.bitcoin/bitcoin.conf')

from datetime import datetime
# Set up the amount of blocks we need to estimate the fee (as per bitcoin core algorithm)
# proxy.generate(1002)


start_date = '2017-11-30T00:00:00'


class CreateNetwork(object):

    def __init__(self, date):
        self.first_date = date
        self.node = bitcoin.rpc.Proxy()
        self.addresses = {}

    def get_first_block_height(self, date):
        return db.blocks.findOne({
            'block_time': {'$gte': start_date}
        }).sort({'height': 1})

    def get_blocks(self, height, limit):
        return db.blocks.find(
            {'block_time': {'$gte': '2017-11-30T00:00:00'}},
            {'_id': 0, 'height': 1}
        ).limit(limit).sort({'height': 1})

    def get_transactions_in_block(self, height):
        return db.transactions.find(
            {'block_height': height}
        ).sort({'block_time': 1})

    def process_transaction(self, tx):
        '''
        This function will use sendrawtransaction on the transaction. 
        It will create addresses if required
        :return: the output of sendrawtransaction
        '''
        import json
        with open('test.json') as f:
            js = json.load(f)
            print(js)
            js['inputs'] = self._process_inputs_and_outputs(js['inputs'])
            js['outputs'] = self._process_inputs_and_outputs(js['outputs'])


    def _process_inputs_and_outputs(self, js):
        for i in js:
            if 'address' in i and i['address'] is not None:
                i['address'] = self.get_address(i['address'])
        return js

    def get_address(self, address):
        '''
        Since we cannot create an address we specify, we will map our addresses
        to the original addresses in the blockchain
        :param address: 
        :return: 
        '''
        if address in self.addresses:
            return self.addresses[address]
        else:
            new_address = self.node.getnewaddress()
            self.addresses[address] = new_address
        return self.addresses[address]

    def select_input_address(self, inputs):
        for i in inputs:
            pass

    def get_outputs_total_cost(self, outputs):
        total = 0
        for o in outputs:
            if 'value' in o:
                total += o['value']
        return SATOSHI_BTC_RATE * Decimal(total)

    def process_single_address(self, js):
        

    def process_addresses(self):
        filters = {
            'block_time': {'$gte': self.first_date},
            # 'block_time': {'$lt': datetime. '2017-11-30T00:01:00'}
        }
        cursor = db.transactions.find(filters)
        for c in cursor:
            self.process_single_address(c)



if __name__ == '__main__':
    net = CreateNetwork(start_date)
    net.process_transaction('')





