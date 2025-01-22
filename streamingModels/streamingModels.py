from river import compose, linear_model, preprocessing, metrics, forest, neural_net as nn, optim
from datetime import datetime

class BaseRegressor:
    def _extract_features(self, X):
        features = {
            'open': float(X['open']),
            'high': float(X['high']),
            'low': float(X['low']),
            'close': float(X['close']),
            'volume': float(X['volume']),
            'n_trades': float(X['n_trades']),
            'high_low_diff': float(X['high']) - float(X['low']),
            'close_open_diff': float(X['close']) - float(X['open']),
            'high_low_ratio': float(X['high']) / float(X['low']) if float(X['low']) != 0 else 1.0,
            'close_open_ratio': float(X['close']) / float(X['open']) if float(X['open']) != 0 else 1.0,
            'volume_price_ratio': float(X['volume']) * float(X['close']),
        }
        
        dt = datetime.strptime(X['start_time'], '%d-%m-%Y %H:%M:%S')
        features.update({
            'hour': dt.hour,
            'minute': dt.minute,
            'day_of_week': dt.weekday(),
        })
        
        return features

class PARegressor(BaseRegressor):
    def __init__(self):
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('lin_reg', linear_model.PARegressor(C=1.0, eps=0.1))
        )
        
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()
        
    def learn_one(self, X, y):
        features = self._extract_features(X)
        y = float(y)
        
        self.model.learn_one(features, y)
        
        pred = self.model.predict_one(features)
        self.mae.update(y, pred)
        self.rmse.update(y, pred)
        self.r2.update(y, pred)
        
        return self

    def predict_one(self, X):
        features = self._extract_features(X)
        return self.model.predict_one(features)
    
    def get_metrics(self):
        return {
            'MAE': self.mae.get(),
            'RMSE': self.rmse.get(),
            'R2': self.r2.get()
        }

class ARFRegressor(BaseRegressor):
    def __init__(self):
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('forest', forest.ARFRegressor(seed=42))
        )
        
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()
        
    def learn_one(self, X, y):
        features = self._extract_features(X)
        y = float(y)
        
        self.model.learn_one(features, y)
        
        pred = self.model.predict_one(features)
        self.mae.update(y, pred)
        self.rmse.update(y, pred)
        self.r2.update(y, pred)
        
        return self

    def predict_one(self, X):
        features = self._extract_features(X)
        return self.model.predict_one(features)
    
    def get_metrics(self):
        return {
            'MAE': self.mae.get(),
            'RMSE': self.rmse.get(),
            'R2': self.r2.get()
        }

class NNRegressor(BaseRegressor):
    def __init__(self):
        self.model = compose.Pipeline(
            ('scale', preprocessing.StandardScaler()),
            ('nn', nn.MLPRegressor(
                hidden_dims=(5,),
                activations=(nn.activations.ReLU, nn.activations.ReLU, nn.activations.Identity),
                optimizer=optim.SGD(1e-3),
                seed=42
            ))
        )
        
        self.mae = metrics.MAE()
        self.rmse = metrics.RMSE()
        self.r2 = metrics.R2()
        
    def learn_one(self, X, y):
        features = self._extract_features(X)
        y = float(y)
        
        self.model.learn_one(features, y)
        
        pred = self.model.predict_one(features)
        self.mae.update(y, pred)
        self.rmse.update(y, pred)
        self.r2.update(y, pred)
        
        return self

    def predict_one(self, X):
        features = self._extract_features(X)
        return self.model.predict_one(features)
    
    def get_metrics(self):
        return {
            'MAE': self.mae.get(),
            'RMSE': self.rmse.get(),
            'R2': self.r2.get()
        }