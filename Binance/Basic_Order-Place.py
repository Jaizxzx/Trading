from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
from keys import testnet_api , testnet_secret
# Initialize Binance testnet client
api_key = testnet_api
api_secret = testnet_secret
client = Client(api_key, api_secret, testnet=True)

def get_symbol_info(symbol):
    return client.get_symbol_info(symbol)

def get_current_price(symbol):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def get_valid_quantity(symbol, desired_quantity, side):
    info = get_symbol_info(symbol)
    if info is None:
        raise ValueError(f"Invalid symbol: {symbol}")

    lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', info['filters']))
    min_qty = float(lot_size_filter['minQty'])
    max_qty = float(lot_size_filter['maxQty'])
    step_size = float(lot_size_filter['stepSize'])

    min_notional_filter = next(filter(lambda x: x['filterType'] == 'NOTIONAL', info['filters']))
    min_notional = float(min_notional_filter['minNotional'])

    current_price = get_current_price(symbol)

    if side == Client.SIDE_BUY:
        min_qty_for_notional = min_notional / current_price
        quantity = max(desired_quantity, min_qty_for_notional)
    else:  # SELL
        quantity = desired_quantity

    # Adjust quantity to step size
    quantity = (quantity // step_size) * step_size

    # Ensure quantity is within allowed range
    quantity = max(min_qty, min(quantity, max_qty))

    # Check if the adjusted quantity meets the min notional
    if quantity * current_price < min_notional:
        quantity = min_notional / current_price
        quantity = (quantity // step_size + 1) * step_size  # Round up to the next valid step

    return round(quantity, 8)  # Round to 8 decimal places

def place_limit_order(symbol, side, quantity):
    try:
        valid_quantity = get_valid_quantity(symbol, quantity, side)
        print(f"Placing {side} order with quantity: {valid_quantity}")

        current_price = get_current_price(symbol)
        # Adjust price slightly to ensure the order gets filled quickly
        if side == Client.SIDE_BUY:
            price = round(current_price * 1.005, 2)  # 0.5% above current price
        else:
            price = round(current_price * 0.995, 2)  # 0.5% below current price

        # Place a limit order
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_LIMIT,
            quantity=valid_quantity,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            price=price
        )
        print(f"Order placed successfully: {order}")
        return order
    except BinanceAPIException as e:
        print(f"An error occurred: {e}")
        return None

def buy_limit(symbol, quantity):
    return place_limit_order(symbol, Client.SIDE_BUY, quantity)

def sell_limit(symbol, quantity):
    return place_limit_order(symbol, Client.SIDE_SELL, quantity)
def check_order_status(order_id):
    try:
        order = client.get_order(symbol='SUIUSDT',orderId=order_id)
        return order
    except Exception as e:
        print(f"Error checking order status: {e}")
        return None, None, None
# Example usage
if __name__ == "__main__":
    # Set the trading pair and quantity
    symbol = 'SUIUSDT'
    desired_quantity = 1  # This will be adjusted to a valid quantity

    # Place a buy order
    buy_order = buy_limit(symbol, desired_quantity)
    if buy_order:
        print("Buy order executed successfully!")
    else:
        print("Failed to execute buy order.")
    time.sleep(1)
    print(check_order_status(buy_order['orderId']))
    time.sleep(1)
    # Place a sell order
    sell_order = sell_limit(symbol, desired_quantity)
    print(check_order_status(sell_order['orderId']))
    if sell_order:
        print("Sell order executed successfully!")
    else:
        print("Failed to execute sell order.")