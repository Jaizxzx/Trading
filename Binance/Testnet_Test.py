import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
import pytz

# Initialize Binance testnet client
api_key = 'qpUumn3rfEvFXywYS2DCq4rfndL1tjgP9hapNXX2blf6PmAMInRTqhz0J2B5T58o'  # Replace with your Binance testnet API key
api_secret = 'V5H8jFNqzKb6wHqWrIljXrr8Y5KjguSr23oNCLQLq6PoIyrtiyUWIkOrl77dd5n0'  # Replace with your Binance testnet API secret
client = Client(api_key, api_secret, testnet=True)

# Trading parameters
symbol = 'SUIUSDT'
timeframe = Client.KLINE_INTERVAL_5MINUTE
quantity = 100  # Adjust this based on your testnet account balance and the symbol's minimum order size

# New York timezone
ny_tz = pytz.timezone('America/New_York')

# Hardcoded date range
START_DATE = datetime(2024, 9, 8)
END_DATE = datetime(2024, 9, 12)

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

def get_symbol_info(symbol):
    info = client.get_symbol_info(symbol)
    price_filter = next(filter(lambda f: f['filterType'] == 'PRICE_FILTER', info['filters']))
    lot_size_filter = next(filter(lambda f: f['filterType'] == 'LOT_SIZE', info['filters']))
    
    tick_size = float(price_filter['tickSize'])
    step_size = float(lot_size_filter['stepSize'])
    
    price_precision = len(str(tick_size).split('.')[1])
    quantity_precision = len(str(step_size).split('.')[1])
    
    return price_precision, quantity_precision

def round_step_size(quantity, step_size):
    return round(quantity - quantity % step_size, len(str(step_size).split('.')[1]))

price_precision, quantity_precision = get_symbol_info(symbol)

def round_price(price):
    return round(price, price_precision)

def place_order(side, order_type, price=None, stop_loss=None, take_profit=None):
    try:
        rounded_quantity = round_step_size(quantity, 10 ** -quantity_precision)
        
        if order_type == ORDER_TYPE_MARKET:
            order = client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=rounded_quantity
            )
        elif order_type == ORDER_TYPE_LIMIT:
            order = client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=rounded_quantity,
                price=round_price(price)
            )
        
        print(f"Main order placed: {order}")
        
        # Place stop loss order
        if stop_loss:
            stop_loss_side = SIDE_SELL if side == SIDE_BUY else SIDE_BUY
            sl_order = client.create_order(
                symbol=symbol,
                side=stop_loss_side,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=rounded_quantity,
                stopPrice=round_price(stop_loss),
                price=round_price(stop_loss)  # Set limit price same as stop price
            )
            print(f"Stop Loss order placed: {sl_order}")
        
        # Place take profit order
        if take_profit:
            take_profit_side = SIDE_SELL if side == SIDE_BUY else SIDE_BUY
            tp_order = client.create_order(
                symbol=symbol,
                side=take_profit_side,
                type=ORDER_TYPE_TAKE_PROFIT_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=rounded_quantity,
                stopPrice=round_price(take_profit),
                price=round_price(take_profit)  # Set limit price same as take profit price
            )
            print(f"Take Profit order placed: {tp_order}")
        
        return order
    except Exception as e:
        print(f"An error occurred while placing the order: {e}")
        return None

def analyze_candles(first_candle, second_candle, current_position, moves):
    max_moves = 2
    action_taken = False
    action_time = None
    stop_loss = None
    take_profit = None

    if moves >= max_moves:
        return current_position, moves, action_taken, action_time, stop_loss, take_profit

    if current_position == "Long":
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
            
            # Close long position
            place_order(SIDE_SELL, ORDER_TYPE_MARKET)
            # Open new short position with SL/TP
            place_order(SIDE_SELL, ORDER_TYPE_LIMIT, price=open_price, stop_loss=stop_loss, take_profit=take_profit)
            
            return "Short", moves + 1, True, action_time, stop_loss, take_profit
    elif current_position == "Short":
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
            
            # Close short position
            place_order(SIDE_BUY, ORDER_TYPE_MARKET)
            # Open new long position with SL/TP
            place_order(SIDE_BUY, ORDER_TYPE_LIMIT, price=open_price, stop_loss=stop_loss, take_profit=take_profit)
            
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
            
            # Place initial long position with SL/TP
            place_order(SIDE_BUY, ORDER_TYPE_LIMIT, price=open_price, stop_loss=stop_loss, take_profit=take_profit)
            
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
            
            # Place initial short position with SL/TP
            place_order(SIDE_SELL, ORDER_TYPE_LIMIT, price=open_price, stop_loss=stop_loss, take_profit=take_profit)
            
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

def main():
    global price_precision, quantity_precision
    price_precision, quantity_precision = get_symbol_info(symbol)
    current_date = START_DATE
    while current_date <= END_DATE:
        ny_midnight = get_ny_midnight(current_date)
        print(f"\nAnalyzing candles for {ny_midnight.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        trading_start = ny_midnight
        trading_end = trading_start + timedelta(hours=1)
        
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
                        # Close position
                        place_order(SIDE_SELL if current_position == "Long" else SIDE_BUY, ORDER_TYPE_MARKET)
                        trading_allowed = False
                        print("Trading stopped for the day.")
                        break
                    elif result == "SL":
                        print(f"\nStop Loss hit - Flipping position")
                        print(f"Time (NY): {hit_candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        print_candle_info(hit_candle)
                        # Close current position
                        place_order(SIDE_SELL if current_position == "Long" else SIDE_BUY, ORDER_TYPE_MARKET)
                        # Flip the position
                        current_position = "Short" if current_position == "Long" else "Long"
                        first_candle = second_candle
                        second_candle = new_candle
                        moves += 1
                        if moves >= 2:
                            print("Maximum number of moves reached after stop loss. Trading stopped for the day.")
                            break
                        continue
                
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
        
        current_date += timedelta(days=1)

if __name__ == "__main__":
    main()