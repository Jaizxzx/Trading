from binance.client import Client
from binance.exceptions import BinanceAPIException

# Initialize Binance client with your API key and secret
api_key = 'pr5GIjVdQbms8xLJhjB4aOD1FSuPTKqoy8syXf7cVYYSA0r31rgJ9Fz9nr7ok0Bv'  # Replace with your actual API key
api_secret = 'DDRDDTHqHAQQTX5D5vNxBxnOlU1RvjS81otZUPUAgUaSZw2i32uwOJ6ACYqTzxcR'  # Replace with your actual API secret
client = Client(api_key, api_secret)

# Function to borrow funds
def borrow_margin(asset, amount, symbol):
    try:
        response = client.create_margin_loan(asset=asset, amount=amount, isIsolated='TRUE', symbol=symbol)
        print(f"Borrowed {amount} {asset} in isolated margin account for {symbol}.")
        print(response)
    except BinanceAPIException as e:
        print(f"Error borrowing {amount} {asset}: {e}")

# Function to repay funds
def repay_margin(asset, amount, symbol):
    try:
        response = client.repay_margin_loan(asset=asset, amount=amount, isIsolated='TRUE', symbol=symbol)
        print(f"Repaid {amount} {asset} in isolated margin account for {symbol}.")
        print(response)
    except BinanceAPIException as e:
        print(f"Error repaying {amount} {asset}: {e}")

# Example usage
if __name__ == "__main__":
    asset_to_borrow = 'USDT'
    amount_to_borrow = '100'
    trading_pair = 'BTCUSDT'

    # Borrow funds
    borrow_margin(asset_to_borrow, amount_to_borrow, trading_pair)

    # Repay funds
    repay_margin(asset_to_borrow, amount_to_borrow, trading_pair)