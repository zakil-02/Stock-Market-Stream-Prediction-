#!/bin/bash
# Script to run the enhanced dashboard

echo "🚀 Starting Enhanced Crypto Trading Dashboard..."
echo ""
echo "Make sure you have:"
echo "  1. Kafka server running"
echo "  2. ProduceData.py running (data producer)"
echo "  3. ConsumeTrainProduce.py running (model consumer)"
echo ""
echo "Starting dashboard in 3 seconds..."
sleep 3

streamlit run Dashboard_Enhanced.py
