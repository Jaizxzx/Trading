# Cryptocurrency Trading Bot Documentation

# File Information

- **File Name**: `Futures_Cloud_Live_Run.py`
- **Directory**: `Binance\`
- **Full Path**: `Trading\Binance\`

## Overview

This Python script implements an automated trading bot for cryptocurrency futures on the Binance exchange. The bot uses a simple strategy based on comparing two consecutive 5-minute candles to make trading decisions.

## Key Features

- Trades SUIUSDT perpetual futures contracts
- Operates within specified trading hours (New York time zone)
- Uses a 5-minute candlestick interval for analysis
- Implements a basic long/short strategy with stop-loss and take-profit orders
- Includes position flipping logic after stop-loss is hit

## Dependencies

- binance.um_futures
- datetime
- pytz
- time

## Configuration

The script uses the following key parameters:

- `pair`: Trading pair (default: "SUIUSDT")
- `contract_type`: Contract type (default: "PERPETUAL")
- `interval`: Candlestick interval (default: "5m")
- `balance_perc`: Percentage of balance to use for trading (default: 80%)
- `leverage`: Trading leverage (default: 5)
- `timezoness`: Time zone for trading hours (default: "America/New_York")
- `start_time`: Daily trading start time (default: "10:40")
- `end_time`: Daily trading end time (default: "11:36")

## Main Components

1. **Initialization**: Sets up the Binance client and configures trading parameters.

2. **Utility Functions**:
   - `print_candle()`: Displays candle information
   - `is_within_trading_hours()`: Checks if current time is within trading hours
   - `get_candle_data()`: Extracts relevant data from a candle
   - `get_balance_usdt()`: Retrieves current USDT balance

3. **Trading Logic**:
   - `compare_candles()`: Compares two candles to determine trading direction
   - `order_status()`: Checks the status of stop-loss and take-profit orders
   - `main_loop()`: Main trading loop that orchestrates the entire process

## Trading Strategy

1. The bot waits for the completion of two consecutive 5-minute candles within the trading hours.
2. It compares the closing prices of these candles:
   - If the first candle closes higher, it opens a short position.
   - If the first candle closes lower, it opens a long position.
3. Stop-loss is set at the high (for short) or low (for long) of the first candle.
4. Take-profit is calculated as: `open_price + 2 * (open_price - stop_loss)`
5. If stop-loss is hit, the bot attempts to "flip" the position in the opposite direction.

## Error Handling and Robustness

- The script includes basic error handling and will attempt to continue running in case of exceptions.
- It cancels all open orders at the start of each trading day.
- The bot resets its state outside of trading hours.

## Limitations and Risks

- The strategy is relatively simple and may not perform well in all market conditions.
- There's no backtesting or risk management beyond basic stop-loss orders.
- The bot trades with a significant portion of the account balance, which could lead to substantial losses.

## Usage

1. Ensure all dependencies are installed.
2. Set up API keys in a separate `keys.py` file.
3. Adjust trading parameters as needed.
4. Run the script: `python trading_bot.py`

## Disclaimer

This bot is for educational purposes only. Cryptocurrency trading carries significant risk. Use at your own risk and always monitor your trades.
