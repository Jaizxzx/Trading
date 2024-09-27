from binance.um_futures import UMFutures
from datetime import datetime, timedelta, timezone
import pytz
import time
from binance.error import ClientError
from keys import api , secret
# Initialize the UMFutures client
api_key = api
api_secret = secret
um_futures_client = UMFutures(api_key, api_secret)

# Set the parameters
pair = "SUIUSDT"
contract_type = "PERPETUAL"
interval = "5m"
qty = 7 # (current_balance*0.8)*leverage/open_price
leverage = 5
timezoness = "America/New_York"
# percentage_leverage (0.8) initially


# Set the New York timezone
ny_timezone = pytz.timezone(timezoness)
print(f"Using timezone: {ny_timezone}")

# Set the daily start and end times (in NY time)
start_time = datetime.strptime("10:40", "%H:%M").time()
end_time = datetime.strptime("11:36", "%H:%M").time()

def print_candle(candle):
    utc_time = datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
    ny_time = utc_time.astimezone(ny_timezone)
    print(f"Candle start (NY): {ny_time}, Open: {candle[1]}, High: {candle[2]}, Low: {candle[3]}, Close: {candle[4]}")


def print_candle(candle):
    utc_time = datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
    ny_time = utc_time.astimezone(ny_timezone)
    print(f"Candle start (NY): {ny_time}, Open: {candle[1]}, High: {candle[2]}, Low: {candle[3]}, Close: {candle[4]}")

def is_within_trading_hours(current_time):
    current_time = current_time.time()
    if start_time < end_time:
        return start_time <= current_time <= end_time
    else:  # Handle case where trading window crosses midnight
        return current_time >= start_time or current_time <= end_time

def get_candle_data(candle):
    return {
        'timestamp': candle[0],
        'open': float(candle[1]),
        'high': float(candle[2]),
        'low': float(candle[3]),
        'close': float(candle[4])
    }

def get_balance_usdt():
    try:
        response = um_futures_client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['balance'])

    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


# Placeholder comparison function
def compare_candles(first_candle, second_candle,flag_num_orders):
    print('\nGetting balance...')
    balance = get_balance_usdt()
    if balance != None:
        print("Balance is: ", balance, " USDT")
    print("\nCanceling all the orders from the previous day...")
    try:
        open_orders_cancel = um_futures_client.cancel_open_orders(symbol=pair)
        print(open_orders_cancel)
    except Exception as e:
        print("An error occurred while canceling orders: ", e)
    print("\nComparing the two stored candles...")
    resp2 = None
    resp3 = None
    side = None
    if first_candle['close'] > second_candle['close']:
        print("First candle closed higher than the second candle")
        print("Short Initial Signal")
        open_price = second_candle['close']
        stop_loss = first_candle['high']
        take_profit = round(open_price + 2 * (open_price - stop_loss),4)
        print("Open Price: ", open_price)
        print("Stop Loss: ", stop_loss)
        print("Take Profit: ", take_profit)
        
        resp1 = um_futures_client.new_order(symbol=pair,price = open_price ,side='SELL', type='LIMIT', quantity=qty, leverage=leverage,tp_price=take_profit,sl_price=stop_loss,timeInForce='GTC')
        print(pair, 'SELL', "placing order")
        print(resp1)
        flag_num_orders+=1
        time.sleep(2)

        resp2 = um_futures_client.new_order(symbol=pair, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=stop_loss,closePosition=True)
        print(resp2)
        time.sleep(2)
        resp3 = um_futures_client.new_order(symbol=pair, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                stopPrice=take_profit,closePosition=True)
        print(resp3)
        side = 'SELL'
        open_price = None
        stop_loss = None
        take_profit = None

    elif first_candle['close'] <= second_candle['close']:
        print("First candle closed lower than the second candle")
        print("Long Initial Signal") 
        open_price = second_candle['close']
        stop_loss = first_candle['low']
        take_profit = round(open_price + 2 * (open_price - stop_loss),4)
        print("Open Price: ", open_price)
        print("Stop Loss: ", stop_loss)
        print("Take Profit: ", take_profit)
        resp1 = um_futures_client.new_order(symbol=pair,price = open_price ,side='BUY', type='LIMIT', quantity=qty, leverage=leverage,tp_price=take_profit,sl_price=stop_loss,timeInForce='GTC')
        print(pair, 'BUY', "placing order")
        flag_num_orders+=1
        print(resp1)
        time.sleep(2)

        resp2 = um_futures_client.new_order(symbol=pair, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=stop_loss,closePosition=True)
        print(resp2)
        time.sleep(2)
        resp3 = um_futures_client.new_order(symbol=pair, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                stopPrice=take_profit,closePosition=True)
        print(resp3)
        side = 'BUY'
        open_price = None
        stop_loss = None
        take_profit = None

    else:
        print("Error in comparison of first two candles")
    # Add your comparison logic here
    return resp2, resp3, side,flag_num_orders

def order_status(tp_order, sl_order, initial_signal):
    print("\nChecking order status...")
    order_sl_check = um_futures_client.query_order(symbol=sl_order['symbol'],orderId=sl_order['orderId'])
    print("Stop loss order status: ", order_sl_check['status'], " for order id: ", sl_order['orderId'])
    order_tp_check = um_futures_client.query_order(symbol=tp_order['symbol'],orderId=tp_order['orderId'])
    print("Take profit order status: ", order_tp_check['status'], " for order id: ", tp_order['orderId'])

    if order_sl_check['status'] == 'FILLED':
        print("Stop loss order has been filled")
        print("Cancelling the take profit order")
        resp_tp_cancel = um_futures_client.cancel_order(symbol=pair, orderId=tp_order['orderId'])
        print(resp_tp_cancel)
        return True
    elif order_tp_check['status'] == 'FILLED':
        print("Take profit order has been filled")
        print("Cancelling the stop loss order")
        resp_sl_cancel = um_futures_client.cancel_order(symbol=pair, orderId=sl_order['orderId'])
        print(resp_sl_cancel)
        return False
    else:
        return False

def main_loop():
    first_candle = None
    second_candle = None
    in_trading_window = False
    order_placed = False
    tp_order = None
    sl_order = None
    initial_signal = None
    sl_order_fill_status = False
    flag_num_orders = 0
    while True:
        now = datetime.now(ny_timezone)
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} NY time")
        
        current_in_trading_window = is_within_trading_hours(now)
        
        if current_in_trading_window and not in_trading_window:
            print("Entered trading window. Starting trading logic.")
            first_candle = None
            second_candle = None
        elif not current_in_trading_window and in_trading_window:
            print("Exited trading window. Resetting candles.")
            first_candle = None
            second_candle = None
        
        in_trading_window = current_in_trading_window

        if in_trading_window:
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
                    
                    current_candle = get_candle_data(klines[0])
                    
                    if first_candle is None:
                        first_candle = current_candle
                        print("Stored first candle data")
                    elif second_candle is None:
                        second_candle = current_candle
                        print("Stored second candle data")
                        
                        print("\nStored Candle Data:")
                        print("First Candle:", first_candle)
                        print("Second Candle:", second_candle)

                        sl_order, tp_order, initial_signal,flag_num_orders= compare_candles(first_candle, second_candle,flag_num_orders)
                        
                        print("Code reached here after compare_candles !!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        order_placed = True
                        # first_candle = None #changed
                        # second_candle = None #changed
                    elif order_placed:
                        # Call the order_status function for all subsequent candles
                        sl_order_fill_status = order_status(tp_order=tp_order, sl_order=sl_order, initial_signal=initial_signal)
                        if(sl_order_fill_status):
                            order_placed = False
                    
                    elif sl_order_fill_status:
                        # Fetch and print the last 5-minute candle OHLC data #changed
                        latest_klines = um_futures_client.continuous_klines( #changed
                            pair=pair, #changed
                            contractType=contract_type, #changed
                            interval=interval, #changed
                            limit=1, #changed
                            endTime=int(now.timestamp() * 1000) #changed
                        )
                        if latest_klines: #changed
                            print("\nLatest 5-minute candle after SL order fill status:") #changed
                            print_candle(latest_klines[0]) #changed
                            latest_candle = get_candle_data(latest_klines[0]) #changed
                            print("Latest Candle timestamp :", latest_candle['timestamp']) #changed
                            print("Latest Candle open :", latest_candle['open']) #changed
                            print("Latest Candle close :", latest_candle['close']) #changed
                            print("Latest Candle high :", latest_candle['high']) #changed
                            print("Latest Candle low :", latest_candle['low']) #changed
                            
                            if initial_signal == 'SELL' and flag_num_orders == 1:
                                open_price = latest_candle['high']
                                stop_loss = latest_candle['low']
                                take_profit = round(open_price + 2 * (open_price - stop_loss),4)
                                print("Initial Signal was SELL")
                                print("Placing Long Flip order")
                                print("open_price:", open_price)
                                print("stop_loss:", stop_loss)
                                print("take_profit:", take_profit)
                                resp1 = um_futures_client.new_order(symbol=pair,price = open_price ,side='BUY', type='LIMIT', quantity=qty, leverage=leverage,tp_price=take_profit,sl_price=stop_loss,timeInForce='GTC')
                                print(pair, 'Flip BUY', "placing order")
                                print(resp1)
                                time.sleep(2)
                                flag_num_orders+=1
                                resp2 = um_futures_client.new_order(symbol=pair, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=stop_loss,closePosition=True)
                                print(resp2)
                                time.sleep(2)
                                resp3 = um_futures_client.new_order(symbol=pair, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                                        stopPrice=take_profit,closePosition=True)
                                print(resp3)
                            elif initial_signal == 'BUY' and flag_num_orders == 1:
                                open_price = latest_candle['low']
                                stop_loss = latest_candle['high']
                                take_profit = round(open_price + 2 * (open_price - stop_loss),4)
                                print("Initial Signal was BUY")
                                print("Placing Short Flip order")
                                print("open_price:", open_price)
                                print("stop_loss:", stop_loss)
                                print("take_profit:", take_profit)
                                resp1 = um_futures_client.new_order(symbol=pair,price = open_price ,side='SELL', type='LIMIT', quantity=qty, leverage=leverage,tp_price=take_profit,sl_price=stop_loss,timeInForce='GTC')
                                print(pair, 'Flip SELL', "placing order")
                                print(resp1)
                                time.sleep(2)
                                flag_num_orders+=1
                                resp2 = um_futures_client.new_order(symbol=pair, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=stop_loss,closePosition=True)
                                print(resp2)
                                time.sleep(2)
                                resp3 = um_futures_client.new_order(symbol=pair, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC',
                                                        stopPrice=take_profit,closePosition=True)
                                print(resp3)
                            else:
                                print("Error in initial signal")

                        sl_order_fill_status = False

                else:
                    print("No data received")

                next_candle_end = now + timedelta(minutes=5 - now.minute % 5, seconds=-now.second, microseconds=-now.microsecond)
                sleep_time = (next_candle_end - now).total_seconds() + 2
                print(f"Waiting for {sleep_time:.2f} seconds until next candle completes...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(60)
        else:
            first_candle = None #changed
            second_candle = None #changed
            flag_num_orders = 0
            print("Outside trading hours. Checking again in 60 seconds.")
            time.sleep(60)

if __name__ == "__main__":
    print(f"Script will run continuously, trading daily from {start_time} to {end_time} NY time")
    main_loop()