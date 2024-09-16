'''import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging


api_key, api_secret = 'pr5GIjVdQbms8xLJhjB4aOD1FSuPTKqoy8syXf7cVYYSA0r31rgJ9Fz9nr7ok0Bv','DDRDDTHqHAQQTX5D5vNxBxnOlU1RvjS81otZUPUAgUaSZw2i32uwOJ6ACYqTzxcR'

client = Client(api_key, api_secret)
print(client.margin_transfer_history(asset="USDT"))'''

from binance.client import Client
from binance.exceptions import BinanceAPIException

# Initialize the Binance client
# Replace 'your_api_key' and 'your_api_secret' with your actual Binance API credentials
client = Client('pr5GIjVdQbms8xLJhjB4aOD1FSuPTKqoy8syXf7cVYYSA0r31rgJ9Fz9nr7ok0Bv', 'DDRDDTHqHAQQTX5D5vNxBxnOlU1RvjS81otZUPUAgUaSZw2i32uwOJ6ACYqTzxcR')

def get_all_isolated_margin_balances():
    try:
        # Fetch isolated margin account information
        account_info = client.get_isolated_margin_account()
        
        balances = {}
        for asset in account_info['assets']:
            symbol = asset['symbol']
            base_asset = asset['baseAsset']['asset']
            quote_asset = asset['quoteAsset']['asset']
            
            base_balance = float(asset['baseAsset']['free']) + float(asset['baseAsset']['locked'])
            quote_balance = float(asset['quoteAsset']['free']) + float(asset['quoteAsset']['locked'])
            
            balances[symbol] = {
                base_asset: base_balance,
                quote_asset: quote_balance
            }
        
        return balances
    
    except BinanceAPIException as e:
        return f"An error occurred: {e}"

# Get and print the balances
balances = get_all_isolated_margin_balances()
if isinstance(balances, dict):
    for symbol, balance in balances.items():
        print(f"Isolated Margin Balance for {symbol}:")
        for asset, amount in balance.items():
            print(f"  {asset}: {amount}")
        print()
else:
    print(balances)  # This will print the error message if an exception occurred