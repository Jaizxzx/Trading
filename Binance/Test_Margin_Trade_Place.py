'''from binance.client import Client
from binance.enums import *
import time

# Initialize the Binance client
client = Client('', '')

def get_lot_size(symbol):
    """Fetches the LOT_SIZE filter for a symbol."""
    info = client.get_symbol_info(symbol)
    
    for filter in info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            return {
                'minQty': float(filter['minQty']),
                'maxQty': float(filter['maxQty']),
                'stepSize': float(filter['stepSize'])
            }
    return None

def adjust_quantity(quantity, step_size):
    """Adjusts the order quantity to comply with the step size."""
    return round(quantity // step_size * step_size, len(str(step_size).split('.')[1]))

def isolated_margin_trade_example():
    symbol = 'SUIUSDT'
    
    # Step 1: Get the current isolated margin account balance for the specific symbol (SUIUSDT)
    account_info = client.get_isolated_margin_account()
    symbol_info = next((item for item in account_info['assets'] if item['symbol'] == symbol), None)
    
    if not symbol_info:
        print(f"Error: No account info found for symbol {symbol}")
        return

    usdt_balance = float(symbol_info['quoteAsset']['free'])  # USDT balance for this isolated margin pair
    print(f"Current USDT balance in isolated margin for {symbol}: {usdt_balance}")

    # Ensure USDT balance is greater than 0
    if usdt_balance == 0:
        print("Error: USDT balance is zero in isolated margin. Please deposit USDT into your isolated margin account.")
        return

    # Step 2: Take 80% of the balance
    usable_balance = usdt_balance * 0.8
    print(f"Usable balance (80%): {usable_balance}")

    # Step 3: Borrow 4x of the usable balance in isolated margin
    borrow_amount = round(usable_balance * 0.4, 8)  # Limit to 8 decimal places

    # Ensure the borrow amount is valid
    if borrow_amount <= 0:
        print(f"Error: Invalid borrow amount: {borrow_amount}")
        return

    # Borrow the USDT in isolated margin
    client.create_margin_loan(asset='USDT', amount=f"{borrow_amount:.8f}", isIsolated='TRUE', symbol=symbol)
    print(f"Borrowed amount in isolated margin: {borrow_amount}")

    # Step 4: Calculate order quantity
    total_funds = usable_balance + borrow_amount
    current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    quantity = total_funds / current_price
    print(f"Raw order quantity: {quantity}")

    # Step 5: Adjust quantity based on LOT_SIZE filter
    lot_size_info = get_lot_size(symbol)
    if not lot_size_info:
        print("Error: LOT_SIZE filter not found.")
        return
    
    quantity = adjust_quantity(quantity, lot_size_info['stepSize'])
    print(f"Adjusted order quantity: {quantity}")

    if quantity < lot_size_info['minQty'] or quantity > lot_size_info['maxQty']:
        print(f"Error: Quantity {quantity} does not meet the LOT_SIZE requirements.")
        return

    # Step 6: Place a buy order on isolated margin
    buy_order = client.create_margin_order(
        symbol=symbol,
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=f"{quantity:.3f}",
        isIsolated='TRUE'
    )
    print(f"Buy order placed on isolated margin: {buy_order}")

    # Wait for a short time (for demonstration purposes)
    time.sleep(5)

    # Step 7: Place a sell order to close the position on isolated margin
    sell_order = client.create_margin_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=f"{quantity:.3f}",
        isIsolated='TRUE'
    )
    print(f"Sell order placed on isolated margin: {sell_order}")

    # Repay the borrowed amount in isolated margin
    client.repay_margin_loan(asset='USDT', amount=f"{borrow_amount:.8f}", isIsolated='TRUE', symbol=symbol)
    print(f"Repaid borrowed amount in isolated margin: {borrow_amount}")

    # Print final balance in isolated margin
    final_balance = float(next(item['quoteAsset']['free'] for item in client.get_isolated_margin_account()['assets'] if item['symbol'] == symbol))
    print(f"Final USDT balance in isolated margin for {symbol}: {final_balance}")

if __name__ == "__main__":
    isolated_margin_trade_example()
'''
'''
from binance.spot import Spot as Client
from binance.lib.utils import config_logging



spot_client = Client('', '')


print(spot_client.isolated_margin_account(symbol="USDT"))

'''

import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

# historical_trades requires api key in request header
spot_client = Client(base_url="https://testnet.binance.vision")

logging.info(spot_client.historical_trades("BTCUSDT"))
logging.info(spot_client.historical_trades("BTCUSDT", limit=1, fromId="10"))