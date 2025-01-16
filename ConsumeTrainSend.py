from kafka import KafkaConsumer
from kafka import KafkaProducer
import json

KAFKA_BROKER = "localhost:9092"
TOPIC_1 = "DataForTraining"
TOPIC_2 = "ResultsForPlotting"
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT', 'GALAUSDT']

def consume_symbol_data(symbol):
    """
    Consume data for a specific symbol.
    
    Args:
        symbol (str): The symbol to follow (e.g., 'BTCUSDT').
    """
    if symbol not in SYMBOLS:
        raise ValueError(f"Symbol must be one of {SYMBOLS}")

    # Create the consumer
    consumer = KafkaConsumer(
        TOPIC_1,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        key_deserializer=lambda x: x.decode('utf-8') if x else None,
        group_id=f'group_{symbol}',  # Unique group for each symbol
        auto_offset_reset='latest'
    )

    print(f"Starting consumption for symbol: {symbol}")
    try:
        for message in consumer:
            # Check if the message corresponds to the requested symbol
            if message.key == symbol:
                print(f"\nReceived data for {symbol}:")
                print(f"Key: {message.key}")
                print(f"Value: {message.value}")
                # ZAK HERE YOU CAN PROCESS THE DATA AS YOU WANT
    except KeyboardInterrupt:
        print("\nStopping consumption...")
    finally:
        consumer.close()
        print("Consumer closed")
        
def create_producer(broker=KAFKA_BROKER):
    """
    Create a Kafka producer.
    
    Args:
        broker (str): The Kafka broker address (default: 'localhost:9092').
    
    Returns:
        KafkaProducer: A configured Kafka producer instance.
    """
    return KafkaProducer(
        bootstrap_servers=broker,
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        key_serializer=str.encode
    )

def send(producer, symbol, predictedresults):
    """
    Send predicted results to a Kafka topic.
    
    Args:
        producer (KafkaProducer): The Kafka producer.
        symbol (str): The symbol associated with the predictions (e.g., 'BTCUSDT').
        predictedresults (dict): The predicted results to send (e.g., metrics, predictions, etc.).
    """
    try:
        producer.send(
            TOPIC_2,
            value=predictedresults,  # The predicted results
            key=symbol  # Use the symbol as the key
        )
        print(f"Sent prediction result for {symbol}: {predictedresults}")
    except Exception as e:
        print(f"Failed to send prediction result for {symbol}: {e}")


if __name__ == "__main__":
    # Allow the user to choose a symbol to consume
    print("Available symbols to consume:")
    for idx, sym in enumerate(SYMBOLS, start=1):
        print(f"{idx}. {sym}")
    
    try:
        choice = int(input("Enter the number corresponding to the symbol you want to consume: "))
        if choice < 1 or choice > len(SYMBOLS):
            raise ValueError("Invalid choice. Please select a valid number.")
        
        selected_symbol = SYMBOLS[choice - 1]
        print(f"You selected: {selected_symbol}")
        
        # Start consuming data for the selected symbol
        consume_symbol_data(selected_symbol)
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nExiting.")