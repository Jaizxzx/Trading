# Algo Trading 
# Binance Futures Trading Bot

This project implements a cryptocurrency trading bot for Binance Futures. The bot uses a simple strategy based on comparing two consecutive 5-minute candles to make trading decisions on a specified trading pair.

## Features

- Automated trading on Binance Futures
- Customizable trading hours
- Implements a basic strategy comparing two consecutive candles
- Handles both long and short positions
- Includes stop-loss and take-profit orders
- Supports "flip" trades after stop-loss is triggered

## Prerequisites

- Python 3.7+
- Binance Futures account
- API key and secret from Binance

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/binance-futures-trading-bot.git
   cd binance-futures-trading-bot
   ```

2. Install the required packages:
   ```
   pip install binance-futures-connector pytz
   ```

3. Create a `keys.py` file in the Binance directory with your Binance API credentials:
   ```python
   api = "your_api_key_here"
   secret = "your_secret_key_here"
   ```

## Configuration

Open the `Futures_Cloud_Live_Run.py` file in the Binance directory and adjust the following parameters as needed:

- `pair`: The trading pair (e.g., "SUIUSDT")
- `qty`: The quantity to trade
- `leverage`: The leverage to use
- `timezoness`: Your preferred timezone
- `start_time` and `end_time`: The daily trading window

## Usage

1. Navigate to the Binance directory:
   ```
   cd Binance
   ```

2. Run the bot with the following command:
   ```
   python Futures_Cloud_Live_Run.py
   ```

The bot will run continuously, trading only during the specified hours each day.

## Additional Files and Functions

- Check the `testing` directory for other algorithms and helper functions.
- The `algos` directory contains test net testing codes for various trading algorithms.

Feel free to explore and modify these files to suit your trading strategies.

## Warning

This bot is for educational purposes only. Use it at your own risk. Cryptocurrency trading carries a high level of risk, and you can potentially lose all your invested capital. Always start with small amounts and never trade more than you can afford to lose.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](https://github.com/yourusername/binance-futures-trading-bot/issues) if you want to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
