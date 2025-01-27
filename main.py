#v1.0

import sys
import os
import time
import utils
from algo import Algo
from notifyer import Notifyer
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
        algo = Algo(exchange, user, ohlc,  conf)
        if not algo.check_drawdown():
            notifyer = Notifyer(user["tg_chat_id"])
            notifyer.send_error(utils.extract_log(), "Drawdown check")
            continue
        if conf['version_name'] == 'v1':
            algo.v1()
        elif conf['version_name'] == 'v2':
            algo.v2()
        elif conf['version_name'] == 'v3':
            algo.v3()
        elif conf['version_name'] == 'v5':
            algo.v5()
        elif conf['version_name'] == 'v6':
            algo.v6()
        elif conf['version_name'] == 'v10':
            algo.v10()


    except Exception as e:
        utils.log('ERROR: '+str(e))
    utils.extract_log()

os._exit(0)