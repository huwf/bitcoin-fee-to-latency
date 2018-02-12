import reconstruct_mempool
import client
from datetime import datetime
if __name__ == '__main__':
    start_time = datetime.now()
    # reconstruct_mempool.get_all_blocks()
    start_date = datetime.strptime('2017-11-01', '%Y-%m-%d')
    end_date = datetime.strptime('2017-11-08', '%Y-%m-%d')
    # listy = reconstruct_mempool.get_blocks_in_period(,
    #                                          )
    # print(listy)
    reconstruct_mempool.get_transactions_for_period(start_date, end_date)
    # print(len(listy))
    print('Time taken to run query: ', datetime.now() - start_time)