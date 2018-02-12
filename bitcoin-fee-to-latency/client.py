from __future__ import print_function
import os
import blocktrail
with open('credentials') as f:
    string = f.read().strip().split('|')
    API_KEY = string[0]
    API_SECRET = string[1]

    client = blocktrail.APIClient(api_key=API_KEY, api_secret=API_SECRET, network="BTC", testnet=False) #, api_secret="MY_APISECRET"
    # client.all_blocks()
