"""Module for work with bybit"""
from pybit.unified_trading import HTTP



class Bybit:
    """Class for work with bybit"""

    def __init__(self, api_key, api_secret):
        self.session = HTTP(api_key=api_key, api_secret=api_secret)
        self.api_error_flag = False
        self.api_error_msg = ''

    def error(self, msg: str) -> None:
        self.api_error_flag = True
        self.api_error_msg = msg

    def get_balance(self) -> float:
        """Get USDT balance"""
        wallet_balance = self.session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        if wallet_balance["retCode"] != 0:
            self.error(f'Error getting balance')
            return 0
        balance = float(wallet_balance["result"]["list"][0]["coin"][0]["walletBalance"])
        return balance

    def get_current_price(self, coin) -> None:
        """Get symbol current price"""
        data = self.session.get_mark_price_kline(symbol=f'{coin}USDT', category="linear", interval=1, limit=1)
        if data["retCode"] != 0:
            self.error(f'Cant receive market data: *{coin}*')
        return float(data["result"]["list"][0][4])

    def get_open_positions(self, coin="USDT") -> list:
        """Get all open position"""
        try:
            result = self.session.get_positions(category="linear", baseCoin=coin, settleCoin='USDT')
        except Exception as e:
            self.error(f'Error get position: {e}')
        if result["retCode"] != 0:
            self.error(f'Warning get position: {result["retMsg"]}')
        return result["result"]["list"]

    def make_market_order(self, coin, side, qty) -> dict:
        """Send market order"""
        pos_side = 'Buy'
        if side == 'short':
            pos_side = 'Sell'
        order = {"symbol": f'{coin}USDT', "side": pos_side, "orderType": "Market"}
        order['qty'] = qty
        try:
            result = self.session.place_order(category="linear",
                                              symbol=order["symbol"],
                                              side=order["side"],
                                              orderType=order["orderType"],
                                              qty=order["qty"])
        except Exception as e:
            self.error(e)
            return {}
        if result["retCode"] != 0:
            self.error(result["retMsg"])
            return {}
        order["result"] = result["retMsg"]
        order["orderId"] = result["result"]["orderId"]
        order["price"] = "market"
        return order

    def close_position(self, coin, qty, side):
        order = {"symbol": f'{coin}USDT', "side": side, "orderType": "Market"}
        order['qty'] = qty
        try:
            result = self.session.place_order(category="linear",
                                              symbol=order["symbol"],
                                              side=order["side"],
                                              orderType=order["orderType"],
                                              qty=order["qty"],
                                              reduceOnly=True)
        except Exception as e:
            self.error(e)
            return {}
        if result["retCode"] != 0:
            self.error(result["retMsg"])
            return {}
        order["result"] = result["retMsg"]
        order["orderId"] = result["result"]["orderId"]
        order["price"] = "market"
        return order
