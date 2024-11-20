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
    ohlc = utils.get_ohlc(conf)