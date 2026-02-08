from kafka import KafkaConsumer, KafkaProducer
import json
from datetime import datetime
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from streamingModels.StreamRegressionModels import PARegressor, ARFRegressor, NNRegressor, HoeffdingTreeRegressor, BaggingRegressor, KNNRegressor

KAFKA_BROKER = "localhost:9092"
TOPIC_1 = "SymbolsData"
TOPIC_2 = "Results"
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT', 'GALAUSDT']

class ModelManager:
    def __init__(self):
        self.available_models = {
            1: ("Model 1 - PA Regressor", lambda: PARegressor()),
            2: ("Model 2 - Adaptive RandomForest", lambda: ARFRegressor()),
            3: ("Model 3 - NN Regressor", lambda: NNRegressor()),
            4: ("Model 4 - Bagging Regressor", lambda: BaggingRegressor()),
            5: ("Model 5 - KNN Regressor", lambda: KNNRegressor()),
        }
        self.active_models = {}

    def initialize_selected_models(self, selected_model_numbers):
        """Initialize the selected models."""
        self.active_models = {
            f"model_{num}": self.available_models[num][1]()
            for num in selected_model_numbers
        }
        return self.active_models

    def display_available_models(self):
        """Display available models for selection."""
        print("\nAvailable Models:")
        for num, (description, _) in self.available_models.items():
            print(f"{num}. {description}")

def create_kafka_producer():
    """Create and return a Kafka producer instance."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        key_serializer=str.encode
    )

def send_results(producer, symbol, predictions, real_value, metrics):
    """Send predictions and metrics to Kafka topic."""
    message = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "symbol": symbol,
        "predictions": predictions,
        "real_value": real_value,
        "metrics": metrics
    }
    try:
        producer.send(TOPIC_2, value=message, key=symbol)
        producer.flush()
        print(f"\nSent results for {symbol}:")
        print(f"Real value: {real_value}")
        print(f"Predictions: {predictions}")
        print(f"Metrics: {metrics}")
    except Exception as e:
        print(f"Error sending results: {e}")

def process_symbol_data(symbol, models):
    """Process data for a specific symbol using selected models."""
    consumer = KafkaConsumer(
        TOPIC_1,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        key_deserializer=lambda x: x.decode('utf-8') if x else None,
        group_id=f'group_{symbol}',
        auto_offset_reset='latest'
    )
    
    producer = create_kafka_producer()
    print(f"\nStarting consumption for {symbol} using {len(models)} models")
    
    last_X = None
    last_y = None

    try:
        for message in consumer:
            if message.key == symbol:
                instance = message.value
                y_new = instance['c']
                
                # Prepare input data for current iteration
                X_new = {
                    'start_time': datetime.fromtimestamp(instance['t'] / 1000).strftime('%d-%m-%Y %H:%M:%S'),
                    'end_time': datetime.fromtimestamp(instance['T'] / 1000).strftime('%d-%m-%Y %H:%M:%S'),
                    'open': instance['o'],
                    'high': instance['h'],
                    'low': instance['l'],
                    'close': instance['c'],
                    'volume': instance['v'],
                    'n_trades': instance['n'], 
                }
                
                # Only start prediction after we have a previous data point
                if (last_X is not None) and (last_y is not None):
                    # Process with each model
                    predictions = {}
                    metrics = {}
                    
                    for model_name, model in models.items():
                        # ONLINE LEARNING PROCESS:
                        # 1. Learn from previous candle (last_X) using current close price (y_new) as target
                        #    This teaches the model: "Given last_X features, the actual price was y_new"
                        model.learn_one(last_X, y_new)
                        
                        # 2. Predict next close price using current candle (X_new)
                        #    This asks: "Given X_new features, what will the next price be?"
                        predictions[model_name] = float(model.predict_one(X_new))

                        # Calculate metrics (comparing prediction with actual)
                        metrics[model_name] = model.get_metrics()

                    # Send results to Kafka for dashboard visualization
                    send_results(producer, symbol, predictions, y_new, metrics)
                
                # print(last_X)
                # print(last_y)
                # Update for next iteration
                last_X = X_new
                last_y = y_new

    except KeyboardInterrupt:
        print("\nStopping consumption...")
    finally:
        consumer.close()
        producer.close()
        print("Consumers and producer closed")

def get_user_selections():
    """Get symbol and model selections from user."""
    # Symbol selection
    print("\nAvailable symbols:")
    for idx, sym in enumerate(SYMBOLS, start=1):
        print(f"{idx}. {sym}")
    
    while True:
        try:
            symbol_choice = int(input("\nEnter the number corresponding to the symbol: "))
            if 1 <= symbol_choice <= len(SYMBOLS):
                selected_symbol = SYMBOLS[symbol_choice - 1]
                break
            print("Invalid choice. Please select a valid number.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Model selection
    model_manager = ModelManager()
    model_manager.display_available_models()
    
    while True:
        try:
            model_input = input("\nEnter model numbers to use (comma-separated, e.g., '1,2,3'): ")
            model_numbers = [int(x.strip()) for x in model_input.split(',')]
            
            if not model_numbers:
                print("Please select at least one model.")
                continue
                
            if not all(1 <= num <= len(model_manager.available_models) for num in model_numbers):
                print("Invalid model number(s). Please try again.")
                continue
                
            break
        except ValueError:
            print("Please enter valid numbers separated by commas.")
    
    selected_models = model_manager.initialize_selected_models(model_numbers)
    return selected_symbol, selected_models

if __name__ == "__main__":
    try:
        # Get user selections
        selected_symbol, selected_models = get_user_selections()
        
        print(f"\nStarting prediction system:")
        print(f"Selected symbol: {selected_symbol}")
        print(f"Selected models: {', '.join(selected_models.keys())}")
        
        # Start processing
        process_symbol_data(selected_symbol, selected_models)
        
    except KeyboardInterrupt:
        print("\nExiting the application...")
    except Exception as e:
        print(f"An error occurred: {e}")