import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from binance.client import Client
import os

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



    def get_symbol_data(self, symbol, info_type='reduced', interval='1D', limit=200000):
        '''
        Get historical data for a given symbol

        # Parameters: 
        ----------------

        symbol: str
        info_type: str
        interval: str
        limit: int

        # Returns:
        ----------------
        return: pd.DataFrame

        '''
        klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        all_columns = columns + ['close_time', 'quote_asset_volume', 'number_of_trades',
                                  'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        df = pd.DataFrame(klines, columns=all_columns)
        df['date'] = pd.to_datetime(df['date'], unit='ms')
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})

        if info_type == 'reduced':
            df = df[columns]

        return df



if __name__ == '__main__':
    print("keys: ", BINANCE_API_KEY, BINANCE_SECRET_KEY)
    bd = BinanceData()
    #bd.get_portfolio()
    df_1 = bd.get_symbol_data('BTCUSDT', info_type='reduced', interval='1d', limit=200000)
    df_2 = bd.get_symbol_data('ETHUSDT', info_type='reduced', interval='1d', limit=200000)
    df_3 = bd.get_symbol_data('ADAUSDT', info_type='reduced', interval='1d', limit=200000)

    #save to csv
    df_1.to_csv('./Batch_Learning_notebooks/data/BTCUSDT.csv')
    print("BTCUSDT.csv saved")
    df_2.to_csv('./Batch_Learning_notebooks/data/ETHUSDT.csv')
    print("ETHUSDT.csv saved")
    df_3.to_csv('./Batch_Learning_notebooks/data/ADAUSDT.csv')
    print("ADAUSDT.csv saved")
