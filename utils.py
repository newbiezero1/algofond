import requests
import pandas as pd
import json
from datetime import datetime


import config
from db import Database
from bybit import Bybit
from hyper import Hyper
from notifyer import Notifyer

users = {}
accounts = {}
ohlc_cache = {}

log_tmp = ''

def log(message: str)-> None:
    global log_tmp
    log_tmp += message + '\n'
    print(message)

def extract_log():
    global log_tmp
    tmp_log = log_tmp
    log_tmp = ''
    with open('log.txt', "a") as f:
        f.write(f'\n'+str(tmp_log))
    return tmp_log


def update_max_balance(config_id, balance, enabled=1):
    db.execute_query(f'update configs set max_balance = {balance} where id = {config_id} and enabled = {enabled}')

def find_configs(tf: str) -> list:
    res = db.execute_query(f'select * from configs where tf = "{tf}" and enabled = 1')
    configs = []
    for row in res:
        version = db.execute_query(f'select name from versions where id = "{row[6]}"')[0]
        config = {
            "id": row[0],
            "user_id": row[1],
            "account_id": row[2],
            "coin": row[3],
            "tf": row[4],
            "max_drawdown": row[5],
            "version": row[6],
            "version_name": version[0],
            "param": json.loads(row[7]),
            'start_balance': row[8],
            'max_balance': row[10],
        }
        configs.append(config)
    return configs

def get_user(user_id):
    if not user_id in users:
        res = db.execute_query(f'select * from users where id = "{user_id}"')
        row = res[0]
        user = {"id": row[0],
                "name": row[1],
                "tg_chat_id": row[2]
                }
        users[user_id] = user
    else:
        user = users[user_id]
    return user

def get_account(account_id):
    if not account_id in accounts:
        res = db.execute_query(f'select * from accounts where id = "{account_id}"')
        row = res[0]
        account = {"id": row[0],
                "user_id": row[1],
                "name": row[2],
                "api_key": row[3],
                "api_secret": row[4],
                "exchange": row[5],
                }
        accounts[account_id] = account
    else:
        account = accounts[account_id]
    return account
def get_kline_from_db(coin, tf, date):
    res = db.execute_query(f'select * from ohlc where coin = "{coin}" and tf= "{tf}" and "{date}" > start and "{date}" < end')
    return res[0][2]

def get_ohlc(conf):
    cache_key = f'{conf["coin"]}_{conf["tf"]}'
    if cache_key in ohlc_cache:
        print('from cache')
        return ohlc_cache[cache_key]

    limit = 1500;
    interval = conf['tf']
    umnozhitel = 5

    ohlc = []
    unix_time = int(datetime.now().timestamp())

    response = requests.get(f'https://fapi.binance.com/fapi/v1/klines?symbol={conf["coin"]}USDT&interval={interval}&limit={limit}')
    kline = response.json()
    for line in kline:
        data = {"timestamp": line[0], "open": float(line[1]),
                "high": float(line[2]),
                "low": float(line[3]),
                "close": float(line[4])}
        ohlc.append(data)
    ohlc_cache[cache_key] = ohlc
    return ohlc

def calculate_ema(ohlc, period):
    period = int(period)
    prices = []
    for line in ohlc:
        prices.append(line["close"])
    prices_series = pd.Series(prices)
    ema = prices_series.ewm(span=period, adjust=False).mean()
    return ema.tolist()
def calculate_crossover(v_fastEMA, v_slowEMA):
    bullSignal = []
    for i in range(len(v_fastEMA)):
        bullSignal.append(False)
        if i == 0:
            continue
        if v_fastEMA[i - 1] < v_slowEMA[i - 1] and v_fastEMA[i] > v_slowEMA[i]:
            bullSignal[i] = True
    return bullSignal

def calculate_crossunder(v_fastEMA, v_slowEMA):
    bearSignal = []
    for i in range(len(v_fastEMA)):
        bearSignal.append(False)
        if i == 0:
            continue
        if v_fastEMA[i - 1] > v_slowEMA[i - 1] and v_fastEMA[i] < v_slowEMA[i]:
            bearSignal[i] = True
    return bearSignal
def calculate_rsi(ohlc, period):
    prices = []
    period = int(period)
    for line in ohlc:
        prices.append(line["close"])

    prices_series = pd.Series(prices).astype(float)

    # Расчет изменения цен
    delta = prices_series.diff()

    # Вычисление прироста и убытка
    gain = delta.where(delta > 0, 0)  # Прирост
    loss = -delta.where(delta < 0, 0)  # Убыток (в положительных значениях)

    # Вычисление средних прироста и убытка за период
    avg_gain_initial = gain.rolling(window=period, min_periods=period).mean()
    avg_loss_initial = loss.rolling(window=period, min_periods=period).mean()

    # После первого периода используем формулу EMA для среднего прироста и убытка
    avg_gain = pd.concat([avg_gain_initial.iloc[:period], gain[period:].ewm(alpha=1 / period, adjust=False).mean()])
    avg_loss = pd.concat([avg_loss_initial.iloc[:period], loss[period:].ewm(alpha=1 / period, adjust=False).mean()])

    # Рассчет RS (отношение средних прироста к среднему убытку)
    rs = avg_gain / avg_loss

    # Рассчет RSI
    rsi = 100 - (100 / (1 + rs))

    # Возвращаем RSI в виде списка, где значения до периода заполнены NaN
    rr = rsi.tolist()
    rounded_rsi = []
    for i in rr:
        if i > 0:
            rounded_rsi.append(round(i,2))
        else:
            rounded_rsi.append(0)
    return rounded_rsi

def calculate_bullSignal(v_fastEMA, v_slowEMA):
    bullSignal = []
    for i in range(len(v_fastEMA)):
        bullSignal.append(False)
        if i == 0:
            continue
        if v_fastEMA[i - 1] < v_slowEMA[i - 1] and v_fastEMA[i] > v_slowEMA[i]:
            bullSignal[i] = True
    return bullSignal

def calculate_bearSignal(v_fastEMA, v_slowEMA):
    bearSignal = []
    for i in range(len(v_fastEMA)):
        bearSignal.append(False)
        if i == 0:
            continue
        if v_fastEMA[i - 1] > v_slowEMA[i - 1] and v_fastEMA[i] < v_slowEMA[i]:
            bearSignal[i] = True
    return bearSignal

def get_exchange(account):
    if account['exchange'] == 'bybit':
        return Bybit(account['api_key'], account['api_secret'])
    if account['exchange'] == 'hyper':
        return Hyper(account['api_key'], account['api_secret'])

def get_minqty(coin):
    with open('coins.json') as f:
        data = f.read().strip()

    list = json.loads(data)
    for item in list['result']:
        if item['name'] == f'{coin}USDT':
            minqty = str(float(item['lot_size_filter']['min_trading_qty']))
            break

    return len(minqty.split('.')[1])

def set_minqty(coin):
    with open('coins.json') as f:
        data = f.read().strip()

    list = json.loads(data)
    for item in list['result']:
        if item['name'] == f'{coin}USDT':
            minqty = str(float(item['lot_size_filter']['min_trading_qty']))
            break

    return minqty

def open_pos(exchange, user, conf, side, tp,sl, current_price_olhc=None):
    dep_exch = float(exchange.get_balance())
    #dep = dep_exch / 100 * conf['pos_perc_size']
    dep = dep_exch / 100 * 100
    try:
        current_price = float(exchange.get_current_price(conf['coin']))
    except Exception as e:
        current_price = current_price_olhc
    qty = dep/current_price
    roundC = get_minqty(conf['coin'])
    if get_minqty(conf['coin']) >=1 and conf['coin'] != 'BTC' and conf['coin'] != 'ETH':
        roundC=0
    qty = round(qty, roundC)

    if qty == 0:
        qty = set_minqty(conf['coin'])

    roundTPSL = len(str(current_price).split('.')[1])
    tp = round(tp, roundTPSL)
    sl = round(sl, roundTPSL)
    print(tp,sl)
    res = exchange.make_market_order(conf['coin'], side, qty, tp,sl)
    notifyer = Notifyer(user["tg_chat_id"])
    if exchange.api_error_flag:
        notifyer.send_error(extract_log(), exchange.api_error_msg)
    else:
        notifyer.send_open_pos(extract_log(), res)
    return None

def close_pos(exchange, user, coin, side):
    positions = exchange.get_open_positions(coin)
    if(len(positions) == 0): return None
    position = positions[0]
    qty = float(position['size'])
    if qty > 0:
        notifyer = Notifyer(user["tg_chat_id"])
        if position['side'] == 'Buy' and side == 'long':
            res = exchange.close_position(coin, qty, 'Sell')
            if exchange.api_error_flag:
                notifyer.send_error(extract_log(), exchange.api_error_msg)
            else:
                notifyer.send_open_pos(extract_log(), res)
        elif position['side'] == 'Sell' and side == 'short':
            res = exchange.close_position(coin, qty, 'Buy')
            if exchange.api_error_flag:
                notifyer.send_error(extract_log(), exchange.api_error_msg)
            else:
                notifyer.send_open_pos(extract_log(), res)

db = Database(config.db_name)
db.connect()