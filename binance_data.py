import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from binance.client import Client
import os
import yfinance as yf

BINANCE_API_KEY = os.environ.get('binance_key')
BINANCE_SECRET_KEY = os.environ.get('binance_secret')

class BinanceData:
    def __init__(self, api_key=BINANCE_API_KEY, secret_key=BINANCE_SECRET_KEY):
        self.client = Client(api_key, secret_key)

    def get_portfolio(self):
        '''
        Get the current portfolio of the user

        # Returns:
        ----------------
        return: dict

        '''
        account_info = self.client.get_account()
        balances = account_info['balances']
        portfolio = {item['asset']: float(item['free']) + float(item['locked']) for item in balances}
        relevant_assets = ['BNB', 'BTC', 'ETH', 'USDT']
        portfolio = {asset: portfolio.get(asset, 0) for asset in relevant_assets}

        # Plot portfolio
        plt.figure(figsize=(10, 5))
        plt.bar(portfolio.keys(), portfolio.values())
        plt.title('Portfolio')
        plt.show()

    def get_symbol_data(self, symbol, info_type='reduced', interval='5m', limit=20000):
        all_klines = []
        start_time = None

        while True:
            params = {
                'symbol': symbol, 
                'interval': interval, 
                'limit': 1000  # Binance API max limit per request
            }
            if start_time:
                params['startTime'] = start_time

            try:
                klines = self.client.get_klines(**params)
                
                # If no more data or reached limit, break
                if not klines or len(all_klines) >= limit:
                    break
                
                all_klines.extend(klines)
                
                # Update start_time to the timestamp of the last candle + 1 millisecond
                start_time = int(klines[-1][0]) + 1

            except Exception as e:
                print(f"Error fetching data: {e}")
                break

        columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        all_columns = columns + ['close_time', 'quote_asset_volume', 'number_of_trades',
                                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        df = pd.DataFrame(all_klines[:limit], columns=all_columns)
        df['date'] = pd.to_datetime(df['date'], unit='ms')
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})

        if info_type == 'reduced':
            df = df[columns]

        return df

def compute_technical_indices(df):
    # Moving Averages
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # Relative Strength Index (RSI)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Stochastic Oscillator
    lowest_low = df['low'].rolling(window=14).min()
    highest_high = df['high'].rolling(window=14).max()
    
    df['stoch_k'] = ((df['close'] - lowest_low) / (highest_high - lowest_low)) * 100
    df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
    
    # Bollinger Bands
    rolling_mean = df['close'].rolling(window=20).mean()
    rolling_std = df['close'].rolling(window=20).std()
    df['BB_upper'] = rolling_mean + (rolling_std * 2)
    df['BB_middle'] = rolling_mean
    df['BB_lower'] = rolling_mean - (rolling_std * 2)
    
    # Volatility (Average True Range)
    high_low = df['high'] - df['low']
    high_close_prev = np.abs(df['high'] - df['close'].shift(1))
    low_close_prev = np.abs(df['low'] - df['close'].shift(1))
    df['ATR'] = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1).rolling(window=14).mean()
    
    # Momentum (Rate of Change)
    df['ROC'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    
    return df

def prepare_features(df, lookback=8, forecast_horizon=5):
    # Create lagged features
    for i in range(1, lookback + 1):
        df[f'lag_{i}'] = df['close'].shift(i)
    
    # Create rolling statistics
    df['rolling_mean'] = df['close'].rolling(window=lookback).mean()
    df['rolling_std'] = df['close'].rolling(window=lookback).std()
    
    # Create target variable (future price movement)
    df['target'] = df['close'].shift(-forecast_horizon) / df['close'] - 1
    
    # Drop NaN values
    df.dropna(inplace=True)
    
    return df




if __name__ == '__main__':
    print("keys: ", BINANCE_API_KEY, BINANCE_SECRET_KEY)
    bd = BinanceData()
    #bd.get_portfolio()
    df_1 = bd.get_symbol_data('BTCUSDT', info_type='reduced', limit=20000)
    df_2 = bd.get_symbol_data('ETHUSDT', info_type='reduced', limit=20000)
    df_3 = bd.get_symbol_data('ADAUSDT', info_type='reduced', limit=20000)

    df_1 = compute_technical_indices(df_1)
    df_2 = compute_technical_indices(df_2)
    df_3 = compute_technical_indices(df_3)

    df_1 = prepare_features(df_1)
    df_2 = prepare_features(df_2)
    df_3 = prepare_features(df_3)

    #save to csv
    df_1.to_csv('./Batch_Learning_notebooks/Bdata/BTCUSDT.csv')
    print("BTCUSDT.csv saved")
    df_2.to_csv('./Batch_Learning_notebooks/Bdata/ETHUSDT.csv')
    print("ETHUSDT.csv saved")
    df_3.to_csv('./Batch_Learning_notebooks/Bdata/ADAUSDT.csv')
    print("ADAUSDT.csv saved")
