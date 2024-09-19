'''import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging


api_key, api_secret = '',''

client = Client(api_key, api_secret)
print(client.margin_transfer_history(asset="USDT"))'''

from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

# Your Testnet API Key and Secret
api_key = 'qpUumn3rfEvFXywYS2DCq4rfndL1tjgP9hapNXX2blf6PmAMInRTqhz0J2B5T58o'
api_secret = 'V5H8jFNqzKb6wHqWrIljXrr8Y5KjguSr23oNCLQLq6PoIyrtiyUWIkOrl77dd5n0'

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