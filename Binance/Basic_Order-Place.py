from binance.client import Client
from binance.exceptions import BinanceAPIException

# Initialize Binance client
api_key = 'pr5GIjVdQbms8xLJhjB4aOD1FSuPTKqoy8syXf7cVYYSA0r31rgJ9Fz9nr7ok0Bv'
api_secret = 'DDRDDTHqHAQQTX5D5vNxBxnOlU1RvjS81otZUPUAgUaSZw2i32uwOJ6ACYqTzxcR'
client = Client(api_key, api_secret)

def place_market_order(symbol, side, quantity):
    try:
        # Place a market order
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Order placed successfully: {order}")
        return order
    except BinanceAPIException as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Set the trading pair, side (BUY or SELL), and quantity
    symbol = 'BTCUSDT'
    side = Client.SIDE_BUY
    quantity = 0.0000001  # Be cautious with the quantity! Start with a small amount for testing.

    # Place the order
    order = place_market_order(symbol, side, quantity)

    if order:
        print("Trade executed successfully!")
    else:
        print("Failed to execute trade.")