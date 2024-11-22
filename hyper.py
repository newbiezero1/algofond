from datetime import datetime

import eth_account
from eth_account.signers.local import LocalAccount

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

class Hyper:
    """Class for work with bybit"""

    api_key = None
    api_secret = None

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_error_flag = False
        self.api_error_msg = ''
        self.address, self.info, self.exchange = self.setup()

    def setup(self, base_url=None, skip_ws=False):
        account: LocalAccount = eth_account.Account.from_key(self.api_secret)
        address = self.api_key
        if address == "":
            address = account.address
        print("Running with account address:", address)
        if address != account.address:
            print("Running with agent address:", account.address)
        info = Info(base_url, skip_ws)
        user_state = info.user_state(address)
        spot_user_state = info.spot_user_state(address)
        margin_summary = user_state["marginSummary"]
        if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
            print("Not running the example because the provided account has no equity.")
            url = info.base_url.split(".", 1)[1]
            error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {address} has a balance on {url}.\nIf address shown is your API wallet address, update the config to specify the address of your account, not the address of the API wallet."
            raise Exception(error_string)
        exchange = Exchange(account, base_url, account_address=address)

        return address, info, exchange


    def error(self, msg: str) -> None:
        self.api_error_flag = True
        self.api_error_msg = msg

    def get_balance(self) -> float:
        """Get USDT balance"""
        user_state = self.info.user_state(self.api_key)
        balance = float(user_state['marginSummary']['accountValue'])
        return balance

    def get_current_price(self, coin) -> None:
        tt = int(datetime.now().timestamp()) *1000
        data = self.info.candles_snapshot(coin, interval="1m", startTime=tt, endTime=tt)
        return data[0]['c']

    def get_open_positions(self, coin="USDT") -> list:
        """Get all open position"""
        user_state = self.info.user_state(self.api_key)
        pos_res = []

        for position in user_state["assetPositions"]:
            if position['position']['coin'] == coin:
                pos = position['position']
                pos['side'] = 'Buy'
                pos['size'] = float(pos['szi'])
                if float(pos['szi']) < 0:
                    pos['side'] = 'Sell'
                    pos['size'] = float(pos['szi']) *-1

                pos['avgPrice'] = pos['entryPx']
                pos_res.append(pos)

        return pos_res

    def make_market_order(self, coin, side, qty) -> dict:
        """Send market order"""
        pos_side = True
        if side == 'short':
            pos_side =False

        result = self.exchange.market_open(coin, pos_side, qty)
        result['result'] = result['status']
        return result

    def close_position(self, coin, qty, side):
        result = self.exchange.market_close(coin)
        result['result'] = result['status']
        return result
from datetime import datetime

import eth_account
from eth_account.signers.local import LocalAccount

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

class Hyper:
    """Class for work with bybit"""

    api_key = None
    api_secret = None

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_error_flag = False
        self.api_error_msg = ''
        self.address, self.info, self.exchange = self.setup()

    def setup(self, base_url=None, skip_ws=False):
        account: LocalAccount = eth_account.Account.from_key(self.api_secret)
        address = self.api_key
        if address == "":
            address = account.address
        print("Running with account address:", address)
        if address != account.address:
            print("Running with agent address:", account.address)
        info = Info(base_url, skip_ws)
        user_state = info.user_state(address)
        spot_user_state = info.spot_user_state(address)
        margin_summary = user_state["marginSummary"]
        if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
            print("Not running the example because the provided account has no equity.")
            url = info.base_url.split(".", 1)[1]
            error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {address} has a balance on {url}.\nIf address shown is your API wallet address, update the config to specify the address of your account, not the address of the API wallet."
            raise Exception(error_string)
        exchange = Exchange(account, base_url, account_address=address)

        return address, info, exchange


    def error(self, msg: str) -> None:
        self.api_error_flag = True
        self.api_error_msg = msg

    def get_balance(self) -> float:
        """Get USDT balance"""
        user_state = self.info.user_state(self.api_key)
        balance = float(user_state['marginSummary']['accountValue'])
        return balance

    def get_current_price(self, coin) -> None:
        tt = int(datetime.now().timestamp()) *1000
        data = self.info.candles_snapshot(coin, interval="1m", startTime=tt, endTime=tt)
        return data[0]['c']

    def get_open_positions(self, coin="USDT") -> list:
        """Get all open position"""
        user_state = self.info.user_state(self.api_key)
        pos_res = []

        for position in user_state["assetPositions"]:
            if position['position']['coin'] == coin:
                pos = position['position']
                pos['side'] = 'Buy'
                pos['size'] = float(pos['szi'])
                if float(pos['szi']) < 0:
                    pos['side'] = 'Sell'
                    pos['size'] = float(pos['szi']) *-1

                pos['avgPrice'] = pos['entryPx']
                pos_res.append(pos)

        return pos_res

    def make_market_order(self, coin, side, qty) -> dict:
        """Send market order"""
        pos_side = True
        if side == 'short':
            pos_side =False

        result = self.exchange.market_open(coin, pos_side, qty)
        result['result'] = result['status']
        return result

    def close_position(self, coin, qty, side):
        result = self.exchange.market_close(coin)
        result['result'] = result['status']
        return result
