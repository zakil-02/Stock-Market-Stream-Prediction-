from river import compose, preprocessing, metrics, forest, tree, linear_model
from datetime import datetime
import numpy as np

class ModelTesterClassifier:
    def __init__(self):
        # Create a preprocessing pipeline with feature scaling
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler())
        )
        # Initialize metrics for classification
        self.accuracy = metrics.Accuracy()
        self.f1 = metrics.F1()
        self.precision = metrics.Precision()
        self.recall = metrics.Recall()
        
        # Initialize the models
        self.pa_model = None
        self.hoeffding_model = None
        self.forest_model = None

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

    def _compute_direction(self, current_price, previous_price):
        """Compute price direction (1 for up, 0 for down or no change)."""
        return 1 if current_price > previous_price else 0

    def init_pa_model(self, C=1.0, mode=2):
        """Initialize PAClassifier model"""
        self.pa_model = linear_model.PAClassifier(
            C=C,
            mode=mode
        )
        return self

    def init_hoeffding_model(self):
        """Initialize HoeffdingTreeClassifier model"""
        self.hoeffding_model = tree.HoeffdingTreeClassifier(
            grace_period=100,
            leaf_prediction='mc',
            nb_threshold=10
        )
        return self

    def init_forest_model(self, n_models=10):
        """Initialize AdaptiveRandomForest model"""
        self.forest_model = forest.ARFClassifier(
            n_models=n_models,
            seed=42
        )

            
        return self

    def learn_and_predict(self, X, previous_close, model_type='pa'):
        """
        Learn from the data and predict direction
        
        Parameters:
        -----------
        X : dict
            Input features
        previous_close : float
            Previous closing price for computing direction
        model_type : str
            Type of model to use ('pa', 'hoeffding', or 'forest')
            
        Returns:
        --------
        int
            Predicted direction (1 for up, 0 for down)
        dict
            Updated metrics after learning
        """
        # Extract features
        features = self._extract_features(X)
        
        # Compute actual direction
        current_close = float(X['close'])
        y = self._compute_direction(current_close, previous_close)
        
        # Select and initialize model if needed
        if model_type == 'pa':
            if self.pa_model is None:
                self.init_pa_model()
            model = self.pa_model
        elif model_type == 'hoeffding':
            if self.hoeffding_model is None:
                self.init_hoeffding_model()
            model = self.hoeffding_model
        elif model_type == 'forest':
            if self.forest_model is None:
                self.init_forest_model()
            model = self.forest_model
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Make prediction
        prediction = model.predict_one(features)
        
        # Learn from the current data point
        model.learn_one(features, y)
        
        # Update metrics
        if prediction is not None:
            self.accuracy.update(y, prediction)
            self.f1.update(y, prediction)
            self.precision.update(y, prediction)
            self.recall.update(y, prediction)
        
        # Return both prediction and current metrics
        return prediction, self.get_metrics()

    def get_metrics(self):
        """Return current metrics values"""
        return {
            'Accuracy': self.accuracy.get(),
            'F1': self.f1.get(),
            'Precision': self.precision.get(),
            'Recall': self.recall.get()
        }

    def reset_metrics(self):
        """Reset all metrics"""
        self.accuracy = metrics.Accuracy()
        self.f1 = metrics.F1()
        self.precision = metrics.Precision()
        self.recall = metrics.Recall()