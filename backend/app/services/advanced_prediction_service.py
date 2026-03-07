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
        self.model_metrics = {}
        
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
        lookback_periods: List[int] = None,
        target_steps: Optional[Dict[str, int]] = None,
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

        # 4. 市场微观结构与波动特征
        df["hl_range"] = (df["high"] - df["low"]) / (df[target_col] + 1e-8)
        df["oc_change"] = (df["close"] - df["open"]) / (df["open"] + 1e-8)
        df["vwap"] = (df["close"] * df["volume"]).cumsum() / (df["volume"].cumsum() + 1e-8)
        df["vwap_distance"] = (df[target_col] - df["vwap"]) / (df["vwap"] + 1e-8)

        true_range = pd.concat(
            [
                (df["high"] - df["low"]).abs(),
                (df["high"] - df["close"].shift(1)).abs(),
                (df["low"] - df["close"].shift(1)).abs(),
            ],
            axis=1
        ).max(axis=1)
        df["atr_14"] = true_range.rolling(window=14).mean()
        df["atr_pct"] = df["atr_14"] / (df[target_col] + 1e-8)

        bb_mid = df[target_col].rolling(window=20).mean()
        bb_std = df[target_col].rolling(window=20).std()
        df["bb_upper"] = bb_mid + 2 * bb_std
        df["bb_lower"] = bb_mid - 2 * bb_std
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (bb_mid + 1e-8)
        df["bb_position"] = (df[target_col] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-8)

        obv_step = np.where(df[target_col].diff() >= 0, df["volume"], -df["volume"])
        df["obv"] = pd.Series(obv_step, index=df.index).cumsum()
        df["obv_trend_10"] = df["obv"] - df["obv"].shift(10)

        vol_mean = df["volume"].rolling(window=20).mean()
        vol_std = df["volume"].rolling(window=20).std()
        df["volume_zscore"] = (df["volume"] - vol_mean) / (vol_std + 1e-8)
        df["return_zscore"] = (df["returns"] - df["returns"].rolling(20).mean()) / (
            df["returns"].rolling(20).std() + 1e-8
        )

        # 5. 趋势斜率特征
        for period in [10, 20, 50]:
            roll_mean = df[target_col].rolling(window=period).mean()
            df[f"slope_{period}"] = (roll_mean - roll_mean.shift(period // 2)) / (roll_mean.shift(period // 2) + 1e-8)

        # 6. 周期性特征
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
        
        # 7. 滞后特征
        for i in range(1, 6):
            df[f"lag_{i}"] = df[target_col].shift(i)
            df[f"lag_return_{i}"] = df["returns"].shift(i)
        
        # 8. 目标变量（未来收益率）
        default_target_steps = {"1h": 1, "4h": 4, "24h": 24}
        step_config = target_steps or default_target_steps
        for label, step in step_config.items():
            safe_step = max(1, int(step))
            df[f"target_{label}"] = df[target_col].shift(-safe_step) / df[target_col] - 1
        
        # 清理异常值后移除 NaN
        df = df.replace([np.inf, -np.inf], np.nan)
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
        y_true_arr = np.array(y_true, dtype=float)
        y_pred_arr = np.array(y_pred, dtype=float)

        if not HAS_SKLEARN:
            return {
                "mse": float(np.mean((y_true_arr - y_pred_arr) ** 2)),
                "mae": float(np.mean(np.abs(y_true_arr - y_pred_arr))),
                "directional_accuracy": float(
                    np.mean((np.sign(y_true_arr) == np.sign(y_pred_arr)).astype(int))
                ),
            }
        
        return {
            "mse": float(mean_squared_error(y_true_arr, y_pred_arr)),
            "mae": float(mean_absolute_error(y_true_arr, y_pred_arr)),
            "rmse": float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))),
            "r2": float(r2_score(y_true_arr, y_pred_arr)),
            "directional_accuracy": float(
                np.mean((np.sign(y_true_arr) == np.sign(y_pred_arr)).astype(int))
            )
        }

    def update_model_metrics(self, model_key: str, metrics: Dict[str, float]):
        """记录模型评估指标，用于后续加权集成"""
        if not metrics:
            return
        self.model_metrics[model_key] = metrics
    
    def get_ensemble_prediction(
        self,
        symbol: str,
        X: pd.DataFrame,
        df_with_dates: pd.DataFrame = None,
        trade_type: str = "intraday",
    ) -> Dict[str, Any]:
        """
        获取所有可用模型的集成预测
        
        参考: Deep Learning for Stock Prediction 的集成方法
        """
        predictions: Dict[str, float] = {}
        model_weights: Dict[str, float] = {}
        model_keys = [key for key in self.models.keys() if key.startswith(symbol)]
        current_price = float(df_with_dates["close"].iloc[-1]) if df_with_dates is not None else None
        
        for model_key in model_keys:
            if "prophet" in model_key and df_with_dates is not None:
                # Prophet 特殊处理
                model = self.models[model_key]
                future = model.make_future_dataframe(periods=1, freq="H")
                forecast = model.predict(future)
                pred_price = float(forecast["yhat"].iloc[-1])
                if current_price and current_price > 0:
                    pred_return = pred_price / current_price - 1
                else:
                    pred_return = 0.0
                predictions[model_key] = float(pred_return)
            else:
                # 其他模型
                pred = self.predict_with_model(model_key, X.iloc[-1:])
                if pred is not None:
                    predictions[model_key] = float(pred[0])

            if model_key in predictions:
                model_weights[model_key] = self._get_model_weight(model_key)
        
        if not predictions:
            return {
                "success": False,
                "message": "没有可用的预测模型"
            }
        
        # 按历史表现加权集成
        total_weight = sum(model_weights.values()) or 1.0
        normalized_weights = {
            k: v / total_weight
            for k, v in model_weights.items()
        }
        mean_pred = float(sum(predictions[k] * normalized_weights[k] for k in predictions))
        
        preds = list(predictions.values())
        pred_std = float(np.std(preds)) if len(preds) > 1 else 0.0
        signs = [np.sign(p) for p in preds if abs(p) > 1e-8]
        agreement_score = float(max(0.0, np.mean([1.0 if s == np.sign(mean_pred) else 0.0 for s in signs]))) if signs else 0.5

        # 方向判断
        if abs(mean_pred) < 0.001:
            direction = "sideways"
        elif mean_pred > 0:
            direction = "up"
        else:
            direction = "down"

        avg_acc = np.mean(
            [
                self.model_metrics.get(k, {}).get("directional_accuracy", 0.5)
                for k in predictions
            ]
        ) if predictions else 0.5
        strength = min(abs(mean_pred) * 20, 1.0)
        confidence = float(max(0.2, min(0.98, 0.35 * strength + 0.4 * agreement_score + 0.25 * avg_acc)))

        # 预测区间
        z_map = {
            "realtime": 1.28,  # 约 80%
            "intraday": 1.65,  # 约 90%
            "longterm": 1.96,  # 约 95%
        }
        z = z_map.get(trade_type, 1.65)
        pred_interval = {
            "lower_return": float(mean_pred - z * pred_std),
            "upper_return": float(mean_pred + z * pred_std),
        }
        if current_price is not None:
            pred_interval["lower_price"] = float(current_price * (1 + pred_interval["lower_return"]))
            pred_interval["upper_price"] = float(current_price * (1 + pred_interval["upper_return"]))

        regime = self._detect_market_regime(X)

        self.prediction_history[symbol].append(
            {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "symbol": symbol,
                "final_direction": direction,
                "final_label": "看涨" if direction == "up" else ("看跌" if direction == "down" else "震荡"),
                "final_confidence": confidence,
                "predicted_return": mean_pred,
                "agreement_score": agreement_score,
            }
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "trade_type": trade_type,
            "direction": direction,
            "confidence": confidence,
            "predicted_return": mean_pred,
            "individual_predictions": predictions,
            "model_weights": normalized_weights,
            "prediction_interval": pred_interval,
            "agreement_score": agreement_score,
            "market_regime": regime,
            "model_count": len(predictions),
            "prediction_history": list(self.prediction_history[symbol])[-20:],
        }

    def _get_model_weight(self, model_key: str) -> float:
        """
        根据历史评估指标生成模型权重。
        """
        metrics = self.model_metrics.get(model_key, {})
        directional_acc = float(metrics.get("directional_accuracy", 0.5))
        rmse = float(metrics.get("rmse", 0.02))
        rmse_penalty = 1.0 / (1.0 + rmse * 100)
        return max(0.1, directional_acc * 0.7 + rmse_penalty * 0.3)

    def _detect_market_regime(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        识别市场状态（趋势/震荡 + 波动率）。
        """
        if X is None or X.empty:
            return {"trend_regime": "unknown", "volatility_regime": "unknown"}

        row = X.iloc[-1]
        slope_20 = float(row.get("slope_20", 0.0))
        vol_20 = float(row.get("volatility_20", 0.0))

        if slope_20 > 0.01:
            trend_regime = "uptrend"
        elif slope_20 < -0.01:
            trend_regime = "downtrend"
        else:
            trend_regime = "sideways"

        if vol_20 > 0.8:
            vol_regime = "high_volatility"
        elif vol_20 < 0.2:
            vol_regime = "low_volatility"
        else:
            vol_regime = "normal_volatility"

        return {
            "trend_regime": trend_regime,
            "volatility_regime": vol_regime,
            "slope_20": slope_20,
            "volatility_20": vol_20,
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

