import streamlit as st
import plotly.graph_objects as go
from kafka import KafkaConsumer
import json
from datetime import datetime
import pandas as pd
import threading
import time

# Constants
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "Results"
MAX_POINTS = 800

# Modern color schemes
DARK_THEME = {
    'bg_primary': '#0E1117',
    'bg_secondary': '#1E2130',
    'text_primary': '#FAFAFA',
    'text_secondary': '#B0B0B0',
    'accent_1': '#00D9FF',
    'accent_2': '#FF6B6B',
    'accent_3': '#4ECDC4',
    'accent_4': '#FFE66D',
    'success': '#51CF66',
    'warning': '#FFD93D',
    'error': '#FF6B6B',
    'chart_bg': '#1E2130',
    'grid_color': '#2D3142'
}

LIGHT_THEME = {
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F8F9FA',
    'text_primary': '#212529',
    'text_secondary': '#6C757D',
    'accent_1': '#0066CC',
    'accent_2': '#DC3545',
    'accent_3': '#20C997',
    'accent_4': '#FFC107',
    'success': '#28A745',
    'warning': '#FFC107',
    'error': '#DC3545',
    'chart_bg': '#FFFFFF',
    'grid_color': '#E9ECEF'
}

MODEL_COLORS = ['#00D9FF', '#FF6B6B', '#4ECDC4', '#FFE66D', '#A78BFA', '#FB923C']


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
                    'real_value': float(message['real_value'])
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


def create_price_plot(data, models, theme):
    """Create enhanced price prediction plot"""
    fig = go.Figure()
    
    # Add real values with enhanced styling
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['real_value'],
        name='Real Price',
        line=dict(color=theme['accent_2'], width=3),
        mode='lines',
        hovertemplate='<b>Real Price</b><br>%{y:.4f}<extra></extra>'
    ))
    
    # Add predicted prices with distinct colors
    for i, model in enumerate(models):
        model_display = model.replace('model_', 'Model ')
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data[f'pred_{model}'],
            name=model_display,
            line=dict(color=MODEL_COLORS[i % len(MODEL_COLORS)], width=2, dash='dot'),
            mode='lines',
            hovertemplate=f'<b>{model_display}</b><br>%{{y:.4f}}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>Real-Time Price Predictions</b> • {data["symbol"].iloc[-1]}',
            x=0.5,
            xanchor='center',
            font=dict(size=24, color=theme['text_primary'], family='Arial Black')
        ),
        xaxis=dict(
            title='Time',
            gridcolor=theme['grid_color'],
            showgrid=True,
            color=theme['text_secondary']
        ),
        yaxis=dict(
            title='Price (USDT)',
            gridcolor=theme['grid_color'],
            showgrid=True,
            color=theme['text_secondary']
        ),
        plot_bgcolor=theme['chart_bg'],
        paper_bgcolor=theme['bg_secondary'],
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary'])
        ),
        margin=dict(l=60, r=60, t=100, b=60),
        font=dict(color=theme['text_primary'])
    )
    
    return fig


def create_metric_plot(data, models, metric, theme):
    """Create enhanced metric plot"""
    fig = go.Figure()
    
    metric_info = {
        'mae': {'title': 'Mean Absolute Error', 'format': '.4f'},
        'rmse': {'title': 'Root Mean Square Error', 'format': '.4f'},
        'r2': {'title': 'R² Score', 'format': '.4f'},
        'mape': {'title': 'Mean Absolute Percentage Error', 'format': '.2f'}
    }
    
    info = metric_info.get(metric, {'title': metric.upper(), 'format': '.4f'})
    
    for i, model in enumerate(models):
        metric_col = f'{metric.lower()}_{model}'
        if metric_col in data.columns:
            model_display = model.replace('model_', 'Model ')
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data[metric_col],
                name=model_display,
                line=dict(color=MODEL_COLORS[i % len(MODEL_COLORS)], width=2.5),
                mode='lines',
                fill='tozeroy',
                fillcolor=f'rgba{tuple(list(int(MODEL_COLORS[i % len(MODEL_COLORS)][j:j+2], 16) for j in (1, 3, 5)) + [0.1])}',
                hovertemplate=f'<b>{model_display}</b><br>%{{y:{info["format"]}}}<extra></extra>'
            ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>{info["title"]}</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color=theme['text_primary'], family='Arial')
        ),
        xaxis=dict(
            title='',
            gridcolor=theme['grid_color'],
            showgrid=True,
            color=theme['text_secondary']
        ),
        yaxis=dict(
            title=metric.upper(),
            gridcolor=theme['grid_color'],
            showgrid=True,
            color=theme['text_secondary']
        ),
        plot_bgcolor=theme['chart_bg'],
        paper_bgcolor=theme['bg_secondary'],
        height=280,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary'], size=10)
        ),
        margin=dict(l=50, r=50, t=70, b=50),
        font=dict(color=theme['text_primary'])
    )
    
    return fig


def get_custom_css(theme):
    """Generate custom CSS based on theme"""
    return f"""
    <style>
        /* Main container styling */
        .stApp {{
            background: linear-gradient(135deg, {theme['bg_primary']} 0%, {theme['bg_secondary']} 100%);
        }}
        
        /* Metric cards */
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 700;
            color: {theme['accent_1']};
        }}
        
        [data-testid="stMetricLabel"] {{
            font-size: 1rem;
            font-weight: 500;
            color: {theme['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Chart containers */
        .stPlotlyChart {{
            background: {theme['bg_secondary']};
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            padding: 20px;
            margin: 10px 0;
            border: 1px solid {theme['grid_color']};
        }}
        
        /* Title styling */
        h1 {{
            color: {theme['text_primary']};
            font-weight: 800;
            text-align: center;
            padding: 20px 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            background: linear-gradient(90deg, {theme['accent_1']}, {theme['accent_3']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        /* Info box */
        .stAlert {{
            background: {theme['bg_secondary']};
            border-left: 4px solid {theme['accent_1']};
            border-radius: 10px;
            padding: 15px;
            color: {theme['text_primary']};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: {theme['bg_secondary']};
            border-right: 1px solid {theme['grid_color']};
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(90deg, {theme['accent_1']}, {theme['accent_3']});
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 217, 255, 0.4);
        }}
        
        /* Metric container */
        div[data-testid="metric-container"] {{
            background: {theme['bg_secondary']};
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            border: 1px solid {theme['grid_color']};
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 20px;
            color: {theme['text_secondary']};
            font-size: 0.9rem;
            margin-top: 40px;
        }}
    </style>
    """


def main():
    st.set_page_config(
        page_title="Crypto Trading Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    
    # Get current theme
    theme = DARK_THEME if st.session_state.theme == 'dark' else LIGHT_THEME
    
    # Apply custom CSS
    st.markdown(get_custom_css(theme), unsafe_allow_html=True)
    
    # Header with theme toggle
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown("### 📈")
    with col2:
        st.title("Real-Time Crypto Trading Predictions")
    with col3:
        if st.button("🌓 Theme"):
            st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
            st.rerun()
    
    # Initialize data manager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
        consumer_thread = threading.Thread(
            target=kafka_consumer_thread,
            args=(st.session_state.data_manager,),
            daemon=True
        )
        consumer_thread.start()
    
    # Main content
    header_metrics = st.container()
    price_chart = st.empty()
    metrics_section = st.container()
    
    while True:
        with st.session_state.data_manager.lock:
            if not st.session_state.data_manager.data.empty:
                data = st.session_state.data_manager.data
                models = get_active_models(data)
                
                if models:
                    # Header metrics
                    with header_metrics:
                        cols = st.columns(4)
                        
                        with cols[0]:
                            st.metric(
                                "Trading Pair",
                                data['symbol'].iloc[-1],
                                delta=None
                            )
                        
                        with cols[1]:
                            current_price = data['real_value'].iloc[-1]
                            prev_price = data['real_value'].iloc[-2] if len(data) > 1 else current_price
                            delta = current_price - prev_price
                            st.metric(
                                "Current Price",
                                f"${current_price:.4f}",
                                delta=f"{delta:+.4f}",
                                delta_color="normal"
                            )
                        
                        with cols[2]:
                            st.metric(
                                "Active Models",
                                len(models),
                                delta=None
                            )
                        
                        with cols[3]:
                            if len(data) > 0:
                                avg_mae = sum(data[f'mae_{model}'].iloc[-1] for model in models) / len(models)
                                st.metric(
                                    "Avg MAE",
                                    f"{avg_mae:.4f}",
                                    delta=None
                                )
                    
                    # Price prediction chart
                    price_chart.plotly_chart(
                        create_price_plot(data, models, theme),
                        use_container_width=True,
                        key=f"price_{time.time()}"
                    )
                    
                    # Metrics charts
                    with metrics_section:
                        st.markdown("### 📊 Performance Metrics")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.plotly_chart(
                                create_metric_plot(data, models, 'mae', theme),
                                use_container_width=True,
                                key=f"mae_{time.time()}"
                            )
                            st.plotly_chart(
                                create_metric_plot(data, models, 'r2', theme),
                                use_container_width=True,
                                key=f"r2_{time.time()}"
                            )
                        
                        with col2:
                            st.plotly_chart(
                                create_metric_plot(data, models, 'rmse', theme),
                                use_container_width=True,
                                key=f"rmse_{time.time()}"
                            )
                            st.plotly_chart(
                                create_metric_plot(data, models, 'mape', theme),
                                use_container_width=True,
                                key=f"mape_{time.time()}"
                            )
                    
                    # Footer
                    st.markdown(
                        f'<div class="footer">By: Zakaria Akil | Real-Time Crypto Predictions v2.0</div>',
                        unsafe_allow_html=True
                    )
            else:
                with header_metrics:
                    st.info("🔄 Waiting for real-time data from Kafka... Make sure the producer and consumer are running.")
        
        time.sleep(4)
        st.rerun()


if __name__ == "__main__":
    main()
