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
MAX_POINTS = 800


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


class DataManager:
    def __init__(self):
        self.data = pd.DataFrame()
        self.lock = threading.Lock()
        
    def update_data(self, message):
        with self.lock:
            try:
                new_data = {
                    'timestamp': message['timestamp'],
                    'symbol': message['symbol'],
                    'real_value': float(message['real_value'])  # Add real value
                }
                
                # Add predictions
                for model_name, pred_value in message['predictions'].items():
                    new_data[f'pred_{model_name}'] = float(pred_value)
                
                # Add metrics
                for model_name, metrics in message['metrics'].items():
                    new_data[f'mae_{model_name}'] = float(metrics.get('MAE', 0))
                    new_data[f'rmse_{model_name}'] = float(metrics.get('RMSE', 0))
                    new_data[f'r2_{model_name}'] = float(metrics.get('R2', 0))
                    new_data[f'mape_{model_name}'] = float(metrics.get('MAPE', 0))
                
                new_df = pd.DataFrame([new_data])
                self.data = pd.concat([self.data, new_df], ignore_index=True)
                
                if len(self.data) > MAX_POINTS:
                    self.data = self.data.iloc[-MAX_POINTS:]
                
            except Exception as e:
                print(f"Error updating data: {e}")
                print(f"Message structure: {message}")

def create_price_plot(data, models):
    fig = go.Figure()
    
    # Add real values
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['real_value'],
        name='Real Price',
        line=dict(color='red', width=2.5, dash='solid'),
        mode='lines'
    ))
    
    # Add predicted prices
    colors = ['navy', 'green', 'black', 'orange']
    for i, model in enumerate(models):
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data[f'pred_{model}'],
            name=f'Model {model} Prediction',
            line=dict(color=colors[i % len(colors)], width=1.5, dash='dot'),
            mode='lines'
        ))
    
    fig.update_layout(
        title=dict(
            text=f'Real vs Predicted Prices - {data["symbol"].iloc[-1]}',
            x=0.5,
            font=dict(size=20)
        ),
        xaxis_title='Time',
        yaxis_title='Price',
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    return fig

def create_metric_plot(data, models, metric):
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'purple']
    for i, model in enumerate(models):
        metric_col = f'{metric.lower()}_{model}'
        if metric_col in data.columns:
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data[metric_col],
                name=f'Model {model}',
                line=dict(color=colors[i % len(colors)], width=1.8),
                mode='lines'
            ))
    
    fig.update_layout(
        title=dict(
            text=f'{metric.upper()} Over Time',
            x=0.5,
            font=dict(size=16)
        ),
        xaxis_title='Time',
        yaxis_title=metric.upper(),
        height=250,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=60, b=50)
    )
    return fig


def main():
    st.set_page_config(page_title="Trading Predictions Dashboard", layout="wide")
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stPlotlyChart {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 10px;
        }
        h1 {
            padding-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Real-time Trading Predictions Dashboard")
    
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
        consumer_thread = threading.Thread(
            target=kafka_consumer_thread,
            args=(st.session_state.data_manager,),
            daemon=True
        )
        consumer_thread.start()

    header = st.container()
    price_plot = st.empty()
    metrics_container = st.container()

    # Use st.cache_data to prevent constant re-rendering
    @st.cache_data
    def process_data(data):
        models = get_active_models(data)
        return models

    # Use st.experimental_connection for Kafka data
    data_container = st.empty()

    while True:
        with st.session_state.data_manager.lock:
            if not st.session_state.data_manager.data.empty:
                data = st.session_state.data_manager.data
                models = process_data(data)
                
                if models:
                    with header:
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Symbol", data['symbol'].iloc[-1])
                        with cols[1]:
                            st.metric("Current Price", f"{data['real_value'].iloc[-1]:.4f}")
                        with cols[2]:
                            st.metric("Active Models", len(models))
                        # with cols[3]:
                        #     latest_mae = data[f'mae_{models[0]}'].iloc[-1]
                        #     st.metric("Latest MAE", f"{latest_mae:.4f}")
                    
                    price_plot.plotly_chart(
                        create_price_plot(data, models),
                        use_container_width=True
                    )
                    
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
                            # Add MAPE plot
                            st.plotly_chart(
                                create_metric_plot(data, models, 'mape'),
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

        # Use st.experimental_rerun for smoother updates
        time.sleep(4)
        st.rerun()

if __name__ == "__main__":
    main()