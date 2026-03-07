"""
高级预测服务 - 基于 GitHub 优秀项目
参考: Stock-Prediction-Models, freqtrade, jesse 等
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# 尝试导入高级模型库
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

try:
    from sklearn.ensemble import (
        RandomForestRegressor,
        GradientBoostingRegressor,
        AdaBoostRegressor,
        StackingRegressor
    )
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class AdvancedPredictionService:
    """高级预测服务 - 包含多种机器学习模型"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.prediction_history = defaultdict(list)
        
        # 模型配置
        self.model_configs = {
            "xgboost": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42
            },
            "lightgbm": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42
            },
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "random_state": 42
            },
            "prophet": {
                "changepoint_prior_scale": 0.05,
                "seasonality_prior_scale": 10.0,
                "holidays_prior_scale": 10.0,
                "seasonality_mode": "additive"
            }
        }
    
    def create_advanced_features(
        self,
        df: pd.DataFrame,
        target_col: str = "close",
        lookback_periods: List[int] = None
    ) -> pd.DataFrame:
        """
        创建高级特征
        
        参考: Stock-Prediction-Models 的特征工程
        """
        if lookback_periods is None:
            lookback_periods = [1, 2, 3, 5, 10, 20, 50]
        
        df = df.copy()
        
        # 确保有必要的列
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = df[target_col]
        
        # 1. 价格特征
        df["returns"] = df[target_col].pct_change()
        df["log_returns"] = np.log1p(df["returns"])
        
        # 2. 技术指标特征
        for period in lookback_periods:
            # 移动平均线
            df[f"ma_{period}"] = df[target_col].rolling(window=period).mean()
            df[f"ema_{period}"] = df[target_col].ewm(span=period, adjust=False).mean()
            
            # 收益率相关
            df[f"returns_std_{period}"] = df["returns"].rolling(window=period).std()
            df[f"volatility_{period}"] = df[f"returns_std_{period}"] * np.sqrt(365)
            
            # 最高价/最低价
            df[f"high_{period}"] = df["high"].rolling(window=period).max()
            df[f"low_{period}"] = df["low"].rolling(window=period).min()
            
            # 成交量特征
            df[f"volume_ma_{period}"] = df["volume"].rolling(window=period).mean()
            df[f"volume_ratio_{period}"] = df["volume"] / df[f"volume_ma_{period}"]
            
            # 价格位置
            df[f"price_position_{period}"] = (
                (df[target_col] - df[f"low_{period}"]) /
                (df[f"high_{period}"] - df[f"low_{period}"] + 1e-8)
            )
        
        # 3. 动量特征
        for period in [5, 10, 20]:
            # RSI 简化版
            delta = df["returns"]
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / (loss + 1e-8)
            df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
            
            # MACD 简化版
            if period >= 12:
                ema12 = df[target_col].ewm(span=12, adjust=False).mean()
                ema26 = df[target_col].ewm(span=26, adjust=False).mean()
                df["macd"] = ema12 - ema26
                df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
                df["macd_hist"] = df["macd"] - df["macd_signal"]
        
        # 4. 周期性特征
        if "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        elif df.index.dtype == "datetime64[ns]":
            df["datetime"] = df.index
        else:
            df["datetime"] = pd.date_range(
                start=datetime.now() - timedelta(days=len(df)),
                periods=len(df),
                freq="H"
            )
        
        df["hour"] = df["datetime"].dt.hour
        df["dayofweek"] = df["datetime"].dt.dayofweek
        df["dayofmonth"] = df["datetime"].dt.day
        df["month"] = df["datetime"].dt.month
        
        # 5. 滞后特征
        for i in range(1, 6):
            df[f"lag_{i}"] = df[target_col].shift(i)
            df[f"lag_return_{i}"] = df["returns"].shift(i)
        
        # 6. 目标变量（未来收益率）
        df["target_1h"] = df[target_col].shift(-1) / df[target_col] - 1
        df["target_4h"] = df[target_col].shift(-4) / df[target_col] - 1
        df["target_24h"] = df[target_col].shift(-24) / df[target_col] - 1
        
        # 移除 NaN
        df = df.dropna()
        
        return df
    
    def prepare_ml_data(
        self,
        df: pd.DataFrame,
        target_col: str = "target_1h",
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str]]:
        """
        准备机器学习数据
        """
        # 特征列
        feature_cols = [
            col for col in df.columns
            if col not in [
                "datetime", "timestamp", "target_1h", "target_4h", "target_24h",
                "open", "high", "low", "close", "volume"
            ] and not col.startswith("target_")
        ]
        
        # 移除剩余的非数值列
        feature_cols = [
            col for col in feature_cols
            if pd.api.types.is_numeric_dtype(df[col])
        ]
        
        # 分割数据（时间序列分割）
        split_idx = int(len(df) * (1 - test_size))
        
        X_train = df[feature_cols].iloc[:split_idx]
        X_test = df[feature_cols].iloc[split_idx:]
        y_train = df[target_col].iloc[:split_idx]
        y_test = df[target_col].iloc[split_idx:]
        
        return X_train, X_test, y_train, y_test, feature_cols
    
    def train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        训练 XGBoost 模型
        
        参考: freqtrade 的 XGBoost 策略
        """
        if not HAS_XGBOOST:
            return {
                "success": False,
                "message": "XGBoost 未安装，使用替代模型"
            }
        
        try:
            config = self.model_configs["xgboost"]
            model = xgb.XGBRegressor(**config)
            model.fit(X_train, y_train)
            
            # 保存模型
            model_key = f"{symbol}_xgboost"
            self.models[model_key] = model
            
            # 特征重要性
            self.feature_importance[model_key] = dict(
                zip(X_train.columns, model.feature_importances_)
            )
            
            return {
                "success": True,
                "model": model,
                "model_key": model_key
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"XGBoost 训练失败: {str(e)}"
            }
    
    def train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        训练 LightGBM 模型
        
        参考: jesse 的 LightGBM 集成
        """
        if not HAS_LIGHTGBM:
            return {
                "success": False,
                "message": "LightGBM 未安装，使用替代模型"
            }
        
        try:
            config = self.model_configs["lightgbm"]
            model = lgb.LGBMRegressor(**config, verbose=-1)
            model.fit(X_train, y_train)
            
            # 保存模型
            model_key = f"{symbol}_lightgbm"
            self.models[model_key] = model
            
            # 特征重要性
            self.feature_importance[model_key] = dict(
                zip(X_train.columns, model.feature_importances_)
            )
            
            return {
                "success": True,
                "model": model,
                "model_key": model_key
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"LightGBM 训练失败: {str(e)}"
            }
    
    def train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        训练随机森林模型
        """
        if not HAS_SKLEARN:
            return {
                "success": False,
                "message": "Scikit-learn 未安装"
            }
        
        try:
            config = self.model_configs["random_forest"]
            model = RandomForestRegressor(**config)
            model.fit(X_train, y_train)
            
            # 保存模型
            model_key = f"{symbol}_random_forest"
            self.models[model_key] = model
            
            # 特征重要性
            self.feature_importance[model_key] = dict(
                zip(X_train.columns, model.feature_importances_)
            )
            
            return {
                "success": True,
                "model": model,
                "model_key": model_key
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"随机森林训练失败: {str(e)}"
            }
    
    def train_prophet(
        self,
        df: pd.DataFrame,
        target_col: str = "close",
        symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        训练 Prophet 模型
        
        参考: Facebook Prophet 时间序列预测
        """
        if not HAS_PROPHET:
            return {
                "success": False,
                "message": "Prophet 未安装"
            }
        
        try:
            # 准备 Prophet 数据
            prophet_df = df.copy()
            
            if "datetime" in prophet_df.columns:
                prophet_df = prophet_df.rename(columns={"datetime": "ds"})
            elif prophet_df.index.dtype == "datetime64[ns]":
                prophet_df["ds"] = prophet_df.index
            else:
                prophet_df["ds"] = pd.date_range(
                    start=datetime.now() - timedelta(days=len(prophet_df)),
                    periods=len(prophet_df),
                    freq="H"
                )
            
            prophet_df["y"] = prophet_df[target_col]
            
            # 训练模型
            config = self.model_configs["prophet"]
            model = Prophet(**config)
            model.fit(prophet_df[["ds", "y"]])
            
            # 保存模型
            model_key = f"{symbol}_prophet"
            self.models[model_key] = model
            
            return {
                "success": True,
                "model": model,
                "model_key": model_key
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Prophet 训练失败: {str(e)}"
            }
    
    def predict_with_model(
        self,
        model_key: str,
        X: pd.DataFrame
    ) -> Optional[np.ndarray]:
        """使用训练好的模型进行预测"""
        if model_key not in self.models:
            return None
        
        model = self.models[model_key]
        
        try:
            return model.predict(X)
        except Exception as e:
            print(f"预测失败: {str(e)}")
            return None
    
    def evaluate_model(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """评估模型性能"""
        if not HAS_SKLEARN:
            return {
                "mse": float(np.mean((y_true - y_pred) ** 2)),
                "mae": float(np.mean(np.abs(y_true - y_pred)))
            }
        
        return {
            "mse": float(mean_squared_error(y_true, y_pred)),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "r2": float(r2_score(y_true, y_pred)),
            "directional_accuracy": float(
                np.mean((np.sign(y_true) == np.sign(y_pred)).astype(int))
            )
        }
    
    def get_ensemble_prediction(
        self,
        symbol: str,
        X: pd.DataFrame,
        df_with_dates: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        获取所有可用模型的集成预测
        
        参考: Deep Learning for Stock Prediction 的集成方法
        """
        predictions = {}
        model_keys = [key for key in self.models.keys() if key.startswith(symbol)]
        
        for model_key in model_keys:
            if "prophet" in model_key and df_with_dates is not None:
                # Prophet 特殊处理
                model = self.models[model_key]
                future = model.make_future_dataframe(periods=24, freq="H")
                forecast = model.predict(future)
                pred = forecast["yhat"].iloc[-1]
                predictions[model_key] = float(pred)
            else:
                # 其他模型
                pred = self.predict_with_model(model_key, X.iloc[-1:])
                if pred is not None:
                    predictions[model_key] = float(pred[0])
        
        if not predictions:
            return {
                "success": False,
                "message": "没有可用的预测模型"
            }
        
        # 简单平均集成
        mean_pred = np.mean(list(predictions.values()))
        
        # 方向判断
        direction = "up" if mean_pred > 0 else "down"
        confidence = min(abs(mean_pred) * 10, 1.0)  # 归一化到 0-1
        
        return {
            "success": True,
            "symbol": symbol,
            "direction": direction,
            "confidence": float(confidence),
            "predicted_return": float(mean_pred),
            "individual_predictions": predictions,
            "model_count": len(predictions)
        }
    
    def get_top_features(
        self,
        model_key: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """获取重要特征"""
        if model_key not in self.feature_importance:
            return []
        
        importance = self.feature_importance[model_key]
        sorted_features = sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {"feature": feat, "importance": float(imp)}
            for feat, imp in sorted_features
        ]


# 全局实例
_advanced_prediction_service = None


def get_advanced_prediction_service() -> AdvancedPredictionService:
    """获取高级预测服务单例"""
    global _advanced_prediction_service
    if _advanced_prediction_service is None:
        _advanced_prediction_service = AdvancedPredictionService()
    return _advanced_prediction_service

