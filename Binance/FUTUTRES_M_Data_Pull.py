from binance.um_futures import UMFutures
from datetime import datetime, timedelta, timezone
import pytz
import time
from binance.error import ClientError
# Initialize the UMFutures client
um_futures_client = UMFutures()

# Set the parameters
pair = "SUIUSDT"
contract_type = "PERPETUAL"
interval = "5m"

# Set the New York timezone
ny_timezone = pytz.timezone("America/New_York")
print(f"Using timezone: {ny_timezone}")

# Set the daily start and end times (in NY time)
start_time = datetime.strptime("00:05", "%H:%M").time() # Start 5 minutes after market open e.g this was intended to start at 08:00
end_time = datetime.strptime("01:06", "%H:%M").time() # Add 6 minute to end time to avoid missing the last candle e.g this was intended to close at 08:20

def print_candle(candle):
    utc_time = datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
    ny_time = utc_time.astimezone(ny_timezone)
    print(f"Candle start (NY): {ny_time}, Open: {candle[1]}, High: {candle[2]}, Low: {candle[3]}, Close: {candle[4]}")

def is_within_trading_hours(current_time):
    return start_time <= current_time.time() <= end_time

def wait_for_next_session(current_time):
    next_day = current_time.date() + timedelta(days=1)
    next_session_start = datetime.combine(next_day, start_time).replace(tzinfo=ny_timezone)
    wait_seconds = (next_session_start - current_time).total_seconds()
    print(f"Outside trading hours. Waiting until next session at {next_session_start.strftime('%Y-%m-%d %H:%M:%S')} NY time")
    time.sleep(wait_seconds)

def main_loop():
    while True:
        now = datetime.now(ny_timezone)
        
        if not is_within_trading_hours(now):
            wait_for_next_session(now)
            continue

        try:
            last_candle_start = now - timedelta(minutes=now.minute % 5 + 5, seconds=now.second, microseconds=now.microsecond)
            start_timestamp = int(last_candle_start.timestamp() * 1000)

            klines = um_futures_client.continuous_klines(
                pair=pair, 
                contractType=contract_type, 
                interval=interval, 
                limit=1,
                endTime=start_timestamp
            )

            if klines:
                print("\nLast completed 5-minute candle:")
                print_candle(klines[0])
            else:
                print("No data received")

            next_candle_end = now + timedelta(minutes=5 - now.minute % 5, seconds=-now.second, microseconds=-now.microsecond)
            sleep_time = (next_candle_end - now).total_seconds() + 2

            if is_within_trading_hours(next_candle_end):
                print(f"Waiting for {sleep_time:.2f} seconds until next candle completes...")
                time.sleep(sleep_time)
            else:
                print("Reached end of trading hours for today.")
                wait_for_next_session(now)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print(f"Script will run daily from {start_time} to {end_time} NY time")
    main_loop()