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
    v_filterEMA = utils.calculate_ema(ohlc, conf['filter_ema'])[-1]

    utils.log('EMA fast: ' + str(v_fastEMA[-1]))
    utils.log('EMA slow: ' + str(v_slowEMA[-1]))
    utils.log('EMA filter: ' + str(v_filterEMA))

    rsi = utils.calculate_rsi(ohlc, 14)[-1]
    utils.log('RSI: ' + str(rsi))

    bullSignal = utils.calculate_bullSignal(v_fastEMA, v_slowEMA)[-2]
    bearSignal = utils.calculate_bearSignal(v_fastEMA, v_slowEMA)[-2]

    utils.log('Bull Signal: ' + str(bullSignal))
    utils.log('Bear Signal: ' + str(bearSignal))

    close = ohlc[-1]["close"]
    high = ohlc[-1]["high"]
    low = ohlc[-1]["low"]

    utils.log('CURRENT: ' + str(close))
    utils.log('HIGH: ' + str(high))
    utils.log('LOW: ' + str(low))

    have_long = False
    have_short = False

    # check open conditions
    if conf['enable_long'] and bullSignal and (not conf['filter_ema_on'] or close > v_filterEMA):
        if conf['rsi_protection_for_long'] and rsi > conf['high_rsi']:
            utils.log('CLOSE LONG, No Long - RSI Protection')
        elif conf['filter_ema_on'] and close <= v_filterEMA:
            utils.log('CLOSE LONG, No Long - Filter EMA Protection')
        else:
            utils.log('CLOSE SHORT for LONG')
            if not have_long:
                utils.log('OPEN LONG')

    if conf['enable_short'] and bearSignal and (not conf['filter_ema_on'] or close < v_filterEMA):
        if conf['rsi_protection_for_short'] and rsi < conf['low_rsi']:
            utils.log('CLOSE SHORT, No Short - RSI Protection')
        elif conf['filter_ema_on'] and close >= v_filterEMA:
            utils.log('CLOSE SHORT, No Short - Filter EMA Protection')
        else:
            utils.log('CLOSE LONG for SHORT')
            if not have_short:
                utils.log('OPEN SHORT')