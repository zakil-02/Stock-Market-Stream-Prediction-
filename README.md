# Real-Time Cryptocurrency Symbol Prediction Using Kafka
  <img src="https://static.vecteezy.com/system/resources/previews/013/257/156/non_2x/finance-and-business-background-bar-chart-and-candlestick-chart-show-stock-market-trading-price-vector.jpg" alt="Binance"/>
## Project Overview
This project implements Real-Time Cryptocurrency Symbol Prediction Using Kafkan and stream learning techniques.

## Prerequisites
- Python 3.8+
- Binance Account and API Keys from Binance (if you want to use Client data retrieval script)
  

## Installation

### Dependencies
```bash
pip install -r requirement.tx
```

### Binance Client API Configuration [Not required for the demo]
1. Create a Binance account
2. Generate API Key and Secret Key
3. Set environment variables:
```bash
export BINANCE_API_KEY='your_api_key'
export BINANCE_SECRET='your_secret_key'
```

## Batch Learning Models
This part is not included in the application workflow, it is implemented in jupyter notebooks and served to do a comparative study between batch and online learning.
### Implemented Models
1. **ARIMAX**
   - Time series forecasting model
   - Incorporates exogenous variables
   - Handles linear trends and seasonality

2. **Support Vector Regression (SVR)**
   - Non-linear regression technique
   - Effective for complex, non-linear relationships
   - Handles high-dimensional data

3. **Prophet**
   - Developed by Facebook
   - Robust to missing data and shifts
   - Automatic trend, seasonality detection

## Streaming Learning Models

### Online Learning Algorithms
1. **PARegressor (Passive-Aggressive Regressor)**
   - Online learning algorithm
   - Updates model incrementally
   - Handles changing data distributions

2. **KNNRegressor (K-Nearest Neighbors)**
   - Non-parametric method
   - Adapts to local data patterns
   - Suitable for streaming data

3. **ARFRegressor (Adaptive Random Forest)**
   - Ensemble method for streaming data
   - Dynamic model updates
   - Handles concept drift

4. **Linear Regression**
   - Gives a baseline model
   - Simple, interpretable model
   - Incremental learning capabilities

6. **Neural Network Regressor**
   - Deep learning approach
   - Captures complex non-linear patterns
   - Adaptable through online learning

## Demo Walkthrough

### Dashboard Features
- Real-time Crypto price predictions
- Model performance visualization
- Comparative analysis of different models

### Screenshot
![Dashboard Preview](dash.png)

## Running the Project

### Data Retrieval
```bash
python binance_data.py
```

### Kafka Setup
1. Start Kafka server
2. Run topics:
```bash
python SymbolsData_Topic.py
python Results_Topic.py
```

### Data Processing
```bash
python ProduceData.py
python ConsumeTrainProduce.py
```

### Launch Dashboard
```bash
streamlit run Dashboard_streamlit.py
```

## Performance Metrics
- Mean Absolute Error (MAE)
- Root Mean Square Error (RMSE)
- Mean Absolute Pourcentage Error (MAPE)
- R-squared (R²) Score

##  Project Technologies
<p align="center">
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="Python" width="60" height="60"/>
  <img src="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/binance.svg" alt="Binance" width="60" height="60"/>
  <img src="https://production-media.paperswithcode.com/social-images/IIGvoRhcqPHRAxAp.svg" alt="River" width="120" height="60"/>
  <img src="https://upload.wikimedia.org/wikipedia/commons/0/0a/Apache_kafka-icon.svg" alt="Kafka" width="60" height="60"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/streamlit/streamlit-original.svg" alt="Streamlit" width="60" height="60"/>
</p>


## Future Improvements
- Implement more advanced streaming models
- Enhanced feature engineering during the online learning
- Tracking price predictions for multiple symbols at a time

