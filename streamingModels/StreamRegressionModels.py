from river import compose, linear_model, preprocessing, metrics, forest, neural_net as nn, optim, tree, ensemble
from datetime import datetime
import numpy as np


#----------------------------------------
# The base class for all regressors
#----------------------------------------

class BaseRegressor:
    def __init__(self):
        self.model = None
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()

    def _extract_features(self, X):
        open_price = float(X['open'])
        high = float(X['high'])
        low = float(X['low'])
        close = float(X['close'])
        volume = float(X['volume'])
        n_trades = float(X['n_trades'])

        # Calculate features
        high_low_diff = high - low
        close_open_diff = close - open_price
        high_low_ratio = high / low if low != 0 else 1.0
        close_open_ratio = close / open_price if open_price != 0 else 1.0
        volume_price_ratio = volume * close

        # Parse datetime
        dt = datetime.strptime(X['start_time'], '%d-%m-%Y %H:%M:%S')
        hour, minute, day_of_week = dt.hour, dt.minute, dt.weekday()
        features = {
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume,
                    'n_trades': n_trades,
                    'high_low_diff': high_low_diff,
                    'close_open_diff': close_open_diff,
                    'high_low_ratio': high_low_ratio,
                    'close_open_ratio': close_open_ratio,
                    'volume_price_ratio': volume_price_ratio,
                    'hour': hour,
                    'minute': minute,
                    'day_of_week': day_of_week,
                    }
        return features

    def learn_one(self, X, y):
        features = self._extract_features(X)
        y = float(y)

        self.model.learn_one(features, y)
        pred = self.model.predict_one(features)

        # Update metrics
        self._update_metrics(y, pred)

    def predict_one(self, X):
        features = self._extract_features(X)
        return self.model.predict_one(features)

    def get_metrics(self):
        return {
            'MAE': self.mae.get(),
            'RMSE': self.rmse.get(),
            'R2': self.r2.get(),
        }

    def _update_metrics(self, y, pred):
        self.mae.update(y, pred)
        self.rmse.update(y, pred)
        self.r2.update(y, pred)

#-----------------------------------------------------------

class PARegressor(BaseRegressor):
    def __init__(self):
        super().__init__()
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('lin_reg', linear_model.PARegressor(C=1.0, eps=0.1))
        )


class ARFRegressor(BaseRegressor):
    def __init__(self):
        super().__init__()
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('forest', forest.ARFRegressor(seed=42))
        )


class NNRegressor(BaseRegressor):
    def __init__(self):
        super().__init__()
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('nn', nn.MLPRegressor(
                hidden_dims=(5,),
                activations=(nn.activations.ReLU, nn.activations.ReLU, nn.activations.Identity),
                optimizer=optim.SGD(1e-6),
                seed=42
            ))
        )

class HoeffdingTreeRegressor(BaseRegressor):
    def __init__(self):
        super().__init__()
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('hoeffding', tree.HoeffdingTreeRegressor(
                grace_period=100,
                leaf_prediction='mean',
                model_selector_decay=0.6
            ))
        )

class BaggingRegressor(BaseRegressor):
    def __init__(self, n_models=10):
        super().__init__()
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('bagging', ensemble.BaggingRegressor(
                model=linear_model.LinearRegression(),
                n_models=n_models,
                seed=42
            ))
        )
#----------------------------------------------------
# SNARIMAX model for time series forecasting
#----------------------------------------------------

class SNARIMAXTester:
    def __init__(self, p=1, d=0, q=0, m=12, sp=0, sd=0, sq=0):
        """
        Initialize the SNARIMAX model.

        Parameters:
        -----------
        p : int
            Order of the autoregressive part.
        d : int
            Differencing order.
        q : int
            Order of the moving average part.
        m : int
            Season length.
        sp : int
            Seasonal order of the autoregressive part.
        sd : int
            Seasonal differencing order.
        sq : int
            Seasonal order of the moving average part.
        """
        self.model = time_series.SNARIMAX(
            p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq,
            regressor=preprocessing.StandardScaler() | linear_model.LinearRegression()
        )
        self.metrics = {
            'MAE': metrics.MAE(),
            'RMSE': metrics.RMSE(),
            'R2': metrics.R2()
        }

    def learn_and_predict(self, X, y):
        """
        Learn from the data and make predictions.

        Parameters:
        -----------
        X : dict
            Input features
        y : float
            Target value

        Returns:
        --------
        float
            Prediction for the next value
        dict
            Updated metrics after learning
        """
        self.model.learn_one(y)  # SNARIMAX directly learns on the target value
        forecast = self.model.forecast(horizon=1)
        prediction = forecast[0] if forecast else None

        # Update metrics if we have a prediction
        if prediction is not None:
            for metric in self.metrics.values():
                metric.update(y, prediction)

        return prediction, self.get_metrics()

    def get_metrics(self):
        """Return current metrics values."""
        return {name: metric.get() for name, metric in self.metrics.items()}

    def reset_metrics(self):
        """Reset all metrics."""
        for metric in self.metrics.values():
            metric.reset()