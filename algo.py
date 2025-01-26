import utils

class Algo:
    def __init__(self, exchange,user,  ohlc, conf):
        self.exchange = exchange
        self.user = user
        self.ohlc = ohlc
        self.id = conf['id']
        self.coin = conf['coin']
        self.params = conf['param']
        self.balance = conf['max_balance']
        self.max_drawdown = conf['max_drawdown']
        self.params['coin'] = self.coin

    def check_drawdown(self):
        dep = float(self.exchange.get_balance())
        if dep > self.balance:
            utils.update_max_balance(self.id, dep, 1)

        if self.balance - (self.balance /100 * self.max_drawdown) > dep:
            utils.log(f'Drawdown check: {dep} < {self.balance}  max drawdown: {self.max_drawdown}')
            return False
        return True
    def v1(self):
        utils.log('run v1')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        utils.log(f'rsi: {rsi[-2]}')
        longCondition = rsi[-2] < self.params['oversell']
        shortCondition = rsi[-2] > self.params['overbuy']
        have_long = False
        have_short = False
        positions = self.exchange.get_open_positions(self.coin)
        if len(positions) > 0:
            position = positions[0]
            if position['side'] == 'Buy':
                have_long = True
            else:
                have_short = True

        try:
            if longCondition and not have_long:
                if have_short:
                    utils.log('CLOSE SHORT for LONG')
                    utils.close_pos(self.exchange, self.user, self.coin, 'short')
                utils.log('OPEN LONG')
                tp = float(self.ohlc[-1]['open']) * (1 + float(self.params['tp']) / 100)
                sl = float(self.ohlc[-1]['open']) * (1 - float(self.params['sl']) / 100)
                utils.open_pos(self.exchange, self.user, self.params, 'long',tp, sl, float(self.ohlc[-1]['open']))


            if shortCondition and not have_short:
                if have_long:
                    utils.log('CLOSE LONG for SHORT')
                    utils.close_pos(self.exchange, self.user, self.coin, 'long')
                utils.log('OPEN SHORT')
                tp = float(self.ohlc[-1]['open']) * (1 - float(self.params['tp']) / 100)
                sl = float(self.ohlc[-1]['open']) * (1 + float(self.params['sl']) / 100)
                utils.open_pos(self.exchange, self.user, self.params, 'short', tp, sl, float(self.ohlc[-1]['open']))
        except Exception as e:
            utils.log('ERROR: ' + str(e))
        return
    
    def v2(self):
        utils.log('run v2')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        utils.log(f'rsi: {rsi[-2]}')
        longCondition = rsi[-2] < self.params['oversell']
        shortCondition = rsi[-2] > self.params['overbuy']
        candlesize = self.ohlc[-3]['high'] - self.ohlc[-3]['low']
        have_long = False
        have_short = False
        positions = self.exchange.get_open_positions(self.coin)
        if len(positions) > 0:
            position = positions[0]
            if position['side'] == 'Buy':
                have_long = True
            else:
                have_short = True

        try:
            if longCondition and not have_long:
                if have_short:
                    utils.log('CLOSE SHORT for LONG')
                    utils.close_pos(self.exchange, self.user, self.coin, 'short')
                utils.log('OPEN LONG')
                sl = self.ohlc[-1]['open'] - candlesize
                tp = self.ohlc[-1]['open'] + candlesize
                utils.open_pos(self.exchange, self.user, self.params, 'long',tp, sl, float(self.ohlc[-1]['open']))


            if shortCondition and not have_short:
                if have_long:
                    utils.log('CLOSE LONG for SHORT')
                    utils.close_pos(self.exchange, self.user, self.coin, 'long')
                utils.log('OPEN SHORT')
                sl = self.ohlc[-1]['open'] + candlesize
                tp = self.ohlc[-1]['open'] - candlesize
                utils.open_pos(self.exchange, self.user, self.params, 'short',tp, sl, float(self.ohlc[-1]['open']))
        except Exception as e:
            utils.log('ERROR: ' + str(e))
        return

    def v3(self):
        utils.log('run v3')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        ema = utils.calculate_ema(self.ohlc, self.params['ema'])

        two_day_rsi_avg = (rsi[-2] + rsi[-3]) / 2
        utils.log(f'two_day_rsi_avg: {two_day_rsi_avg}')
        utils.log(f'ema: {ema[-2]}')
        longCondition = self.ohlc[-1]['open'] > ema[-2] and two_day_rsi_avg < 33
        have_long = False
        have_short = False
        positions = self.exchange.get_open_positions(self.coin)
        if len(positions) > 0:
            position = positions[0]
            if position['side'] == 'Buy':
                have_long = True
            else:
                have_short = True

        try:
            if longCondition and not have_long:
                if have_short:
                    utils.log('CLOSE SHORT for LONG')
                    utils.close_pos(self.exchange, self.user, self.coin, 'short')
                utils.log('OPEN LONG')
                tp = float(self.ohlc[-1]['open']) * (1 + float(self.params['tp']) / 100)
                sl = float(self.ohlc[-1]['open']) * (1 - float(self.params['sl']) / 100)
                utils.open_pos(self.exchange, self.user, self.params, 'long',tp, sl, float(self.ohlc[-1]['open']))

        except Exception as e:
            utils.log('ERROR: ' + str(e))
        return

    def v10(self):
        utils.log('run v10')
        trendEma = utils.calculate_ema(self.ohlc, self.params['filter_ema'])
        slowEma = utils.calculate_ema(self.ohlc, self.params['slow_ema'])
        crossover = utils.calculate_crossover(slowEma, trendEma)
        crossunder = utils.calculate_crossunder(slowEma, trendEma)

        utils.log(f'Trend Ema: {trendEma[-2]}')
        utils.log(f'Slow Ema: {slowEma[-2]}')
        longCondition = crossover[-2]
        shortCondition = crossunder[-2]
        have_long = False
        have_short = False
        positions = self.exchange.get_open_positions(self.coin)
        if len(positions) > 0:
            position = positions[0]
            if position['side'] == 'Buy':
                have_long = True
            else:
                have_short = True

        try:
            if longCondition and not have_long:
                if have_short:
                    utils.log('CLOSE SHORT for LONG')
                    utils.close_pos(self.exchange, self.user, self.coin, 'short')
                utils.log('OPEN LONG')
                tp = float(self.ohlc[-1]['open']) * (1 + float(self.params['tp']) / 100)
                sl = float(self.ohlc[-1]['open']) * (1 - float(self.params['sl']) / 100)
                utils.open_pos(self.exchange, self.user, self.params, 'long',tp, sl, float(self.ohlc[-1]['open']))


            if shortCondition and not have_short:
                if have_long:
                    utils.log('CLOSE LONG for SHORT')
                    utils.close_pos(self.exchange, self.user, self.coin, 'long')
                utils.log('OPEN SHORT')
                tp = float(self.ohlc[-1]['open']) * (1 - float(self.params['tp']) / 100)
                sl = float(self.ohlc[-1]['open']) * (1 + float(self.params['sl']) / 100)
                utils.open_pos(self.exchange, self.user, self.params, 'short', tp, sl, float(self.ohlc[-1]['open']))
        except Exception as e:
            utils.log('ERROR: ' + str(e))
        return