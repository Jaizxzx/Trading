import csv
import json
import os
from datetime import datetime

import pandas as pd
from binance.client import Client

# init
api_key = '' # Api Key 
api_secret = '' #Secret Access key

client = Client(api_key, api_secret)

## main

# valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

# Set specific start date and time
start_date = '03-09-2024 00:00:00'  # format: dd-mm-yyyy hh:mm:ss
start_timestamp = int(datetime.strptime(start_date, '%d-%m-%Y %H:%M:%S').timestamp() * 1000)

# request historical candle (or klines) data
bars = client.get_historical_klines('BTCUSDT', '5m', start_timestamp, limit=100)
# print(bars)

# Convert timestamp to readable format
for bar in bars:
    bar[0] = datetime.fromtimestamp(bar[0] / 1000).strftime('%d%m%Y %H%M%S')
'''
# option 1 - save to file using json method - this will retain Python format (list of lists)
with open('btc_bars.json', 'w') as e:
    json.dump(bars, e)
'''
'''# option 2 - save as CSV file using the csv writer library
with open('btc_bars.csv', 'w', newline='') as f:
    wr = csv.writer(f)
    for line in bars:
        wr.writerow(line)

# option 3 - save as CSV file without using a library. Shorten to just date, open, high, low, close
with open('btcusdt_ohlc.csv', 'w') as d:
    for line in bars:
        d.write(f'{line[0]}, {line[1]}, {line[2]}, {line[3]}, {line[4]}\n')'''

# delete unwanted data - just keep date, open, high, low, close
for line in bars:
    del line[5:]

# option 4 - create a Pandas DataFrame and export to CSV
btc_df = pd.DataFrame(bars, columns=['date', 'open', 'high', 'low', 'close'])
btc_df.set_index('date', inplace=True)
print(btc_df.head())
# export DataFrame to csv
btc_df.to_csv('btcusdt_ohlc.csv')