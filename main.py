#v1.0

import sys

import config
import utils

if len(sys.argv) == 1:
    print("Set TF as python main.py 15m")
    exit();

tf = sys.argv[1]

configs = utils.find_configs(tf)
if len(configs) == 0:
    print("No configs found for " + tf)
    exit()

for conf in configs:
    user = utils.get_user(conf['user_id'])
    account = utils.get_account(conf['account_id'])
    utils.log('START ' + conf['coin'] + ' for ' + user['name'] + ' on ' + account['name'] + '')

    ohlc = utils.get_ohlc(conf)

    v_fastEMA = utils.calculate_ema(ohlc, conf['fast_ema'])
    v_slowEMA = utils.calculate_ema(ohlc, conf['slow_ema'])
    v_filterEMA = utils.calculate_ema(ohlc, conf['filter_ema'])

    utils.log('EMA fast: ' + str(v_fastEMA[-1]))
    utils.log('EMA slow: ' + str(v_slowEMA[-1]))
    utils.log('EMA filter: ' + str(v_filterEMA[-1]))