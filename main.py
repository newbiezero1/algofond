#v1.0

import sys
import os
import time
import utils
import algo

from datetime import datetime

if len(sys.argv) == 1:
    print("Set TF as python main.py 15m")
    exit();

tf = sys.argv[1]

configs = utils.find_configs(tf)
if len(configs) == 0:
    print("No configs found for " + tf)
    exit()

time.sleep(2)
for conf in configs:
    try:
        utils.extract_log()
        user = utils.get_user(conf['user_id'])
        account = utils.get_account(conf['account_id'])

        current_dateTime = datetime.now()
        utils.log(f'\n====={current_dateTime} START ' + conf['coin'] + f' ({conf["param"]}) for ' + user['name'] + ' on ' + account['name'] + ' '+ conf['tf']+ ' =====')

        ohlc = utils.get_ohlc(conf)
        exchange = utils.get_exchange(account)
        algo = algo.Algo(exchange, user, ohlc,  conf)
        if conf['version'] == 1:
            algo.v1()

        utils.extract_log()
        os._exit(0)

    except Exception as e:
        utils.log('ERROR: '+str(e))
    utils.extract_log()

os._exit(0)