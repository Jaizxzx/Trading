import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
import pytz

# Initialize Binance client and API Keys
api_key = 'pr5GIjVdQbms8xLJhjB4aOD1FSuPTKqoy8syXf7cVYYSA0r31rgJ9Fz9nr7ok0Bv'  # Replace with your actual API key
api_secret = 'DDRDDTHqHAQQTX5D5vNxBxnOlU1RvjS81otZUPUAgUaSZw2i32uwOJ6ACYqTzxcR'  # Replace with your actual API secret
client = Client(api_key, api_secret)

# Trading parameters
symbol = 'SUIUSDT'
timeframe = Client.KLINE_INTERVAL_5MINUTE

# New York timezone
ny_tz = pytz.timezone('America/New_York')

def get_ny_midnight(date):
    midnight = datetime.combine(date, datetime.min.time())
    return ny_tz.localize(midnight, is_dst=None)

def get_candles(start_time):
    start_time_utc = start_time.astimezone(pytz.UTC)
    end_time_utc = start_time_utc + timedelta(minutes=5)
    
    klines = client.get_klines(
        symbol=symbol,
        interval=timeframe,
        startTime=int(start_time_utc.timestamp() * 1000),
        endTime=int(end_time_utc.timestamp() * 1000),
        limit=1
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

def print_candle_info(candle):
    print(f"Time (NY): {candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Open: {candle['open']}")
    print(f"High: {candle['high']}")
    print(f"Low: {candle['low']}")
    print(f"Close: {candle['close']}")
    print("------------------------")

def analyze_candles(first_candle, second_candle, current_position, moves):
    max_moves = 2
    action_taken = False
    action_time = None
    stop_loss = None
    take_profit = None

    if moves >= max_moves:
        return current_position, moves, action_taken, action_time, stop_loss, take_profit

    if current_position == "Long":
        # Check for Flip Short
        if second_candle['low'] < first_candle['low']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Flip Short")
            print_candle_info(second_candle)
            open_price = first_candle['low']
            stop_loss = first_candle['high']
            take_profit = open_price - (stop_loss - open_price)
            print(f"Open Price (Limit Order): {open_price}")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("------------------------")
            return "Short", moves + 1, True, action_time, stop_loss, take_profit
    elif current_position == "Short":
        # Check for Flip Long
        if second_candle['high'] > first_candle['high']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Flip Long")
            print_candle_info(second_candle)
            open_price = first_candle['high']
            stop_loss = first_candle['low']
            take_profit = open_price + (open_price - stop_loss)
            print(f"Open Price (Limit Order): {open_price}")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("------------------------")
            return "Long", moves + 1, True, action_time, stop_loss, take_profit
    else:  # No position yet
        if second_candle['close'] > first_candle['close']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Initial Long")
            print_candle_info(first_candle)
            print_candle_info(second_candle)
            open_price = second_candle['close']
            stop_loss = first_candle['low']
            take_profit = open_price + 2 * (open_price - stop_loss)
            print(f"Open Price (Limit Order): {open_price}")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("------------------------")
            return "Long", moves + 1, True, action_time, stop_loss, take_profit
        elif second_candle['close'] < first_candle['close']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Initial Short")
            print_candle_info(first_candle)
            print_candle_info(second_candle)
            open_price = second_candle['close']
            stop_loss = first_candle['high']
            take_profit = open_price - 2 * (stop_loss - open_price)
            print(f"Open Price (Limit Order): {open_price}")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("------------------------")
            return "Short", moves + 1, True, action_time, stop_loss, take_profit
    
    return current_position, moves, action_taken, action_time, stop_loss, take_profit

def check_tp_sl(candle, position, stop_loss, take_profit):
    if position == "Long":
        if candle['high'] >= take_profit:
            return "TP", candle
        elif candle['low'] <= stop_loss:
            return "SL", candle
    elif position == "Short":
        if candle['low'] <= take_profit:
            return "TP", candle
        elif candle['high'] >= stop_loss:
            return "SL", candle
    return None, None

def run_trading_session(trading_start, trading_end):
    print(f"Trading window: {trading_start.strftime('%H:%M:%S')} - {trading_end.strftime('%H:%M:%S')} NY time")
    
    try:
        current_time = trading_start
        first_candle = get_candles(current_time)[0]
        current_time += timedelta(minutes=5)
        second_candle = get_candles(current_time)[0]
        
        current_position = None
        moves = 0
        stop_loss = None
        take_profit = None
        trading_allowed = True
        
        while current_time < trading_end and moves < 2 and trading_allowed:
            new_candle = get_candles(current_time)[0]
            
            if current_position:
                result, hit_candle = check_tp_sl(new_candle, current_position, stop_loss, take_profit)
                if result == "TP":
                    print(f"\nTrade closed due to Take Profit")
                    print(f"Closing Time (NY): {hit_candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print_candle_info(hit_candle)
                    trading_allowed = False
                    print("Trading stopped for the day.")
                    break
                elif result == "SL":
                    print(f"\nStop Loss hit - Flipping position")
                    print(f"Time (NY): {hit_candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print_candle_info(hit_candle)
                    # Flip the position
                    current_position = "Short" if current_position == "Long" else "Long"
                    first_candle = second_candle
                    second_candle = new_candle
                    moves += 1  # Increment moves as we're entering a new trade
                    if moves >= 2:
                        print("Maximum number of moves reached after stop loss. Trading stopped for the day.")
                        break
                    continue  # Skip to the next iteration to analyze the flipped position
            
            new_position, new_moves, action_taken, action_time, new_stop_loss, new_take_profit = analyze_candles(second_candle, new_candle, current_position, moves)
            
            if action_taken:
                current_position = new_position
                moves = new_moves
                stop_loss = new_stop_loss
                take_profit = new_take_profit
                first_candle = second_candle
                second_candle = new_candle
            
            current_time += timedelta(minutes=5)
            time.sleep(1)  # Add a small delay to avoid hitting rate limits
        
        if moves == 2:
            print("Maximum number of moves reached for the day.")
        elif trading_allowed:
            print("Trading window closed for the day.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    while True:
        current_time = datetime.now(ny_tz)
        current_date = current_time.date()
        ny_midnight = get_ny_midnight(current_date)
        
        # If it's past midnight, wait for the next day
        if current_time > ny_midnight + timedelta(hours=1):
            next_midnight = ny_midnight + timedelta(days=1)
            wait_time = (next_midnight - current_time).total_seconds()
            print(f"Waiting for next trading day. Next session starts in {wait_time/3600:.2f} hours.")
            time.sleep(wait_time)
            continue
        
        # If it's before midnight, wait until midnight
        if current_time < ny_midnight:
            wait_time = (ny_midnight - current_time).total_seconds()
            print(f"Waiting for today's trading session. Session starts in {wait_time/3600:.2f} hours.")
            time.sleep(wait_time)
        
        print(f"\nStarting trading session for {ny_midnight.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        trading_start = ny_midnight
        trading_end = trading_start + timedelta(hours=1)
        
        run_trading_session(trading_start, trading_end)

if __name__ == "__main__":
    main()