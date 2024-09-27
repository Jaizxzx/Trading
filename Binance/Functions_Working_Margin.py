import logging
from binance.client import Client
from binance.lib.utils import config_logging
import time
from keys import api , secret

# Configure logging
#config_logging(logging, logging.DEBUG)

# Replace these with your actual API key and secret
api_key = api
api_secret = secret

# Initialize the client
client = Client(api_key, api_secret)


# Get isolated margin account information
response = client.get_isolated_margin_account(symbols="SUIUSDT")

# Extract and print the 'free' balance for each asset
for asset in response['assets']:
    quote_asset = asset['quoteAsset']
    symbol = asset['symbol']
    free_balance = quote_asset['free']
    asset_symbol_balance = quote_asset['asset']
    print(f"Symbol: {symbol}, Free Balance: {free_balance} in asset {asset_symbol_balance}")

'''
loan_response_borrow = client.create_margin_loan(symbol='SUIUSDT', asset='USDT', amount='8',isIsolated='TRUE',recvWindow=60000)

print(loan_response_borrow)

time.sleep(2)
'''

'''
loan_response_repay = client.repay_margin_loan(symbol='SUIUSDT', asset='USDT', amount='8',isIsolated='TRUE',recvWindow=60000)

print(loan_response_repay)
'''
'''
order_create_buy = client.create_margin_order(symbol='SUIUSDT', side='BUY', type='MARKET', quantity=4, isIsolated='TRUE',recvWindow=60000)
print(order_create_buy)
'''
order_create_take_profit = client.create_margin_order(symbol='SUIUSDT', side='SELL', type='TAKE_PROFIT_LIMIT', quantity=4, price=1.8, isIsolated='TRUE',recvWindow=60000,stopPrice = 1.4, timeInForce='GTC')
print(order_create_take_profit)

'''
order_create_stop_loss = client.create_margin_order(symbol='SUIUSDT', side='SELL', type='STOP_LOSS_LIMIT', quantity=4, price=1.4, isIsolated='TRUE',recvWindow=60000,stopPrice = 1.4, timeInForce='GTC')
print(order_create_stop_loss)
'''


time.sleep(50)

'''
order_create_sell = client.create_margin_order(symbol='SUIUSDT', side='SELL', type='MARKET', quantity=4.995, isIsolated='TRUE',recvWindow=60000)

print(order_create_sell)
'''


#time.sleep(20)
'''
order_cancel = client.cancel_margin_order(symbol='SUIUSDT', orderId=order_create_buy['orderId], isIsolated='TRUE',recvWindow=60000)
print(order_cancel)
order_cancel = client.cancel_margin_order(symbol='SUIUSDT', orderId=order_create_stop_loss['orderId'], isIsolated='TRUE',recvWindow=60000)
print(order_cancel)
order_cancel = client.cancel_margin_order(symbol='SUIUSDT', orderId=order_create_take_profit['orderId'], isIsolated='TRUE',recvWindow=60000)
print(order_cancel)

time.sleep(2)
'''
'''
loan_response_repay = client.repay_margin_loan(symbol='SUIUSDT', asset='USDT', amount='8',isIsolated='TRUE',recvWindow=60000)

print(loan_response_repay)
'''