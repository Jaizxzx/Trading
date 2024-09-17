'''import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging


api_key, api_secret = '',''

client = Client(api_key, api_secret)
print(client.margin_transfer_history(asset="USDT"))'''

from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

# Your Testnet API Key and Secret
api_key = 'xG9dN7c3u703o27DHjr1N8KoUZ2WYhjB1hJ7uizdYfJwIq0OI8mR4PtVDXa5rAEF'
api_secret = 'xK4H9wh87e2Ues5XuyfxtHIcT37tCSI641cS75l5jqloF7HnJ4du8EfTuSyRGtGi'

# Initialize Binance Client for Testnet
client = Client(api_key, api_secret, testnet=True)

# Borrow USDT on Margin Account
def borrow_usdt(asset, amount,symbol):
    try:
        response = client.create_margin_loan(asset=asset, amount=amount, isIsolated=True, symbol=symbol)

        print(f"Borrowed {amount} {asset}. Response: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Repay USDT on Margin Account
def repay_usdt(asset, amount,symbol):
    try:
        response = client.repay_margin_loan(asset=asset, amount=amount,isIsolated=True, symbol=symbol)
        print(f"Repaid {amount} {asset}. Response: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Example Usage
borrow_usdt('SUIUSDT', 100,symbol='USDT')  # Borrow 100 USDT
repay_usdt('USDT', 100,symbol='USDT')   # Repay 100 USDT