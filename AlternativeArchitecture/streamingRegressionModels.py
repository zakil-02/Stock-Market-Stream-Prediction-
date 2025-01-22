from river import compose, preprocessing, metrics, ensemble, tree, linear_model
from datetime import datetime
import numpy as np

class ModelTester:
    def __init__(self):
        # Create a preprocessing pipeline with feature scaling
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler())
        )
        # Initialize metrics for tracking performance
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()
        
        # Initialize the models
        self.bagging_model = None
        self.hoeffding_model = None
        self.pa_model = None

    def _extract_features(self, X):
        """Extract and compute additional features from the raw data."""
        features = {
            'open': float(X['open']),
            'high': float(X['high']),
            'low': float(X['low']),
            'close': float(X['close']),
            'volume': float(X['volume']),
            'n_trades': float(X['n_trades']),
            # Add price differences
            'high_low_diff': float(X['high']) - float(X['low']),
            'close_open_diff': float(X['close']) - float(X['open']),
            # Add price ratios
            'high_low_ratio': float(X['high']) / float(X['low']) if float(X['low']) != 0 else 1.0,
            'close_open_ratio': float(X['close']) / float(X['open']) if float(X['open']) != 0 else 1.0,
            # Volume-weighted features
            'volume_price_ratio': float(X['volume']) * float(X['close']),
        }
        # Add time-based features
        dt = datetime.strptime(X['start_time'], '%d-%m-%Y %H:%M:%S')
        features.update({
            'hour': dt.hour,
            'minute': dt.minute,
            'day_of_week': dt.weekday(),
        })
        return features

    def init_bagging_model(self, n_models=10):
        """Initialize BaggingRegressor model"""
        self.bagging_model = ensemble.BaggingRegressor(
            model=linear_model.LinearRegression(),
            n_models=n_models,
            seed=42
        )
        return self

    def init_hoeffding_model(self):
        """Initialize HoeffdingTreeRegressor model"""
        self.hoeffding_model = tree.HoeffdingTreeRegressor(
            grace_period=100,
            leaf_prediction='mean',
            model_selector_decay=0.6
        )
        return self

    def init_pa_model(self, C=1.0):
        """Initialize PARegressor model"""
        self.pa_model = linear_model.PARegressor(
            C=C,
            mode=2,
            eps=0.1
        )
        return self

    def learn_and_predict(self, X, y, model_type='bagging'):
        """
        Learn from the data and make predictions using the specified model
        
        Parameters:
        -----------
        X : dict
            Input features
        y : float
            Target value
        model_type : str
            Type of model to use ('bagging', 'hoeffding', or 'pa')
            
        Returns:
        --------
        float
            Prediction for the next value
        dict
            Updated metrics after learning
        """
        # Extract features
        features = self._extract_features(X)
        
        # Select and initialize model if needed
        if model_type == 'bagging':
            if self.bagging_model is None:
                self.init_bagging_model()
            model = self.bagging_model
        elif model_type == 'hoeffding':
            if self.hoeffding_model is None:
                self.init_hoeffding_model()
            model = self.hoeffding_model
        elif model_type == 'pa':
            if self.pa_model is None:
                self.init_pa_model()
            model = self.pa_model
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Make prediction
        prediction = model.predict_one(features)
        
        # Learn from the current data point
        model.learn_one(features, y)
        
        # Update metrics if we have a prediction
        if prediction is not None:
            self.mae.update(y, prediction)
            self.rmse.update(y, prediction)
            self.r2.update(y, prediction)
        
        # Return both prediction and current metrics
        return prediction, self.get_metrics()

    def get_metrics(self):
        """Return current metrics values"""
        return {
            'MAE': self.mae.get(),
            'RMSE': self.rmse.get(),
            'R2': self.r2.get()
        }

    def reset_metrics(self):
        """Reset all metrics"""
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()
