from keys import api, secret
from binance.um_futures import UMFutures
import pandas as pd
from time import sleep
from binance.error import ClientError
from datetime import datetime, time, timedelta
import pytz

client = UMFutures(key=api, secret=secret)

leverage = 5  # 4x borrowed + 1x own capital
margin_type = 'ISOLATED'

# Global variables to track trading status
daily_trade_count = 0
take_profit_hit = False
initial_trade_executed = False
last_trade_date = None

def get_balance_usdt():
    try:
        response = client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['balance'])
    except ClientError as error:
        print(f"Error: {error.error_message}")
        return None

def set_leverage(symbol, level):
    try:
        response = client.change_leverage(symbol=symbol, leverage=level, recvWindow=6000)
        print(response)
    except ClientError as error:
        print(f"Error: {error.error_message}")

def set_margin_type(symbol, type):
    try:
        response = client.change_margin_type(symbol=symbol, marginType=type, recvWindow=6000)
        print(response)
    except ClientError as error:
        print(f"Error: {error.error_message}")

def get_price_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['pricePrecision']

def get_qty_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['quantityPrecision']

def get_ny_midnight_candles(symbol):
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = int(midnight.timestamp() * 1000)
    
    try:
        klines = client.klines(symbol, '5m', startTime=start_time, limit=2)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df = df.astype(float)
        return df[['open', 'high', 'low', 'close']]
    except ClientError as error:
        print(f"Error: {error.error_message}")
        return None

def place_margin_order(symbol, side, order_type, quantity, price=None, stop_price=None):
    try:
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timeInForce": "GTC",
        }
        if price:
            params["price"] = price
        if stop_price:
            params["stopPrice"] = stop_price

        response = client.new_margin_order(**params)
        print(f"Margin order placed: {response}")
        return response
    except ClientError as error:
        print(f"Error placing margin order: {error.error_message}")
        return None

def borrow_margin(asset, amount):
    try:
        response = client.margin_borrow(asset=asset, amount=amount)
        print(f"Margin borrowed: {response}")
        return response
    except ClientError as error:
        print(f"Error borrowing margin: {error.error_message}")
        return None

def repay_margin(asset, amount):
    try:
        response = client.margin_repay(asset=asset, amount=amount)
        print(f"Margin repaid: {response}")
        return response
    except ClientError as error:
        print(f"Error repaying margin: {error.error_message}")
        return None

def is_within_trading_window():
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz).time()
    start_time = time(12, 0)  # 12:00 PM
    end_time = time(13, 0)    # 1:00 PM
    return start_time <= now < end_time

def check_and_place_trades(symbol):
    global daily_trade_count, take_profit_hit, initial_trade_executed, last_trade_date

    # Reset daily variables if it's a new day
    current_date = datetime.now(pytz.timezone('America/New_York')).date()
    if last_trade_date != current_date:
        daily_trade_count = 0
        take_profit_hit = False
        initial_trade_executed = False
        last_trade_date = current_date

    if not is_within_trading_window():
        print("Outside trading window. No trades will be placed.")
        return

    if daily_trade_count >= 2:
        print("Maximum daily trade limit reached. No more trades today.")
        return

    if take_profit_hit:
        print("Take profit was hit today. No more trades until tomorrow.")
        return

    candles = get_ny_midnight_candles(symbol)
    if candles is None or len(candles) < 2:
        print("Failed to get candle data")
        return

    first_candle = candles.iloc[0]
    second_candle = candles.iloc[1]

    price_precision = get_price_precision(symbol)
    qty_precision = get_qty_precision(symbol)

    current_price = float(client.ticker_price(symbol)['price'])
    
    # Get current balance and calculate order quantity
    balance = get_balance_usdt()
    if balance is None:
        print("Failed to get account balance")
        return
    
    available_balance = balance * 0.8  # Take 80% of the current balance
    borrowed_amount = available_balance * 4  # Borrow 4x of the available balance
    total_order_amount = available_balance + borrowed_amount
    
    quantity = round(total_order_amount / current_price, qty_precision)

    if not initial_trade_executed:
        # Initial Long
        if second_candle['close'] > first_candle['close']:
            entry_price = round(second_candle['close'], price_precision)
            stop_loss = round(first_candle['low'], price_precision)
            take_profit = round(entry_price + 2 * (entry_price - stop_loss), price_precision)

            borrow_margin('USDT', borrowed_amount)
            place_margin_order(symbol, "BUY", "LIMIT", quantity, price=entry_price)
            place_margin_order(symbol, "SELL", "STOP_MARKET", quantity, stop_price=stop_loss)
            place_margin_order(symbol, "SELL", "TAKE_PROFIT_MARKET", quantity, stop_price=take_profit)

            initial_trade_executed = True
            daily_trade_count += 1

        # Initial Short
        elif second_candle['close'] < first_candle['close']:
            entry_price = round(second_candle['close'], price_precision)
            stop_loss = round(first_candle['high'], price_precision)
            take_profit = round(entry_price - 2 * (stop_loss - entry_price), price_precision)

            borrow_margin('USDT', borrowed_amount)
            place_margin_order(symbol, "SELL", "LIMIT", quantity, price=entry_price)
            place_margin_order(symbol, "BUY", "STOP_MARKET", quantity, stop_price=stop_loss)
            place_margin_order(symbol, "BUY", "TAKE_PROFIT_MARKET", quantity, stop_price=take_profit)

            initial_trade_executed = True
            daily_trade_count += 1

    else:  # Check for flip conditions only if initial trade was executed
        # Flip Short
        if current_price < first_candle['low']:
            entry_price = round(first_candle['low'], price_precision)
            stop_loss = round(first_candle['high'], price_precision)
            take_profit = round(entry_price - (stop_loss - entry_price), price_precision)

            borrow_margin('USDT', borrowed_amount)
            place_margin_order(symbol, "SELL", "LIMIT", quantity, price=entry_price)
            place_margin_order(symbol, "BUY", "STOP_MARKET", quantity, stop_price=stop_loss)
            place_margin_order(symbol, "BUY", "TAKE_PROFIT_MARKET", quantity, stop_price=take_profit)

            daily_trade_count += 1

        # Flip Long
        elif current_price > first_candle['high']:
            entry_price = round(first_candle['high'], price_precision)
            stop_loss = round(first_candle['low'], price_precision)
            take_profit = round(entry_price + (entry_price - stop_loss), price_precision)

            borrow_margin('USDT', borrowed_amount)
            place_margin_order(symbol, "BUY", "LIMIT", quantity, price=entry_price)
            place_margin_order(symbol, "SELL", "STOP_MARKET", quantity, stop_price=stop_loss)
            place_margin_order(symbol, "SELL", "TAKE_PROFIT_MARKET", quantity, stop_price=take_profit)

            daily_trade_count += 1

def close_position_and_repay(symbol):
    # Close the current position
    try:
        position = client.get_position_risk(symbol=symbol)
        if position['positionAmt'] != '0':
            side = "SELL" if float(position['positionAmt']) > 0 else "BUY"
            quantity = abs(float(position['positionAmt']))
            place_margin_order(symbol, side, "MARKET", quantity)
    except ClientError as error:
        print(f"Error closing position: {error.error_message}")
    
    # Repay borrowed margin
    try:
        borrowed = client.get_margin_borrowed(asset='USDT')
        if borrowed > 0:
            repay_margin('USDT', borrowed)
    except ClientError as error:
        print(f"Error repaying margin: {error.error_message}")

def main():
    symbol = "BTCUSDT"  # Change this to the desired trading pair
    
    while True:
        balance = get_balance_usdt()
        if balance is None:
            print('Cannot connect to API. Check IP, restrictions, or wait some time')
            sleep(60)
            continue

        print(f"Current balance: {balance} USDT")

        set_margin_type(symbol, margin_type)
        set_leverage(symbol, leverage)

        check_and_place_trades(symbol)

        # Check if any open orders are filled
        open_orders = client.get_open_orders(symbol=symbol)
        if not open_orders:
            close_position_and_repay(symbol)

        print('Waiting for 5 minutes before next check')
        sleep(300)

if __name__ == "__main__":
    main()