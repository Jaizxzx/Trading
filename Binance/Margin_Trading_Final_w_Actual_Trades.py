import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
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

def get_current_price():
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def get_latest_candle():
    klines = client.get_klines(symbol=symbol, interval=timeframe, limit=1)
    return {
        'open_time': datetime.fromtimestamp(klines[0][0] / 1000, tz=pytz.UTC).astimezone(ny_tz),
        'open': float(klines[0][1]),
        'high': float(klines[0][2]),
        'low': float(klines[0][3]),
        'close': float(klines[0][4])
    }

def print_candle_info(candle):
    print(f"Time (NY): {candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Open: {candle['open']}")
    print(f"High: {candle['high']}")
    print(f"Low: {candle['low']}")
    print(f"Close: {candle['close']}")
    print("------------------------")

def get_account_balance():
    account_info = client.get_isolated_margin_account()
    for asset in account_info['assets']:
        if asset['symbol'] == symbol:
            base_asset = asset['baseAsset']['asset']
            quote_asset = asset['quoteAsset']['asset']
            base_balance = float(asset['baseAsset']['free'])
            quote_balance = float(asset['quoteAsset']['free'])
            return {base_asset: base_balance, quote_asset: quote_balance}
    return None

def borrow_margin(asset, amount):
    try:
        client.create_margin_loan(asset=asset, amount=amount, isIsolated=True, symbol=symbol)
        print(f"Borrowed {amount} {asset}")
    except BinanceAPIException as e:
        print(f"Failed to borrow: {e}")
        return False
    return True

def repay_margin(asset, amount):
    try:
        client.repay_margin_loan(asset=asset, amount=amount, isIsolated=True, symbol=symbol)
        print(f"Repaid {amount} {asset}")
    except BinanceAPIException as e:
        print(f"Failed to repay: {e}")
        return False
    return True

def place_order(side, quantity, price):
    try:
        order = client.create_margin_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=price,
            isIsolated=True
        )
        print(f"Placed {side} order: {quantity} at {price}")
        return order
    except BinanceAPIException as e:
        print(f"Failed to place order: {e}")
        return None

def analyze_candles(first_candle, second_candle, current_position):
    action_taken = False
    action_time = None
    stop_loss = None
    take_profit = None

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
            return "Short", True, action_time, stop_loss, take_profit
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
            return "Long", True, action_time, stop_loss, take_profit
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
            return "Long", True, action_time, stop_loss, take_profit
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
            return "Short", True, action_time, stop_loss, take_profit
    
    return current_position, action_taken, action_time, stop_loss, take_profit

def check_tp_sl(current_price, position, stop_loss, take_profit):
    if position == "Long":
        if current_price >= take_profit:
            return "TP"
        elif current_price <= stop_loss:
            return "SL"
    elif position == "Short":
        if current_price <= take_profit:
            return "TP"
        elif current_price >= stop_loss:
            return "SL"
    return None

def execute_trade(side, price):
    balance = get_account_balance()
    if not balance:
        print("Failed to get account balance")
        return False

    quote_asset = 'USDT'
    base_asset = 'SUI'
    quote_balance = balance[quote_asset] * 0.8  # 80% of current balance
    borrow_amount = quote_balance * 4  # Borrow 4x

    if not borrow_margin(quote_asset, borrow_amount):
        return False

    total_amount = quote_balance + borrow_amount
    quantity = total_amount / price
    
    order = place_order(side, quantity, price)
    if not order:
        repay_margin(quote_asset, borrow_amount)  # Repay if order failed
        return False

    return True

def close_position(side, price):
    balance = get_account_balance()
    if not balance:
        print("Failed to get account balance")
        return False

    base_asset = 'SUI'
    quote_asset = 'USDT'
    
    if side == 'SELL':
        quantity = balance[base_asset]
    else:  # 'BUY'
        quantity = balance[quote_asset] / price

    order = place_order(side, quantity, price)
    if not order:
        return False

    # Repay borrowed amount
    borrowed_balance = client.get_margin_loan_details(asset=quote_asset, isolatedSymbol=symbol)
    if borrowed_balance:
        repay_amount = float(borrowed_balance[0]['principal']) + float(borrowed_balance[0]['interest'])
        if not repay_margin(quote_asset, repay_amount):
            return False

    return True

def main():
    current_position = None
    stop_loss = None
    take_profit = None
    last_candle = None

    while True:
        try:
            current_candle = get_latest_candle()
            current_price = get_current_price()

            if last_candle and current_candle['open_time'] > last_candle['open_time']:
                new_position, action_taken, action_time, new_stop_loss, new_take_profit = analyze_candles(last_candle, current_candle, current_position)
                
                if action_taken:
                    if current_position:
                        close_side = 'SELL' if current_position == 'Long' else 'BUY'
                        if close_position(close_side, current_price):
                            print("Previous position closed successfully")
                        else:
                            print("Failed to close previous position")
                            continue

                    trade_side = 'BUY' if new_position == 'Long' else 'SELL'
                    if execute_trade(trade_side, current_price):
                        current_position = new_position
                        stop_loss = new_stop_loss
                        take_profit = new_take_profit
                    else:
                        print("Failed to execute new trade")

            if current_position:
                result = check_tp_sl(current_price, current_position, stop_loss, take_profit)
                if result:
                    print(f"\nTrade closed due to {result}")
                    print(f"Closing Time (NY): {datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    print(f"Closing Price: {current_price}")
                    close_side = 'SELL' if current_position == 'Long' else 'BUY'
                    if close_position(close_side, current_price):
                        print("Position closed successfully")
                        current_position = None
                        stop_loss = None
                        take_profit = None
                    else:
                        print("Failed to close position")

            last_candle = current_candle
            time.sleep(10)  # Check every 10 seconds

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60)  # Wait for 1 minute before retrying

if __name__ == "__main__":
    main()