import pyspark
import time
import requests
import json
from kafka import KafkaProducer, KafkaConsumer


# Kafka configuration
KAFKA_BROKER = "localhost:9092"
TOPIC = "BTCUSDT"

# Binance API URL
API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

producer = KafkaProducer(bootstrap_servers="localhost:9092")


def fetch_btc_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None
    

def produce_to_kafka(data):
    if not data:
        return
    
    try:
        producer.send(TOPIC, value=json.dumps(data).encode())
        producer.flush() # Ensure all messages are sent
    except Exception as e:
        print(f"Error producing message to Kafka: {e}")
    

def main():
    print("Starting data ingestion...")
    while True:
        btc_data = fetch_btc_data()
        if btc_data:
            print(f"Fetched BTCUSDT price: {btc_data['price']}")
            produce_to_kafka(btc_data)
        else:
            print("No data fetched.")
        
        time.sleep(1)  #1 seconds between each 2 requests