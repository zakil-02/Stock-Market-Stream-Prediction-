# Stock Market Prediction using Batch learning and Stream learning techniques

## Introduction

## Guide 

### Binance data retrieval : 
- Before running the binance_data.py file in order to get some static data, you need to have a binance account and generate an API key and secret key.
- You need to install the python-binance library by running the following command in your terminal:
```bash
pip install python-binance
```
You need then to export your API key and secret key as environment variables in your terminal:
```bash
export BINANCE_API_KEY='your_api_key'
export BINANCE_SECRET = 'your_secret'
```
- You can then run the binance_data.py file to get the data from the binance API.



-----

In order to get the dashboard, you need to : 
- Install kafka
- run SymbolsData_Topic.py (create the 1st topic)
- run Results_Topic.py (create 2nd topic)
- run ProduceDara.py
- run ConsumeTrainProduce.py

  Then run this command : 
```bash
streamlit run Dashboard_streamlit.py
```

