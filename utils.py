import requests
import pandas as pd
import json

import config
from db import Database
from bybit import Bybit
from notifyer import Notifyer

users = {}
accounts = {}

log_tmp = ''

def log(message: str)-> None:
    global log_tmp
    log_tmp += message + '\n'
    print(message)

def extract_log():
    global log_tmp
    tmp_log = log_tmp
    log_tmp = ''
    return tmp_log

def find_configs(tf: str) -> list:
    res = db.execute_query(f'select * from configs where tf = "{tf}"')
    configs = []
    for row in res:
        config = {
            "id": row[0],
            "user_id": row[1],
            "account_id": row[2],
            "coin": row[3],
            "sl_on": row[4],
            "tp_on": row[5],
            "sl": row[6],
            "tp": row[7],
            "filter_ema": row[8],
            "fast_ema": row[9],
            "slow_ema": row[10],
            "filter_ema_on": row[11],
            "enable_long": row[12],
            "enable_short": row[13],
            "low_rsi": row[14],
            "high_rsi": row[15],
            "rsi_protection_for_long": row[16],
            "rsi_protection_for_short": row[17],
            "rsi_tp_long": row[18],
            "rsi_tp_short": row[19],
            "force_rsi_tp_for_long": row[20],
            "force_rsi_tp_for_short": row[21],
            "tf": row[22]
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

def get_ohlc(conf):
    limit = conf["filter_ema"] + 50;
    response = requests.get(f'https://fapi.binance.com/fapi/v1/klines?symbol={conf["coin"]}USDT&interval={conf["tf"]}&limit={limit}')
    kline = response.json()
    ohlc = []
    for line in kline:
        data = {"open": line[1],
                "high": line[2],
                "low": line[3],
                "close": line[4]}
        ohlc.append(data)
    return ohlc

def calculate_ema(ohlc, period):
    prices = []
    for line in ohlc:
        prices.append(line["close"])
    prices_series = pd.Series(prices)
    ema = prices_series.ewm(span=period, adjust=False).mean()
    return ema.tolist()

def calculate_rsi(ohlc, period):
    prices = []
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
    return rsi.tolist()

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

def open_pos(exchange, user, coin, side):
    dep = float(exchange.get_balance())
    current_price = float(exchange.get_current_price(coin))
    qty = dep/current_price
    qty = round(qty, get_minqty(coin))
    if qty == 0:
        qty = set_minqty(coin)
    res = exchange.make_market_order(coin, side, qty)
    notifyer = Notifyer(user["tg_chat_id"])
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
            notifyer.send_open_pos(extract_log(), res)
        elif position['side'] == 'Sell' and side == 'short':
            res = exchange.close_position(coin, qty, 'Buy')
            notifyer.send_open_pos(extract_log(), res)

db = Database(config.db_name)
db.connect()