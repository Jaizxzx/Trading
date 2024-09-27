from binance.um_futures import UMFutures
from datetime import datetime, timedelta, timezone
import pytz
import time
from binance.error import ClientError
from keys import api, secret
# Initialize the UMFutures client
api_key = api
api_secret = secret
um_futures_client = UMFutures(api_key, api_secret)

# Set the parameters
pair = "SUIUSDT"
contract_type = "PERPETUAL"
interval = "5m"
qty = 7
leverage = 5

order = um_futures_client.get_orders(
    symbol='SUIUSDT',
    orderId='8292671646')
print(order)