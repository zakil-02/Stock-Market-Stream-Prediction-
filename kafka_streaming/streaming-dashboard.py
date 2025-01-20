import streamlit as st
import plotly.graph_objects as go
from kafka import KafkaConsumer
import json
from datetime import datetime
import pandas as pd
import threading
import queue
import time

# Constants
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "Results"
MAX_POINTS = 100

class DataManager:
    def __init__(self):
        self.data = pd.DataFrame()
        self.lock = threading.Lock()
        
    def update_data(self, message):
        """Update the dataframe with new data"""
        with self.lock:
            try:
                # Extract timestamp and symbol
                new_data = {
                    'timestamp': message['timestamp'],
                    'symbol': message['symbol']
                }
                
                # Add predictions for each model
                for model_name, pred_value in message['predictions'].items():
                    new_data[f'pred_{model_name}'] = float(pred_value)
                
                # Add metrics for each model
                for model_name, metrics in message['metrics'].items():
                    new_data[f'mae_{model_name}'] = float(metrics.get('MAE', 0))
                    new_data[f'rmse_{model_name}'] = float(metrics.get('RMSE', 0))
                    new_data[f'r2_{model_name}'] = float(metrics.get('R2', 0))
                
                # Convert to DataFrame and append
                new_df = pd.DataFrame([new_data])
                self.data = pd.concat([self.data, new_df], ignore_index=True)
                
                # Keep only last MAX_POINTS
                if len(self.data) > MAX_POINTS:
                    self.data = self.data.iloc[-MAX_POINTS:]
                
            except Exception as e:
                print(f"Error updating data: {e}")
                print(f"Message structure: {message}")

def kafka_consumer_thread(data_manager):
    """Thread function to consume Kafka messages"""
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest'
    )
    
    for message in consumer:
        try:
            data_manager.update_data(message.value)
            time.sleep(0.1)
        except Exception as e:
            print(f"Error in consumer thread: {e}")

def get_active_models(data):
    """Extract active model names from the DataFrame columns"""
    pred_columns = [col for col in data.columns if col.startswith('pred_')]
    return [col.replace('pred_', '') for col in pred_columns]

def create_price_plot(data, models):
    """Create price comparison plot"""
    fig = go.Figure()
    
    # Add predicted prices for each model
    colors = ['navy', 'green', 'black', 'orange']
    for i, model in enumerate(models):
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data[f'pred_{model}'],
            name=f'Model {model} Prediction',
            line=dict(color=colors[i % len(colors)]),
            mode='lines+markers',
            marker=dict(
            size=8,  # Size of the markers
            color=colors[i % len(colors)],  # Marker fill color
            line=dict(
                color='black',  # Edge color
                width=2  # Width of the edge
                )
            )
        ))
    
    fig.update_layout(
        title=f'Predicted Prices for {data["symbol"].iloc[-1]}',
        xaxis_title='Time',
        yaxis_title='Price',
        height=400,
        hovermode='x unified'
    )
    return fig

def create_metric_plot(data, models, metric):
    """Create plot for a specific metric"""
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'purple']
    for i, model in enumerate(models):
        metric_col = f'{metric.lower()}_{model}'
        if metric_col in data.columns:
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data[metric_col],
                name=f'Model {model}',
                line=dict(color=colors[i % len(colors)]),
                mode='lines+markers',
                marker=dict(
                size=6,  # Size of the markers
                color=colors[i % len(colors)],  # Marker fill color
                line=dict(
                    color='black',  # Edge color
                    width=1  # Width of the edge
                    )
                )
            ))
    
    fig.update_layout(
        title=f'{metric.upper()} Over Time',
        xaxis_title='Time',
        yaxis_title=metric.upper(),
        height=300,
        hovermode='x unified'
    )
    return fig

def main():
    st.set_page_config(page_title="Trading Predictions Dashboard", layout="wide")
    st.title("Real-time Trading Predictions Dashboard")
    
    # Initialize session state
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
        consumer_thread = threading.Thread(
            target=kafka_consumer_thread,
            args=(st.session_state.data_manager,),
            daemon=True
        )
        consumer_thread.start()

    # Create placeholders
    header = st.container()
    price_plot = st.empty()
    metrics_container = st.container()

    while True:
        with st.session_state.data_manager.lock:
            if not st.session_state.data_manager.data.empty:
                data = st.session_state.data_manager.data
                models = get_active_models(data)
                
                if models:
                    # Update header information
                    with header:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader(f"Symbol: {data['symbol'].iloc[-1]}")
                        with col2:
                            st.subheader(f"Active Models: {len(models)}")
                    
                    # Update price plot
                    price_plot.plotly_chart(
                        create_price_plot(data, models),
                        use_container_width=True
                    )
                    
                    # Update metrics plots
                    with metrics_container:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.plotly_chart(
                                create_metric_plot(data, models, 'mae'),
                                use_container_width=True
                            )
                            st.plotly_chart(
                                create_metric_plot(data, models, 'r2'),
                                use_container_width=True
                            )
                        
                        with col2:
                            st.plotly_chart(
                                create_metric_plot(data, models, 'rmse'),
                                use_container_width=True
                            )
            else:
                with header:
                    st.info("Waiting for data from Kafka...")

        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()