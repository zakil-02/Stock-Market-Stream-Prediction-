# 🚀 Quick Setup Guide

## Prerequisites

1. **Python 3.8+**
2. **Apache Kafka** (for streaming)
3. **Binance Account** (optional, for live data)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Kafka Server

```bash
# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka (in a new terminal)
bin/kafka-server-start.sh config/server.properties
```

### 3. Create Kafka Topics

```bash
cd kafka_streaming

# Create topics
python SymbolsData_Topic.py
python Results_Topic.py
```

### 4. Start Data Producer

```bash
# Terminal 1: Start producing data from Binance
python ProduceData.py
```

This will connect to Binance WebSocket and stream real-time data for:
- BTCUSDT
- ETHUSDT
- ADAUSDT
- XRPUSDT
- GALAUSDT

### 5. Start Model Consumer

```bash
# Terminal 2: Start consuming and training models
python ConsumeTrainProduce.py
```

You'll be prompted to:
1. Select a cryptocurrency symbol (1-5)
2. Select which models to use (comma-separated, e.g., "1,2,3")

Available models:
1. PA Regressor (Passive-Aggressive)
2. Adaptive Random Forest
3. Neural Network Regressor
4. Bagging Regressor
5. KNN Regressor

### 6. Launch Dashboard

```bash
# Terminal 3: Start the enhanced dashboard
./run_dashboard.sh

# Or directly:
streamlit run Dashboard_Enhanced.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Dashboard Features

### Theme Toggle
Click the "🌓 Theme" button in the top-right to switch between dark and light modes.

### Real-Time Updates
- Price chart updates every 4 seconds
- Shows real price vs model predictions
- Displays performance metrics for each model

### Metrics Displayed
- **MAE** (Mean Absolute Error) - Lower is better
- **RMSE** (Root Mean Square Error) - Lower is better
- **R²** (R-squared Score) - Higher is better (max 1.0)
- **MAPE** (Mean Absolute Percentage Error) - Lower is better

## Troubleshooting

### Kafka Connection Issues
```bash
# Check if Kafka is running
jps | grep Kafka

# Check topics
kafka-topics.sh --list --bootstrap-server localhost:9092
```

### No Data in Dashboard
1. Ensure ProduceData.py is running and connected to Binance
2. Ensure ConsumeTrainProduce.py is running and processing data
3. Check that you selected the same symbol in both consumer and dashboard
4. Wait a few minutes for initial data to accumulate

### Port Already in Use
```bash
# If port 8501 is busy, specify a different port
streamlit run Dashboard_Enhanced.py --server.port 8502
```

## Architecture Flow

```
Binance WebSocket
       ↓
ProduceData.py → Kafka Topic: SymbolsData
       ↓
ConsumeTrainProduce.py (Train Models)
       ↓
Kafka Topic: Results
       ↓
Dashboard_Enhanced.py (Visualize)
```

## Tips

1. **Start with fewer models** (1-2) for faster processing
2. **Let it run for 5-10 minutes** to see meaningful patterns
3. **Compare models** to see which performs best for each symbol
4. **Use dark theme** for better visibility of charts
5. **Monitor multiple terminals** to see the data flow

## System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Multi-core recommended for parallel model training
- **Network**: Stable internet connection for Binance WebSocket
- **Storage**: ~100MB for dependencies

---

**Ready to start? Follow the steps above and enjoy real-time crypto predictions!** 🚀
