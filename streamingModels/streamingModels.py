from river import compose
from river import linear_model
from river import preprocessing
from river import metrics
from datetime import datetime
import numpy as np

class PARegressor:  # Passive-Aggressive Regressor
    def __init__(self):
        # Create a preprocessing pipeline with feature scaling and model
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('lin_reg', linear_model.PARegressor(
                C=1.0,  # Regularization parameter
                eps=0.1  # Epsilon in the epsilon-insensitive loss function
            ))
        )
        
        # Initialize metrics for tracking performance
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()
        
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

    def learn_one(self, X, y):
        """Update the model with a single instance."""
        features = self._extract_features(X)
        y = float(y)
        
        # Update the model
        self.model.learn_one(features, y)
        
        # Update metrics
        self.mae.update(y, self.model.predict_one(features))
        self.rmse.update(y, self.model.predict_one(features))
        self.r2.update(y, self.model.predict_one(features))
        
        return self

    def predict_one(self, X):
        """Make a prediction for a single instance."""
        features = self._extract_features(X)
        return self.model.predict_one(features)
    
    def get_metrics(self):
        """Return current performance metrics."""
        return {
            'MAE': self.mae.get(),
            'RMSE': self.rmse.get(),
            'R2': self.r2.get()
        }
