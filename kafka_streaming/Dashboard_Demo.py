"""
Demo version of the enhanced dashboard that simulates data without requiring Kafka.
This allows you to see the UI and features without setting up the full streaming pipeline.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import time
import random
import numpy as np

# Constants
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


class DemoDataGenerator:
    """Generates simulated cryptocurrency data for demo purposes"""
    
    def __init__(self):
        self.base_price = 45000.0  # Starting BTC price
        self.time_start = datetime.now() - timedelta(minutes=100)
        self.data_points = []
        self.models = ['model_1', 'model_2', 'model_3']
        
        # Generate initial data
        for i in range(100):
            self._generate_next_point(i)
    
    def _generate_next_point(self, index):
        """Generate a single data point"""
        timestamp = (self.time_start + timedelta(minutes=index)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Simulate price movement with trend and noise
        trend = 0.0001 * index
        noise = random.gauss(0, 50)
        real_price = self.base_price + trend * self.base_price + noise
        
        # Generate predictions with varying accuracy
        predictions = {}
        metrics = {}
        
        for i, model in enumerate(self.models):
            # Each model has different characteristics
            model_bias = (i - 1) * 20  # Some models over/under predict
            model_noise = random.gauss(0, 30 + i * 10)
            pred_price = real_price + model_bias + model_noise
            predictions[model] = pred_price
            
            # Calculate cumulative metrics
            mae = abs(pred_price - real_price) + random.uniform(10, 50)
            rmse = mae * 1.2 + random.uniform(5, 20)
            r2 = max(0, min(1, 0.95 - i * 0.1 + random.uniform(-0.05, 0.05)))
            mape = (mae / real_price) * 100
            
            metrics[model] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'mape': mape
            }
        
        data_point = {
            'timestamp': timestamp,
            'symbol': 'BTCUSDT',
            'real_value': real_price
        }
        
        # Add predictions
        for model, pred in predictions.items():
            data_point[f'pred_{model}'] = pred
        
        # Add metrics
        for model, metric_dict in metrics.items():
            data_point[f'mae_{model}'] = metric_dict['mae']
            data_point[f'rmse_{model}'] = metric_dict['rmse']
            data_point[f'r2_{model}'] = metric_dict['r2']
            data_point[f'mape_{model}'] = metric_dict['mape']
        
        self.data_points.append(data_point)
        
        if len(self.data_points) > MAX_POINTS:
            self.data_points.pop(0)
    
    def get_dataframe(self):
        """Return current data as DataFrame"""
        return pd.DataFrame(self.data_points)
    
    def add_new_point(self):
        """Add a new data point (simulating real-time updates)"""
        index = len(self.data_points)
        self._generate_next_point(index)


def get_active_models(data):
    """Extract active model names from the DataFrame columns"""
    pred_columns = [col for col in data.columns if col.startswith('pred_')]
    return [col.replace('pred_', '') for col in pred_columns]


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
        hovertemplate='<b>Real Price</b><br>$%{y:.2f}<extra></extra>'
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
            hovertemplate=f'<b>{model_display}</b><br>$%{{y:.2f}}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>Real-Time Price Predictions</b> • {data["symbol"].iloc[-1]} (DEMO MODE)',
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
        'mae': {'title': 'Mean Absolute Error', 'format': '.2f'},
        'rmse': {'title': 'Root Mean Square Error', 'format': '.2f'},
        'r2': {'title': 'R² Score', 'format': '.4f'},
        'mape': {'title': 'Mean Absolute Percentage Error', 'format': '.2f'}
    }
    
    info = metric_info.get(metric, {'title': metric.upper(), 'format': '.4f'})
    
    for i, model in enumerate(models):
        metric_col = f'{metric.lower()}_{model}'
        if metric_col in data.columns:
            model_display = model.replace('model_', 'Model ')
            
            # Convert hex color to rgba for fill
            hex_color = MODEL_COLORS[i % len(MODEL_COLORS)]
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data[metric_col],
                name=model_display,
                line=dict(color=hex_color, width=2.5),
                mode='lines',
                fill='tozeroy',
                fillcolor=f'rgba({r},{g},{b},0.1)',
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
        
        /* Demo badge */
        .demo-badge {{
            background: linear-gradient(90deg, {theme['accent_1']}, {theme['accent_3']});
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            margin: 10px 0;
        }}
    </style>
    """


def main():
    st.set_page_config(
        page_title="Crypto Trading Dashboard - Demo",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    
    # Initialize data generator
    if 'data_generator' not in st.session_state:
        st.session_state.data_generator = DemoDataGenerator()
    
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
        st.markdown('<div class="demo-badge">🎮 DEMO MODE - Simulated Data</div>', unsafe_allow_html=True)
    with col3:
        if st.button("🌓 Theme"):
            st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
            st.rerun()
    
    # Info message
    st.info("📊 This is a demo version showing the enhanced UI. Real version connects to Kafka for live cryptocurrency data.")
    
    # Main content
    header_metrics = st.container()
    price_chart = st.empty()
    metrics_section = st.container()
    
    # Get data
    data = st.session_state.data_generator.get_dataframe()
    models = get_active_models(data)
    
    if not data.empty and models:
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
                    f"${current_price:.2f}",
                    delta=f"{delta:+.2f}",
                    delta_color="normal"
                )
            
            with cols[2]:
                st.metric(
                    "Active Models",
                    len(models),
                    delta=None
                )
            
            with cols[3]:
                avg_mae = sum(data[f'mae_{model}'].iloc[-1] for model in models) / len(models)
                st.metric(
                    "Avg MAE",
                    f"${avg_mae:.2f}",
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
            f'<div class="footer">By: Zakaria Akil | Real-Time Crypto Predictions v2.0 | Demo Mode</div>',
            unsafe_allow_html=True
        )
    
    # Add new data point and refresh
    time.sleep(2)
    st.session_state.data_generator.add_new_point()
    st.rerun()


if __name__ == "__main__":
    main()
