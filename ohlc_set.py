import config
from db import Database
import requests
from datetime import datetime

def insert_ohlc(coin, interval, limit,date_start):
    response = requests.get(
        f'https://fapi.binance.com/fapi/v1/klines?symbol={coin}USDT&interval={interval}&limit={limit}&startTime={date_start}')
    ohlc = response.json()
    start = ohlc[0][0]
    end = ohlc[-1][0]
    db.execute_query(
        f'insert into ohlc (coin, tf, data, start, end) values ("{coin}", "{tf}",' + "'" + response.text + "'" + f', "{start}", "{end}")')

db = Database(config.db_name)
db.connect()

ohlc_cache = {}
db.execute_query(f'delete from ohlc ')
res = db.execute_query(f'select coin,tf from configs ')
for config in res:
    coin = config[0]
    tf = config[1]
    cache_key = f'{coin}_tf'
    if cache_key in ohlc_cache:
        continue
    limit = 1500;
    interval = tf
    umnozhitel = 5
    if tf == '5m':
        umnozhitel = 5
    if tf == '10m':
        umnozhitel = 5
    if tf == '15m':
        umnozhitel = 15
    if tf == '30m':
        umnozhitel = 30
    if tf == '1h':
        umnozhitel = 60
    if tf == '4h':
        umnozhitel = 240

    if tf == '10m':
        interval = '5m'
    unix_time = int(datetime.now().timestamp())
    date_start = (unix_time - (limit * umnozhitel * 60) * 11) * 1000
    insert_ohlc(coin, interval, limit,date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 10) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 9) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 8) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 7) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 6) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 5) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 4) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 3) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    date_start = (unix_time - (limit * umnozhitel * 60) * 2) * 1000
    insert_ohlc(coin, interval, limit, date_start)
    ohlc_cache[cache_key] = True
