import pandas as pd
import time
import requests
import json
import websockets
import asyncio
from kafka import KafkaProducer

KAFKA_BROKER = "localhost:9092"
TOPIC = "DataForTraining"

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT', 'GALAUSDT']

PARTITIONS = 5

# Create a global Kafka producer to avoid creating a new producer for every send
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    key_serializer=str.encode,  # Automatic key encoding
    value_serializer=lambda x: json.dumps(x).encode('utf-8')  # Serialize message values to JSON
)

# Function to send processed data to Kafka
def produce_to_kafka(symbol, data):
    if not data:
        print(f"No data to send for symbol: {symbol}")
        return
    try:
        producer.send(
            TOPIC,
            key=symbol,  # Key used for partitioning
            value=data  # Actual message data
        )
        print(f"Sent to Kafka topic {TOPIC}: {data}")
        producer.flush()  # Ensure the message is sent successfully
    except Exception as e:
        print(f"Error producing message to Kafka: {e}")


async def listen_binance(symbol):
    url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_1m"  # WebSocket URL for 1-minute candlesticks
    while True:
        try:
            async with websockets.connect(url) as websocket:
                while True:
                    message = await websocket.recv()  # Receive real-time data
                    data = json.loads(message)  # Convert JSON data to a Python dictionary
                    kline = data['k']  # Extract candlestick information
                    print(f"Received data for {symbol}:")
                    produce_to_kafka(symbol, kline)
        except websockets.ConnectionClosed as e:
            print(f"Connection to Binance WebSocket closed for {symbol}, reconnecting... Error: {e}")
            await asyncio.sleep(5)  # Wait 5 seconds before attempting to reconnect
        except Exception as e:
            print(f"Error in WebSocket connection for {symbol}: {e}")
            await asyncio.sleep(5)  # Wait 5 seconds before attempting to reconnect

async def main():
    tasks = []
    for symbol in SYMBOLS:
        tasks.append(listen_binance(symbol))
    
    await asyncio.gather(*tasks)  # Execute all listening tasks in parallel

# Start real-time listening for all symbols
asyncio.run(main())
