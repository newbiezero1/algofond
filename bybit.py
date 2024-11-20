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

    def get_open_positions(self, coin="USDT") -> list:
        """Get all open position"""
        try:
            result = self.session.get_positions(category="linear", baseCoin=coin, settleCoin='USDT')
        except Exception as e:
            self.error(f'Error get position: {e}')
        if result["retCode"] != 0:
            self.error(f'Warning get position: {result["retMsg"]}')
        return result["result"]["list"]