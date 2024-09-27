import logging
from binance.client import Client
from binance.lib.utils import config_logging
import time
from binance.um_futures import UMFutures
from binance.error import ClientError
from keys import api , secret

# Configure logging
#config_logging(logging, logging.DEBUG)

# Replace these with your actual API key and secret
api_key = api
api_secret = secret
client = UMFutures(api_key, api_secret)

def get_balance_usdt():
    try:
        response = client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['balance'])

    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

    # we need to get balance to check if the connection is good, or you have all the needed permissions
balance = get_balance_usdt()
if balance == None:
    print('Cant connect to API. Check IP, restrictions or wait some time')
if balance != None:
    print("My balance is: ", balance, " USDT")
#order_normal = client.new_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=0.001, recvWindow=60000)


tp_price = 1.5
sl_price = 1.3
leverage = 5
type = 'ISOLATED'  # type is 'ISOLATED' or 'CROSS'
qty = 7
symbol = 'SUIUSDT'

resp1 = client.new_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty, leverage=leverage,tp_price=tp_price,sl_price=sl_price)
print(symbol, 'BUY', "placing order")
print(resp1)
time.sleep(2)

resp2 = client.new_order(symbol=symbol, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price,closePosition=True)
print(resp2)
time.sleep(2)
resp3 = client.new_order(symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                         stopPrice=tp_price,closePosition=True)
print(resp3)
