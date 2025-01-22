from kafka import KafkaConsumer, KafkaProducer
import json
from datetime import datetime
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamingModels.streamingRegressionModels import ModelTester
from streamingModels.streamingClassificationModels import ModelTesterClassifier

KAFKA_BROKER = "localhost:9092"
TOPIC_1 = "SymbolsData"
TOPIC_2 = "Results"
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT', 'GALAUSDT']

class ModelManager:
    def __init__(self):
        # Définition des modèles de régression
        self.available_regression_models = {
            1: ("Regression - PA Regressor", self._create_pa_regressor),
            2: ("Regression - Bagging Regressor", self._create_bagging_regressor),
            3: ("Regression - Hoeffding Tree Regressor", self._create_hoeffding_regressor)
        }
        # Définition des modèles de classification
        self.available_classification_models = {
            4: ("Classification - PA Classifier", self._create_pa_classifier),
            5: ("Classification - Hoeffding Tree Classifier", self._create_hoeffding_classifier),
            6: ("Classification - Random Forest Classifier", self._create_forest_classifier)
        }
        self.active_models = {}
        self.previous_close = None

    # Méthodes pour les modèles de régression
    def _create_pa_regressor(self):
        tester = ModelTester()
        tester.init_pa_model()
        return ('regression', tester, 'pa')

    def _create_bagging_regressor(self):
        tester = ModelTester()
        tester.init_bagging_model()
        return ('regression', tester, 'bagging')

    def _create_hoeffding_regressor(self):
        tester = ModelTester()
        tester.init_hoeffding_model()
        return ('regression', tester, 'hoeffding')

    # Méthodes pour les modèles de classification
    def _create_pa_classifier(self):
        tester = ModelTesterClassifier()
        tester.init_pa_model()
        return ('classification', tester, 'pa')

    def _create_hoeffding_classifier(self):
        tester = ModelTesterClassifier()
        tester.init_hoeffding_model()
        return ('classification', tester, 'hoeffding')

    def _create_forest_classifier(self):
        tester = ModelTesterClassifier()
        tester.init_forest_model()
        return ('classification', tester, 'forest')

    def initialize_selected_models(self, selected_model_numbers):
        """Initialize the selected models."""
        self.active_models = {}
        
        for num in selected_model_numbers:
            if num <= 3:  # Modèles de régression
                creator = self.available_regression_models[num][1]
            else:  # Modèles de classification
                creator = self.available_classification_models[num][1]
            
            model_type, model_instance, model_name = creator()
            self.active_models[f"model_{num}"] = (model_type, model_instance, model_name)
        
        return self.active_models

    def display_available_models(self):
        """Display available models for selection."""
        print("\nAvailable Regression Models:")
        for num, (description, _) in self.available_regression_models.items():
            print(f"{num}. {description}")
            
        print("\nAvailable Classification Models:")
        for num, (description, _) in self.available_classification_models.items():
            print(f"{num}. {description}")
def create_kafka_producer():
    """Create and return a Kafka producer instance."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        key_serializer=str.encode
    )

def send_results(producer, symbol, predictions, metrics, truevalue):
    """Send predictions and metrics to Kafka topic."""
    message = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "symbol": symbol,
        "predictions": predictions,
        "metrics": metrics,
        "truevalue" : truevalue
    }
    try:
        producer.send(TOPIC_2, value=message, key=symbol)
        producer.flush()
        print(f"\nSent results for {symbol}:")
        print(f"Predictions: {predictions}")
        print(f"Metrics: {metrics}")
        print(f"truevalue: {truevalue}")
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
        auto_offset_reset='latest',
        consumer_timeout_ms=10000
    )
    producer = create_kafka_producer()
    print(f"\nStarting consumption for {symbol} using {len(models)} models")
    
    previous_close = None
    
    try:
        for message in consumer:
            if message.key == symbol:
                instance = message.value
                # Prepare input data
                X_new = {
                    'start_time': datetime.fromtimestamp(instance['t'] / 1000).strftime('%d-%m-%Y %H:%M:%S'),
                    'high': float(instance['h']),
                    'low': float(instance['l']),
                    'open': float(instance['o']),
                    'close': float(instance['c']),
                    'volume': float(instance['v']),
                    'n_trades': float(instance['n'])
                }
                current_close = float(instance['c'])

                # Process with each model
                predictions = {}
                truevalue= {
                    'current_close': current_close,
                    'timestamp': datetime.fromtimestamp(instance['t'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                }
                metrics = {}
                
                for model_name, (model_type, model, model_subtype) in models.items():
                    try:
                        if model_type == 'regression':
                            prediction, current_metrics = model.learn_and_predict(
                                X_new, current_close, model_type=model_subtype
                            )
                        else:  # classification
                            if previous_close is not None:
                                prediction, current_metrics = model.learn_and_predict(
                                    X_new, previous_close, model_type=model_subtype
                                )
                            else:
                                # Skip first iteration for classification as we need previous close
                                continue
                                
                        if prediction is not None:
                            predictions[model_name] = {
                                'type': model_type,
                                'value': float(prediction) if model_type == 'regression' else int(prediction)
                            }
                            metrics[model_name] = current_metrics
                            
                    except Exception as e:
                        print(f"Error processing model {model_name}: {str(e)}")
                        continue

                # Update previous close for next iteration
                previous_close = current_close

                # Send results to Kafka if we have predictions
                if predictions:
                    send_results(producer, symbol, predictions, metrics, truevalue)
                
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
                
            if not all(1 <= num <= (len(model_manager.available_regression_models)+len(model_manager.available_classification_models)) for num in model_numbers):
                print("Invalid model number(s). Please try again.")
                continue
                
            break
        except ValueError:
            print("Please enter valid numbers separated by commas.")
    
    selected_models = model_manager.initialize_selected_models(model_numbers)
    return selected_symbol, selected_models

if __name__ == "__main__":
    try:
        selected_symbol, selected_models = get_user_selections()
        
        print(f"\nStarting prediction system:")
        print(f"Selected symbol: {selected_symbol}")
        print(f"Selected models: {', '.join(selected_models.keys())}")
        print("\nModel types:")
        for name, (type_, _, subtype) in selected_models.items():
            print(f"{name}: {type_} ({subtype})")
        
        process_symbol_data(selected_symbol, selected_models)
        
    except KeyboardInterrupt:
        print("\nExiting the application...")
    except Exception as e:
        print(f"An error occurred: {e}")