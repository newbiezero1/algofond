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
    utils.extract_log()
    user = utils.get_user(conf['user_id'])
    account = utils.get_account(conf['account_id'])
    utils.log('\n=====START ' + conf['coin'] + ' for ' + user['name'] + ' on ' + account['name'] + '=====')

    ohlc = utils.get_ohlc(conf)

    v_fastEMA = utils.calculate_ema(ohlc, conf['fast_ema'])
    v_slowEMA = utils.calculate_ema(ohlc, conf['slow_ema'])
    v_filterEMA = utils.calculate_ema(ohlc, conf['filter_ema'])[-1]

    utils.log('EMA fast: ' + str(round(v_fastEMA[-1],2)))
    utils.log('EMA slow: ' + str(round(v_slowEMA[-1],2)))
    utils.log('EMA filter: ' + str(round(v_filterEMA,2)))

    rsi = utils.calculate_rsi(ohlc, 14)[-1]
    utils.log('RSI: ' + str(round(rsi,2)))

    bullSignal = utils.calculate_bullSignal(v_fastEMA, v_slowEMA)[-2]
    bearSignal = utils.calculate_bearSignal(v_fastEMA, v_slowEMA)[-2]

    utils.log('Bull Signal: ' + str(bullSignal))
    utils.log('Bear Signal: ' + str(bearSignal))

    close = ohlc[-1]["close"]
    high = ohlc[-1]["high"]
    low = ohlc[-1]["low"]

    utils.log('CURRENT: ' + str(float(close)))
    utils.log('HIGH: ' + str(float(high)))
    utils.log('LOW: ' + str(float(low)))

    exchange = utils.get_exchange(account)
    positions = exchange.get_open_positions(conf['coin'])

    if len(positions) > 0:
        position = positions[0]
        utils.log('CURRENT POSITION SIDE: ' + str(position['side']))
        utils.log('CURRENT POSITION AVG: ' + str(position['avgPrice']))

        if conf['force_rsi_tp_for_long'] and rsi >= conf['rsi_tp_long']:
            utils.log('Close Long RSI Force TP triggered - Closing Long')
            utils.close_pos(exchange, user, conf['coin'], 'long')

        if conf['force_rsi_tp_for_short'] and rsi <= conf['rsi_tp_short']:
            utils.log('Close Short RSI Force TP triggered - Closing Short')
            utils.close_pos(exchange, user, conf['coin'], 'short')

        if conf['tp_on']:
            if position['side'] == 'Buy':
                long_take_profit = float(position['avgPrice']) * (1 + float(conf['tp'])/100)
                if float(high) >= long_take_profit:
                    utils.log('Close Long Setted TP triggered - Closing Long')
                    utils.close_pos(exchange, user, conf['coin'], 'long')
            else:
                short_take_profit = float(position['avgPrice']) * (1 - float(conf['tp'])/100)
                if float(low) <= short_take_profit:
                    utils.log('Close Short Setted TP triggered - Closing Short')
                    utils.close_pos(exchange, user, conf['coin'], 'short')

        if conf['sl_on']:
            if position['side'] == 'Buy':
                long_stop_loss = float(position['avgPrice']) * (1 - float(conf['sl'])/100)
                if float(low) <= long_stop_loss:
                    utils.log('Close Long Setted SL triggered - Closing Long')
                    utils.close_pos(exchange, user, conf['coin'], 'long')
            else:
                short_stop_loss = float(position['avgPrice']) * (1 + float(conf['sl'])/100)
                if float(high) >= short_stop_loss:
                    utils.log('Close Short Setted SL triggered - Closing Short')
                    utils.close_pos(exchange, user, conf['coin'], 'short')


    have_long = False
    have_short = False
    positions = exchange.get_open_positions(conf['coin'])
    if len(positions) > 0:
        position = positions[0]
        if position['side'] == 'Buy':
            have_long = True
        else:
            have_short = True

    # check open conditions
    if conf['enable_long'] and bullSignal and (not conf['filter_ema_on'] or float(close) > float(v_filterEMA)):
        if conf['rsi_protection_for_long'] and float(rsi) > float(conf['high_rsi']):
            utils.log('CLOSE LONG, No Long - RSI Protection')
            utils.close_pos(exchange, user, conf['coin'], 'long')
        elif conf['filter_ema_on'] and float(close) <= float(v_filterEMA):
            utils.log('CLOSE LONG, No Long - Filter EMA Protection')
            utils.close_pos(exchange, user, conf['coin'], 'long')
        else:
            utils.log('CLOSE SHORT for LONG')
            utils.close_pos(exchange, user, conf['coin'], 'short')
            if not have_long:
                utils.log('OPEN LONG')
                utils.open_pos(exchange, user, conf['coin'], 'long')

    if conf['enable_short'] and bearSignal and (not conf['filter_ema_on'] or float(close) < float(v_filterEMA)):
        if conf['rsi_protection_for_short'] and float(rsi) < float(conf['low_rsi']):
            utils.log('CLOSE SHORT, No Short - RSI Protection')
            utils.close_pos(exchange, user, conf['coin'], 'short')
        elif conf['filter_ema_on'] and float(close) >= float(v_filterEMA):
            utils.log('CLOSE SHORT, No Short - Filter EMA Protection')
            utils.close_pos(exchange, user, conf['coin'], 'short')
        else:
            utils.log('CLOSE LONG for SHORT')
            utils.close_pos(exchange, user, conf['coin'], 'long')
            if not have_short:
                utils.log('OPEN SHORT')
                utils.open_pos(exchange, user, conf['coin'], 'short')