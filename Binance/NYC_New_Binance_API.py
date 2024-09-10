import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
import pytz

# Initialize Binance client and API Keys
api_key = '' # API KEYS REMOVE BEFORE SHARING
api_secret = '' # API SECRET KEY REMOVE BEFORE SHARING
client = Client(api_key, api_secret)

# Trading parameters
symbol = 'BTCUSDT'
timeframe = Client.KLINE_INTERVAL_5MINUTE

# New York timezone
ny_tz = pytz.timezone('America/New_York')

# Hardcoded date range
START_DATE = datetime(2024, 9, 8)
END_DATE = datetime(2024, 9, 9)

def get_ny_midnight(date):
    # Create a timezone-naive datetime at midnight
    midnight = datetime.combine(date, datetime.min.time())
    # Localize it to New York time
    return ny_tz.localize(midnight, is_dst=None)

def get_candles(start_time):
    # Convert NY time to UTC for Binance API
    start_time_utc = start_time.astimezone(pytz.UTC)
    end_time_utc = start_time_utc + timedelta(minutes=10)  # Get 2 5-minute candles
    
    klines = client.get_klines(
        symbol=symbol,
        interval=timeframe,
        startTime=int(start_time_utc.timestamp() * 1000),
        endTime=int(end_time_utc.timestamp() * 1000),
        limit=2
    )
    return [
        {
            'open_time': datetime.fromtimestamp(kline[0] / 1000, tz=pytz.UTC).astimezone(ny_tz),
            'open': float(kline[1]),
            'high': float(kline[2]),
            'low': float(kline[3]),
            'close': float(kline[4])
        }
        for kline in klines
    ]

def print_candle_info(candle, candle_number):
    print(f"Candle {candle_number}:")
    print(f"Time (NY): {candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Open: {candle['open']}")
    print(f"High: {candle['high']}")
    print(f"Low: {candle['low']}")
    print(f"Close: {candle['close']}")
    print("------------------------")

def analyze_candles(candles):
    if len(candles) < 2:
        print("Not enough candles to analyze.")
        return

    first_candle = candles[0]
    second_candle = candles[1]

    print_candle_info(first_candle, 1)
    print_candle_info(second_candle, 2)

    if second_candle['close'] > first_candle['close']:
        stop_loss = first_candle['open'] - 1  # 1 point below the first candle's open
        stop_loss_distance = first_candle['open'] - stop_loss
        take_profit = first_candle['open'] + (2 * stop_loss_distance)

        print("Signal: BUY")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")
        print("------------------------")
    else:
        print("No buy signal. Second candle close is not higher than first candle close.")

def main():
    current_date = START_DATE
    while current_date <= END_DATE:
        ny_midnight = get_ny_midnight(current_date)
        print(f"\nAnalyzing candles for {ny_midnight.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        try:
            candles = get_candles(ny_midnight)
            
            if len(candles) < 2:
                print(f"Not enough candles available for {ny_midnight.strftime('%Y-%m-%d %H:%M:%S %Z')}.")
            else:
                analyze_candles(candles)
        
        except Exception as e:
            print(f"An error occurred: {e}")
        
        current_date += timedelta(days=1)
        time.sleep(1)  # Add a small delay to avoid hitting rate limits

if __name__ == "__main__":
    main()