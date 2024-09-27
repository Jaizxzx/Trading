import time
from datetime import datetime, timedelta
import argparse
from binance.client import Client
from binance.enums import *
from keys import api, secret
# Initialize Binance client
api_key = api
api_secret = secret
client = Client(api_key, api_secret)

# Trading parameters
symbol = 'BTCUSDT'
timeframe = Client.KLINE_INTERVAL_5MINUTE

# Date range configuration
# Set these variables to use a fixed date range in the code
# Format: 'YYYY-MM-DD'
# Set to None to use command-line arguments instead
START_DATE = '2024-09-08'
END_DATE = '2024-09-09'

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def get_candles(start_time, end_time=None):
    klines = client.get_klines(
        symbol=symbol,
        interval=timeframe,
        startTime=int(start_time.timestamp() * 1000),
        endTime=int(end_time.timestamp() * 1000) if end_time else None,
        limit=1000
    )
    return [
        {
            'open_time': kline[0],
            'open': float(kline[1]),
            'high': float(kline[2]),
            'low': float(kline[3]),
            'close': float(kline[4])
        }
        for kline in klines
    ]

def print_ohlc_and_signal(candle, signal):
    print(f"Time: {datetime.fromtimestamp(candle['open_time']/1000)}")
    print(f"Open: {candle['open']}")
    print(f"High: {candle['high']}")
    print(f"Low: {candle['low']}")
    print(f"Close: {candle['close']}")
    print(f"Signal: {signal}")
    print("------------------------")

def analyze_candles(candles):
    for i in range(1, len(candles)):
        first_candle = candles[i-1]
        second_candle = candles[i]
        
        if second_candle['close'] > first_candle['close']:
            stop_loss = first_candle['open'] * 0.999
            stop_loss_distance = second_candle['close'] - stop_loss
            take_profit = second_candle['close'] + (2 * stop_loss_distance)
            
            print_ohlc_and_signal(second_candle, "BUY")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("------------------------")
        elif second_candle['close'] < first_candle['close']:
            stop_loss = first_candle['open'] * 1.001
            stop_loss_distance = stop_loss - second_candle['close']
            take_profit = second_candle['close'] - (2 * stop_loss_distance)
            
            print_ohlc_and_signal(second_candle, "SELL")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("------------------------")

def main(start_date, end_date):
    current_date = start_date
    
    while current_date <= end_date:
        try:
            next_date = current_date + timedelta(days=1)
            candles = get_candles(current_date, next_date)
            
            if len(candles) < 2:
                print(f"Not enough candles available for {current_date.date()}. Moving to next day.")
                current_date = next_date
                continue
            
            print(f"Analyzing candles for {current_date.date()}")
            analyze_candles(candles)
            
            current_date = next_date
        
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60)  # Wait for 1 minute before retrying

if __name__ == "__main__":
    if START_DATE and END_DATE:
        start_date = parse_date(START_DATE)
        end_date = parse_date(END_DATE)
    else:
        parser = argparse.ArgumentParser(description="Analyze trading signals for a specified date range.")
        parser.add_argument("start_date", type=parse_date, help="Start date in YYYY-MM-DD format")
        parser.add_argument("end_date", type=parse_date, help="End date in YYYY-MM-DD format")
        
        args = parser.parse_args()
        start_date = args.start_date
        end_date = args.end_date
    
    if start_date > end_date:
        print("Error: Start date must be before or equal to end date.")
    else:
        main(start_date, end_date)