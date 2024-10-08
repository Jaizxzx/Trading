import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
import pytz
from keys import api, secret
# Initialize Binance client and API Keys
api_key = api  # Replace with your actual API key
api_secret = secret  # Replace with your actual API secret
client = Client(api_key, api_secret)

# Trading parameters
symbol = 'SUIUSDT'
timeframe = Client.KLINE_INTERVAL_5MINUTE
leverage = 4  # 4x leverage

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
def get_account_balance():
    account_info = client.get_margin_account()
    usdt_balance = next((asset for asset in account_info['userAssets'] if asset['asset'] == 'USDT'), None)
    return float(usdt_balance['free']) if usdt_balance else 0

def calculate_order_quantity(balance):
    usable_balance = balance * 0.8
    borrowed_amount = usable_balance * leverage
    total_amount = usable_balance + borrowed_amount
    return total_amount

def borrow_margin(asset, amount):
    try:
        transaction = client.create_margin_loan(asset=asset, amount=amount)
        print(f"Borrowed {amount} {asset}: {transaction}")
        return True
    except Exception as e:
        print(f"Error borrowing {asset}: {e}")
        return False

def repay_margin(asset, amount):
    try:
        transaction = client.repay_margin_loan(asset=asset, amount=amount)
        print(f"Repaid {amount} {asset}: {transaction}")
        return True
    except Exception as e:
        print(f"Error repaying {asset}: {e}")
        return False

def place_margin_order(side, order_type, quantity, price=None):
    try:
        if order_type == ORDER_TYPE_MARKET:
            order = client.create_margin_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity,
                isIsolated='TRUE'
            )
        elif order_type == ORDER_TYPE_LIMIT:
            order = client.create_margin_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price,
                isIsolated='TRUE'
            )
        print(f"Margin order placed: {order}")
        return order
    except Exception as e:
        print(f"An error occurred while placing margin order: {e}")
        return None

def set_stop_loss_take_profit(side, quantity, stop_loss, take_profit):
    try:
        stop_loss_order = client.create_margin_order(
            symbol=symbol,
            side=SIDE_SELL if side == SIDE_BUY else SIDE_BUY,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            stopPrice=stop_loss,
            price=stop_loss,
            isIsolated='TRUE'
        )
        take_profit_order = client.create_margin_order(
            symbol=symbol,
            side=SIDE_SELL if side == SIDE_BUY else SIDE_BUY,
            type=ORDER_TYPE_TAKE_PROFIT_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            stopPrice=take_profit,
            price=take_profit,
            isIsolated='TRUE'
        )
        print(f"Stop Loss order placed: {stop_loss_order}")
        print(f"Take Profit order placed: {take_profit_order}")
    except Exception as e:
        print(f"An error occurred while setting SL/TP: {e}")

def check_order_status(order_id):
    try:
        order = client.get_margin_order(symbol=symbol, orderId=order_id, isIsolated='TRUE')
        return order['status'], float(order['executedQty']), float(order['cummulativeQuoteQty'])
    except Exception as e:
        print(f"Error checking order status: {e}")
        return None, None, None

def analyze_candles(first_candle, second_candle, current_position, moves):
    max_moves = 2
    action_taken = False
    action_time = None
    stop_loss = None
    take_profit = None

    if moves >= max_moves:
        return current_position, moves, action_taken, action_time, stop_loss, take_profit

    balance = get_account_balance()
    quantity = calculate_order_quantity(balance)

    if current_position == "Long":
        if second_candle['low'] < first_candle['low']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Flip Short")
            open_price = first_candle['low']
            stop_loss = first_candle['high']
            take_profit = open_price - (stop_loss - open_price)
            
            # Close existing long position
            close_order = place_margin_order(SIDE_SELL, ORDER_TYPE_MARKET, quantity)
            if close_order:
                order_id = close_order['orderId']
                status, executed_qty, quote_qty = check_order_status(order_id)
                if status == ORDER_STATUS_FILLED:
                    borrowed_amount = quote_qty / (leverage + 1) * leverage
                    if repay_margin('USDT', borrowed_amount):
                        # Open new short position
                        if borrow_margin('SUI', quantity):
                            short_order = place_margin_order(SIDE_SELL, ORDER_TYPE_LIMIT, quantity, price=open_price)
                            if short_order:
                                set_stop_loss_take_profit(SIDE_SELL, quantity, stop_loss, take_profit)
                                return "Short", moves + 1, True, action_time, stop_loss, take_profit

    elif current_position == "Short":
        if second_candle['high'] > first_candle['high']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Flip Long")
            open_price = first_candle['high']
            stop_loss = first_candle['low']
            take_profit = open_price + (open_price - stop_loss)
            
            # Close existing short position
            close_order = place_margin_order(SIDE_BUY, ORDER_TYPE_MARKET, quantity)
            if close_order:
                order_id = close_order['orderId']
                status, executed_qty, quote_qty = check_order_status(order_id)
                if status == ORDER_STATUS_FILLED:
                    if repay_margin('SUI', executed_qty):
                        # Open new long position
                        if borrow_margin('USDT', quote_qty):
                            long_order = place_margin_order(SIDE_BUY, ORDER_TYPE_LIMIT, quantity, price=open_price)
                            if long_order:
                                set_stop_loss_take_profit(SIDE_BUY, quantity, stop_loss, take_profit)
                                return "Long", moves + 1, True, action_time, stop_loss, take_profit
    
    else:  # No position yet
        if second_candle['close'] > first_candle['close']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Initial Long")
            open_price = second_candle['close']
            stop_loss = first_candle['low']
            take_profit = open_price + 2 * (open_price - stop_loss)
            
            if borrow_margin('USDT', quantity * open_price * (leverage / (leverage + 1))):
                long_order = place_margin_order(SIDE_BUY, ORDER_TYPE_LIMIT, quantity, price=open_price)
                if long_order:
                    set_stop_loss_take_profit(SIDE_BUY, quantity, stop_loss, take_profit)
                    return "Long", moves + 1, True, action_time, stop_loss, take_profit
        
        elif second_candle['close'] < first_candle['close']:
            action_time = second_candle['open_time']
            print(f"\nAction Time (NY): {action_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print("Signal: Initial Short")
            open_price = second_candle['close']
            stop_loss = first_candle['high']
            take_profit = open_price - 2 * (stop_loss - open_price)
            
            if borrow_margin('SUI', quantity):
                short_order = place_margin_order(SIDE_SELL, ORDER_TYPE_LIMIT, quantity, price=open_price)
                if short_order:
                    set_stop_loss_take_profit(SIDE_SELL, quantity, stop_loss, take_profit)
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
        current_order_id = None
        
        while current_time < trading_end and moves < 2 and trading_allowed:
            new_candle = get_candles(current_time)[0]
            
            if current_position:
                result, hit_candle = check_tp_sl(new_candle, current_position, stop_loss, take_profit)
                if result:
                    print(f"\nTrade closed due to {result}")
                    print(f"Closing Time (NY): {hit_candle['open_time'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    
                    status, executed_qty, quote_qty = check_order_status(current_order_id)
                    if status == ORDER_STATUS_FILLED:
                        if current_position == "Long":
                            repay_margin('USDT', quote_qty / (leverage + 1) * leverage)
                        else:
                            repay_margin('SUI', executed_qty)
                        
                        if result == "TP":
                            trading_allowed = False
                            print("Trading stopped for the day.")
                            break
                        elif result == "SL":
                            print(f"\nStop Loss hit - Flipping position")
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

def main():
    while True:
        current_time = datetime.now(ny_tz)
        current_date = current_time.date()
        ny_midnight = get_ny_midnight(current_date)
        
        if current_time > ny_midnight + timedelta(hours=1):
            next_midnight = ny_midnight + timedelta(days=1)
            wait_time = (next_midnight - current_time).total_seconds()
            print(f"Waiting for next trading day. Next session starts in {wait_time/3600:.2f} hours.")
            time.sleep(wait_time)
            continue
        
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