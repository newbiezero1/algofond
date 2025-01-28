import utils

class Algo:
    def __init__(self, exchange,user,  ohlc, conf):
        self.exchange = exchange
        self.user = user
        self.ohlc = ohlc
        self.id = conf['id']
        self.coin = conf['coin']

        self.params = conf['param']
        self.balance = 0
        if conf['max_balance'] is not None:
            self.balance = conf['max_balance']
        self.max_drawdown = conf['max_drawdown']
        self.params['coin'] = self.coin
        self.have_long = False
        self.have_short = False
        self.tp = 0
        self.sl = 0
        self.longCondition = False
        self.shortCondition = False

    def check_drawdown(self):
        dep = float(self.exchange.get_balance())
        if dep > self.balance:
            utils.update_max_balance(self.id, dep, 1)

        if self.balance - (self.balance /100 * self.max_drawdown) > dep:
            utils.log(f'Drawdown check: {dep} < {self.balance}  max drawdown: {self.max_drawdown}')
            return False
        return True

    def check_position(self):
        positions = self.exchange.get_open_positions(self.coin)
        if len(positions) > 0:
            position = positions[0]
            if position['side'] == 'Buy':
                self.have_long = True
            else:
                self.have_short = True

    def trade_init(self):

        if self.longCondition and self.tp == 0 and self.sl == 0:
            self.tp = float(self.ohlc[-1]['open']) * (1 + float(self.params['tp']) / 100)
            self.sl = float(self.ohlc[-1]['open']) * (1 - float(self.params['sl']) / 100)
        if self.shortCondition and self.tp == 0 and self.sl == 0:
            self.tp = float(self.ohlc[-1]['open']) * (1 - float(self.params['tp']) / 100)
            self.sl = float(self.ohlc[-1]['open']) * (1 + float(self.params['sl']) / 100)

        try:
            self.check_position()
            if self.longCondition and not self.have_long:
                if self.have_short:
                    utils.log('CLOSE SHORT for LONG')
                    utils.close_pos(self.exchange, self.user, self.coin, 'short')
                utils.log('OPEN LONG')
                utils.open_pos(self.exchange, self.user, self.params, 'long',self.tp, self.sl, float(self.ohlc[-1]['open']))


            if self.shortCondition and not self.have_short:
                if self.have_long:
                    utils.log('CLOSE LONG for SHORT')
                    utils.close_pos(self.exchange, self.user, self.coin, 'long')
                utils.log('OPEN SHORT')
                utils.open_pos(self.exchange, self.user, self.params, 'short', tp, sl, float(self.ohlc[-1]['open']))
        except Exception as e:
            utils.log('ERROR: ' + str(e))

    def v1(self):
        utils.log('run v1')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        utils.log(f'rsi: {rsi[-2]}')
        self.longCondition = rsi[-2] < float(self.params['oversell'])
        self.shortCondition = rsi[-2] > float(self.params['overbuy'])

        self.trade_init()

        return
    
    def v2(self):
        utils.log('run v2')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        utils.log(f'rsi: {rsi[-2]}')
        self.longCondition = rsi[-2] < float(self.params['oversell'])
        self.shortCondition = rsi[-2] > float(self.params['overbuy'])
        candlesize = self.ohlc[-3]['high'] - self.ohlc[-3]['low']

        if self.longCondition:
            self.sl = self.ohlc[-1]['open'] - candlesize
            self.tp = self.ohlc[-1]['open'] + candlesize
        if self.shortCondition:
            self.sl = self.ohlc[-1]['open'] + candlesize
            self.tp = self.ohlc[-1]['open'] - candlesize
        self.trade_init()
        return

    def v3(self):
        utils.log('run v3')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        ema = utils.calculate_ema(self.ohlc, self.params['ema'])

        two_day_rsi_avg = (rsi[-2] + rsi[-3]) / 2
        utils.log(f'two_day_rsi_avg: {two_day_rsi_avg}')
        utils.log(f'ema: {ema[-2]}')
        self.longCondition = self.ohlc[-1]['open'] > ema[-2] and two_day_rsi_avg < 33

        self.trade_init()
        return

    def v5(self):
        utils.log('run v5')
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])

        utils.log(f'Rsi: {rsi[-2]}')
        crossover = utils.calculate_crossover([rsi[-3], rsi[-2]], [float(self.params['oversell']), float(self.params['oversell'])])
        crossunder = utils.calculate_crossunder([rsi[-3], rsi[-2]], [float(self.params['overbuy']), float(self.params['overbuy'])])
        self.longCondition = crossover[-1]
        self.shortCondition = crossunder[-1]

        self.trade_init()
        return

    def v6(self):
        utils.log('run v6')

        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])

        utils.log(f'Rsi: {rsi[-2]}')
        crossover = utils.calculate_crossover([rsi[-3], rsi[-2]], [float(self.params['oversell']), float(self.params['oversell'])])
        crossunder = utils.calculate_crossunder([rsi[-3], rsi[-2]], [float(self.params['overbuy']), float(self.params['overbuy'])])
        self.longCondition = crossover[-1]
        self.shortCondition = crossunder[-1]
        if self.longCondition:
            self.sl = self.ohlc[-2]['low']
            self.tp = float(self.ohlc[-1]['open']) * (1 + float(self.params['tp']) / 100)
        if self.shortCondition:
            self.sl = self.ohlc[-1]['high']
            self.tp = float(self.ohlc[-1]['open']) * (1 - float(self.params['tp']) / 100)

        self.trade_init()
        return

    def v7(self):
        utils.log('run v7')
        trendEma = utils.calculate_ema(self.ohlc, self.params['filter_ema'])
        fastEma = utils.calculate_ema(self.ohlc, self.params['fast_ema'])
        slowEma = utils.calculate_ema(self.ohlc, self.params['slow_ema'])
        crossover = utils.calculate_crossover(fastEma, slowEma)
        crossunder = utils.calculate_crossunder(fastEma, slowEma)

        utils.log(f'Trend Ema: {trendEma[-2]}')
        utils.log(f'Fast Ema: {fastEma[-2]}')
        utils.log(f'Slow Ema: {slowEma[-2]}')
        self.longCondition = crossover[-2]  and self.ohlc[-1]['open'] > trendEma[-2] and slowEma[-2] > trendEma[-2]
        self.shortCondition = crossunder[-2]  and self.ohlc[-1]['open'] < trendEma[-2] and slowEma[-2] < trendEma[-2]

        self.trade_init()
        return

    def v8(self):
        utils.log('run v8')
        trendEma = utils.calculate_ema(self.ohlc, self.params['filter_ema'])
        fastEma = utils.calculate_ema(self.ohlc, self.params['fast_ema'])
        slowEma = utils.calculate_ema(self.ohlc, self.params['slow_ema'])
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        crossover = utils.calculate_crossover(fastEma, slowEma)
        crossunder = utils.calculate_crossunder(fastEma, slowEma)

        utils.log(f'Trend Ema: {trendEma[-2]}')
        utils.log(f'Fast Ema: {fastEma[-2]}')
        utils.log(f'Slow Ema: {slowEma[-2]}')
        utils.log(f'Rsi: {rsi[-2]}')
        self.longCondition = crossover[-2]  and self.ohlc[-1]['open'] > trendEma[-2] and rsi[-2] < float(self.params['overbuy'])
        self.shortCondition = crossunder[-2]  and self.ohlc[-1]['open'] < trendEma[-2] and rsi[-2] > float(self.params['oversell'])

        self.trade_init()
        return

    def v9(self):
        utils.log('run v9')
        trendEma = utils.calculate_ema(self.ohlc, self.params['filter_ema'])
        crossover = utils.calculate_crossover([self.ohlc[-3]['close'], self.ohlc[-2]['close']], [trendEma[-2], trendEma[-2]])
        crossunder = utils.calculate_crossunder([self.ohlc[-3]['close'], self.ohlc[-2]['close']]  , [trendEma[-2], trendEma[-2]])

        utils.log(f'Trend Ema: {trendEma[-2]}')
        utils.log(f'Price: {self.ohlc[-1]["open"]}')

        self.longCondition = crossover[-1]
        self.shortCondition = crossunder[-1]

        self.trade_init()
        return

    def v10(self):
        utils.log('run v10')
        trendEma = utils.calculate_ema(self.ohlc, self.params['filter_ema'])
        slowEma = utils.calculate_ema(self.ohlc, self.params['slow_ema'])
        crossover = utils.calculate_crossover(slowEma, trendEma)
        crossunder = utils.calculate_crossunder(slowEma, trendEma)

        utils.log(f'Trend Ema: {trendEma[-2]}')
        utils.log(f'Slow Ema: {slowEma[-2]}')
        self.longCondition = crossover[-2]
        self.shortCondition = crossunder[-2]

        self.trade_init()
        return

    def v11(self):
        utils.log('run v11')
        trendEma = utils.calculate_ema(self.ohlc, self.params['filter_ema'])
        rsi = utils.calculate_rsi(self.ohlc, self.params['rsi_length'])
        crossover = utils.calculate_crossover([self.ohlc[-3]['close'], self.ohlc[-2]['close']], [trendEma[-2], trendEma[-2]])
        crossunder = utils.calculate_crossunder([self.ohlc[-3]['close'], self.ohlc[-2]['close']]  , [trendEma[-2], trendEma[-2]])

        utils.log(f'Trend Ema: {trendEma[-2]}')
        utils.log(f'Price: {self.ohlc[-1]["open"]}')
        utils.log(f'RSI: {rsi[-2]}')

        self.longCondition = crossover[-1] and rsi[-2] < float(self.params['overbuy'])
        self.shortCondition = crossunder[-1] and rsi[-2] > float(self.params['oversell'])

        self.trade_init()
        return