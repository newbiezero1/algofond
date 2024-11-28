#v1.0

import sys
import os
import time
import utils

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
        utils.log(f'\n====={current_dateTime} START ' + conf['coin'] + ' for ' + user['name'] + ' on ' + account['name'] + ' '+ conf['tf']+ ' =====')

        ohlc = utils.get_ohlc(conf)

        v_fastEMA = utils.calculate_ema(ohlc, conf['fast_ema'])
        v_slowEMA = utils.calculate_ema(ohlc, conf['slow_ema'])
        v_filterEMA = utils.calculate_ema(ohlc, conf['filter_ema'])

        utils.log('EMA fast: ' + str(round(v_fastEMA[-1],2)))
        utils.log('EMA slow: ' + str(round(v_slowEMA[-1],2)))
        utils.log('EMA filter: ' + str(round(v_filterEMA[-1],2)))

        rsi = utils.calculate_rsi(ohlc, 14)[-2]
        utils.log('RSI: ' + str(round(rsi,2)))

        bullSignalList = utils.calculate_bullSignal(v_fastEMA, v_slowEMA)
        bearSignalList = utils.calculate_bearSignal(v_fastEMA, v_slowEMA)

        bullSignal = bullSignalList[-2]
        bearSignal = bearSignalList[-2]

        signal_ohlc_bull = []
        signal_ohlc_bear = []
        last_signal = 'bull'
        for key, value in enumerate(ohlc):
            if bullSignalList[key] and float(value['close']) > v_filterEMA[key]:
                signal_ohlc_bull.append(ohlc[key])
                last_signal = 'bull'
            if bearSignalList[key] and float(value['close']) < v_filterEMA[key]:
                signal_ohlc_bear.append(ohlc[key])
                last_signal = 'bear'
        magic_rsi_bull = utils.calculate_rsi(signal_ohlc_bull, 14)
        magic_rsi_bear = utils.calculate_rsi(signal_ohlc_bear, 14)
        if last_signal == 'bull':
            magic_rsi = magic_rsi_bull[-1]
        elif last_signal == 'bear':
            magic_rsi = magic_rsi_bear[-1]

        utils.log('Bull Signal: ' + str(bullSignal))
        utils.log('Bear Signal: ' + str(bearSignal))

        open = ohlc[-1]["open"]
        high = ohlc[-1]["high"]
        low = ohlc[-1]["low"]

        utils.log('Last signal: ' + str(last_signal))
        utils.log('Magic RSI: ' + str(round(magic_rsi, 2)))
        utils.log('OPEN: ' + str(float(open)))
        utils.log('HIGH: ' + str(float(high)))
        utils.log('LOW: ' + str(float(low)))
        if conf['coin'] == 'BCH':
            utils.log('OHLC2: ' + str(ohlc[-2]))
            utils.log('OHLC1: ' + str(ohlc[-1]))

        exchange = utils.get_exchange(account)
        positions = exchange.get_open_positions(conf['coin'])
        if len(positions) > 0:
            position = positions[0]
            utils.log('CURRENT POSITION SIDE: ' + str(position['side']))
            utils.log('CURRENT POSITION AVG: ' + str(position['avgPrice']))

            if conf['force_rsi_tp_for_long'] and rsi >= conf['rsi_tp_long'] and position['side'] == 'Buy':
                utils.log('Close Long RSI Force TP triggered - Closing Long')
                utils.close_pos(exchange, user, conf['coin'], 'long')

            if conf['force_rsi_tp_for_short'] and rsi <= conf['rsi_tp_short'] and position['side'] == 'Sell' :
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

            if conf['use_reversal']:
                reversal_ohlc = ohlc[len(ohlc)- conf['reversal_count']:]
                reversal_filter_ema = v_filterEMA[len(v_filterEMA) - conf['reversal_count']:]
                reversal_counter = 0
                for i, item in enumerate(reversal_ohlc):
                    if position['side'] == 'Buy':
                        if float(item['close']) < reversal_filter_ema[i]:
                            reversal_counter += 1
                        else:
                            reversal_counter = 0
                    if position['side'] == 'Sell':
                        if float(item['close']) > reversal_filter_ema[i]:
                            reversal_counter += 1
                        else:
                            reversal_counter = 0
                if reversal_counter >= conf['reversal_count']:
                    utils.log('Reclaim EMA SL')
                    if position['side'] == 'Buy':
                        utils.close_pos(exchange, user, conf['coin'], 'long')
                    else:
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
        try:
            if conf['enable_long'] and bullSignal and (not conf['filter_ema_on'] or float(open) > float(v_filterEMA[-1])):
                if not conf['rsi_protection_for_long'] or float(magic_rsi) <= float(conf['high_rsi']):
                    utils.log('CLOSE SHORT for LONG')
                    utils.close_pos(exchange, user, conf['coin'], 'short')
                    if not have_long:
                        utils.log('OPEN LONG')
                        utils.open_pos(exchange, user, conf, 'long', float(open))

            if conf['enable_short'] and bearSignal and (not conf['filter_ema_on'] or float(open) < float(v_filterEMA[-1])):
                if not conf['rsi_protection_for_short'] or float(magic_rsi) >= float(conf['low_rsi']):
                    utils.log('CLOSE LONG for SHORT')
                    utils.close_pos(exchange, user, conf['coin'], 'long')
                    if not have_short:
                        utils.log('OPEN SHORT')
                        utils.open_pos(exchange, user, conf, 'short', float(open))
        except Exception as e:
            utils.log('ERROR: '+str(e))
    except Exception as e:
        utils.log('ERROR: '+str(e))
    utils.extract_log()

os._exit(0)