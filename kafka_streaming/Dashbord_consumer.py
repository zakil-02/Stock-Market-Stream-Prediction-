from kafka import KafkaConsumer
import json

# Kafka configuration
KAFKA_BROKER = "localhost:9092"
TOPIC_2 = "ResultsForPlotting"
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT', 'GALAUSDT']

def consume_predicted_results(symbol):
    """
    Consume data for a specific symbol based on the key (symbol).
    
    Args:
        symbol (str): The symbol to follow (e.g., 'BTCUSDT').
    """
    if symbol not in SYMBOLS:
        raise ValueError(f"Symbol must be one of {SYMBOLS}")
    
    # Create the consumer
    consumer = KafkaConsumer(
        TOPIC_2,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),  # Deserialize message values
        key_deserializer=lambda x: x.decode('utf-8') if x else None,  # Deserialize keys
        group_id=f'group_{symbol}',  # Unique consumer group for this symbol
        auto_offset_reset='latest'  # Start consuming from the latest message
    )
    
    print(f"Starting consumption for symbol: {symbol}")

    try:
        for message in consumer:
            if message.key == symbol:  # Check if the key matches the symbol
                print(f"\nReceived data for {symbol}:")
                print(f"Partition: {message.partition}, Offset: {message.offset}")
                print(f"Key: {message.key}")
                print(f"Value: {message.value}")
                # Add any additional processing logic here
    except KeyboardInterrupt:
        print("\nStopping consumption...")
    finally:
        consumer.close()
        print("Consumer closed")


