from __future__ import print_function
import os
import blocktrail
try:
    with open('credentials') as f:
        string = f.read().strip().split('|')
        API_KEY = string[0]
        API_SECRET = string[1]
except:
    API_KEY = os.environ['API_KEY']
    API_SECRET = os.environ['API_SECRET']
    client = blocktrail.APIClient(api_key=API_KEY, api_secret=API_SECRET, network="BTC", testnet=False)
