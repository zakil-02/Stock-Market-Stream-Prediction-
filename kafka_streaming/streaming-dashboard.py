import streamlit as st
import plotly.graph_objects as go
from kafka import KafkaConsumer
import json
from datetime import datetime
import pandas as pd
import threading
import time

# Configuration Kafka
KAFKA_BROKER = "localhost:9092"
TOPIC_SYMBOLS = "SymbolsData"
TOPIC_RESULTS = "Results"
MAX_POINTS = 100

class DataManager:
    def __init__(self):
        self.data = pd.DataFrame()
        self.lock = threading.Lock()

    def update_data(self, message):
        """Mise à jour des données avec un nouveau message Kafka."""
        with self.lock:
            try:
                # Extraire les données du message
                new_data = {
                    'timestamp': datetime.strptime(message['timestamp'], '%Y-%m-%d %H:%M:%S'),
                    'symbol': message['symbol']
                }

                # Ajouter les prédictions pour chaque modèle
                for model_name, pred in message['predictions'].items():
                    new_data[f'pred_{model_name}'] = float(pred['value'])

                # Ajouter les métriques pour chaque modèle
                for model_name, metrics in message['metrics'].items():
                    new_data[f'mae_{model_name}'] = float(metrics.get('MAE', 0))
                    new_data[f'rmse_{model_name}'] = float(metrics.get('RMSE', 0))
                    new_data[f'r2_{model_name}'] = float(metrics.get('R2', 0))

                # Ajouter les vraies valeurs
                if 'truevalue' in message:
                    new_data['truevalue'] = float(message['truevalue']['current_close'])
                    new_data['truevalue_timestamp'] = datetime.strptime(message['truevalue']['timestamp'], '%Y-%m-%d %H:%M:%S')

                # Mise à jour du DataFrame
                new_df = pd.DataFrame([new_data])
                self.data = pd.concat([self.data, new_df], ignore_index=True)

                # Limiter à MAX_POINTS
                if len(self.data) > MAX_POINTS:
                    self.data = self.data.iloc[-MAX_POINTS:]

            except Exception as e:
                print(f"Erreur lors de la mise à jour des données : {e}")


def kafka_consumer_thread(data_manager):
    """Thread pour consommer les messages Kafka."""
    consumer = KafkaConsumer(
        TOPIC_RESULTS,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest'
    )

    for message in consumer:
        try:
            data_manager.update_data(message.value)
        except Exception as e:
            print(f"Erreur dans le thread Kafka : {e}")


def get_active_models(data):
    """Extraire les modèles actifs des colonnes du DataFrame."""
    pred_columns = [col for col in data.columns if col.startswith('pred_')]
    return [col.replace('pred_', '') for col in pred_columns]


def create_price_plot(data, models):
    fig = go.Figure()

    # Ajouter les prédictions des modèles
    for model in models:
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data[f'pred_{model}'],
            name=f'Prédiction - {model}',
            mode='lines+markers'
        ))

    # Ajouter les vraies valeurs
    if 'truevalue' in data.columns and 'truevalue_timestamp' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['truevalue_timestamp'],
            y=data['truevalue'],
            name='Valeurs Réelles',
            mode='lines+markers',
            line=dict(color='red', dash='dot')
        ))

    fig.update_layout(
        title='Prédictions des prix et vraies valeurs',
        xaxis_title='Temps',
        yaxis_title='Prix',
        height=400,
        hovermode='x unified'
    )
    return fig



def create_metric_plot(data, models, metric):
    """Créer un graphique pour une métrique donnée."""
    fig = go.Figure()

    for model in models:
        metric_col = f'{metric.lower()}_{model}'
        if metric_col in data.columns:
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data[metric_col],
                name=f'{metric.upper()} - {model}',
                mode='lines+markers'
            ))

    fig.update_layout(
        title=f'{metric.upper()} au fil du temps',
        xaxis_title='Temps',
        yaxis_title=metric.upper(),
        height=300,
        hovermode='x unified'
    )
    return fig


def main():
    st.set_page_config(page_title="Dashboard Kafka", layout="wide")
    st.title("Dashboard en temps réel : Prédictions et métriques")

    # Initialisation
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

    while True:
        with st.session_state.data_manager.lock:
            if not st.session_state.data_manager.data.empty:
                data = st.session_state.data_manager.data
                models = get_active_models(data)

                if models:
                    with header:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader(f"Symbole : {data['symbol'].iloc[-1]}")
                        with col2:
                            st.subheader(f"Modèles actifs : {len(models)}")

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

                        with col2:
                            st.plotly_chart(
                                create_metric_plot(data, models, 'rmse'),
                                use_container_width=True
                            )
            else:
                with header:
                    st.info("En attente des données Kafka...")

        time.sleep(1)
        st.rerun()


if __name__ == "__main__":
    main()