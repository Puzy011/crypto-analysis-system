"""
高级预测 API
"""

from datetime import datetime
from typing import Dict
import traceback

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import numpy as np
import pandas as pd

from app.services.advanced_prediction_service import (
    get_advanced_prediction_service
)
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/advanced-prediction", tags=["高级预测"])
binance_service = BinanceService()

TRADE_PROFILES: Dict[str, Dict[str, object]] = {
    "realtime": {"label": "实时短线", "interval": "15m", "train_limit": 1200, "predict_limit": 480},
    "intraday": {"label": "日内波段", "interval": "1h", "train_limit": 600, "predict_limit": 260},
    "longterm": {"label": "中长线", "interval": "4h", "train_limit": 720, "predict_limit": 320},
}
HORIZON_HOURS = {"1h": 1, "4h": 4, "24h": 24}


def _resolve_trade_profile(trade_type: str) -> Dict[str, object]:
    key = (trade_type or "intraday").lower()
    if key not in TRADE_PROFILES:
        key = "intraday"
    return {"trade_type": key, **TRADE_PROFILES[key]}


def _interval_hours(interval: str) -> float:
    if interval.endswith("m"):
        return max(1, int(interval[:-1])) / 60.0
    if interval.endswith("h"):
        return float(max(1, int(interval[:-1])))
    if interval.endswith("d"):
        return float(max(1, int(interval[:-1])) * 24)
    return 1.0


def _target_steps_for_interval(interval: str) -> Dict[str, int]:
    bar_hours = _interval_hours(interval)
    result: Dict[str, int] = {}
    for horizon, total_hours in HORIZON_HOURS.items():
        result[horizon] = max(1, int(np.ceil(total_hours / bar_hours)))
    return result


class PredictionRequest(BaseModel):
    symbol: str = "BTCUSDT"
    target_horizon: str = "1h"  # 1h, 4h, 24h
    trade_type: str = "intraday"  # realtime, intraday, longterm
    use_xgboost: bool = True
    use_lightgbm: bool = True
    use_random_forest: bool = True
    use_prophet: bool = True


@router.get("/trade-modes")
async def get_prediction_trade_modes():
    """获取高级预测支持的交易模式"""
    modes = []
    for mode in ["realtime", "intraday", "longterm"]:
        profile = _resolve_trade_profile(mode)
        modes.append(
            {
                "trade_type": profile["trade_type"],
                "label": profile["label"],
                "interval": profile["interval"],
                "train_limit": profile["train_limit"],
                "predict_limit": profile["predict_limit"],
            }
        )
    return {"modes": modes, "default": "intraday"}


@router.post("/train")
async def train_advanced_models(
    request: PredictionRequest
):
    """
    训练高级预测模型
    """
    try:
        pred_service = get_advanced_prediction_service()
        profile = _resolve_trade_profile(request.trade_type)
        target_steps = _target_steps_for_interval(str(profile["interval"]))
        target_horizon = request.target_horizon if request.target_horizon in HORIZON_HOURS else "1h"
        target_col = f"target_{target_horizon}"
        model_scope = f"{request.symbol}__{profile['trade_type']}"

        klines = await binance_service.get_klines(
            symbol=request.symbol,
            interval=str(profile["interval"]),
            limit=int(profile["train_limit"])
        )

        df = pd.DataFrame(klines)
        df["timestamp"] = df["timestamp"]
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]

        df_features = pred_service.create_advanced_features(
            df,
            target_steps=target_steps
        )

        X_train, X_test, y_train, y_test, feature_cols = pred_service.prepare_ml_data(
            df_features,
            target_col=target_col
        )

        results = {
            "symbol": request.symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "interval": profile["interval"],
            "target_horizon": target_horizon,
            "target_bars": target_steps[target_horizon],
            "model_scope": model_scope,
            "models_trained": [],
            "feature_count": len(feature_cols),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "timestamp": datetime.now().isoformat()
        }

        if request.use_xgboost:
            xgb_result = pred_service.train_xgboost(X_train, y_train, model_scope)
            if xgb_result["success"]:
                y_pred = pred_service.predict_with_model(
                    f"{model_scope}_xgboost",
                    X_test
                )
                if y_pred is not None:
                    metrics = pred_service.evaluate_model(y_test, y_pred)
                    pred_service.update_model_metrics(f"{model_scope}_xgboost", metrics)
                    results["models_trained"].append({
                        "model": "xgboost",
                        "status": "success",
                        "metrics": metrics
                    })

        if request.use_lightgbm:
            lgb_result = pred_service.train_lightgbm(X_train, y_train, model_scope)
            if lgb_result["success"]:
                y_pred = pred_service.predict_with_model(
                    f"{model_scope}_lightgbm",
                    X_test
                )
                if y_pred is not None:
                    metrics = pred_service.evaluate_model(y_test, y_pred)
                    pred_service.update_model_metrics(f"{model_scope}_lightgbm", metrics)
                    results["models_trained"].append({
                        "model": "lightgbm",
                        "status": "success",
                        "metrics": metrics
                    })

        if request.use_random_forest:
            rf_result = pred_service.train_random_forest(X_train, y_train, model_scope)
            if rf_result["success"]:
                y_pred = pred_service.predict_with_model(
                    f"{model_scope}_random_forest",
                    X_test
                )
                if y_pred is not None:
                    metrics = pred_service.evaluate_model(y_test, y_pred)
                    pred_service.update_model_metrics(f"{model_scope}_random_forest", metrics)
                    results["models_trained"].append({
                        "model": "random_forest",
                        "status": "success",
                        "metrics": metrics
                    })

        if request.use_prophet:
            prophet_result = pred_service.train_prophet(df, "close", model_scope)
            if prophet_result["success"]:
                results["models_trained"].append({
                    "model": "prophet",
                    "status": "success"
                })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{symbol}")
async def get_advanced_prediction(
    symbol: str = "BTCUSDT",
    target_horizon: str = Query("1h", description="预测时间跨度: 1h, 4h, 24h"),
    trade_type: str = Query("intraday", description="交易模式: realtime, intraday, longterm"),
):
    """
    获取高级预测结果
    """
    try:
        pred_service = get_advanced_prediction_service()
        profile = _resolve_trade_profile(trade_type)
        target_steps = _target_steps_for_interval(str(profile["interval"]))
        horizon = target_horizon if target_horizon in HORIZON_HOURS else "1h"
        model_scope = f"{symbol}__{profile['trade_type']}"

        klines = await binance_service.get_klines(
            symbol=symbol,
            interval=str(profile["interval"]),
            limit=int(profile["predict_limit"])
        )

        df = pd.DataFrame(klines)
        df["timestamp"] = df["timestamp"]
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]

        df_features = pred_service.create_advanced_features(
            df,
            target_steps=target_steps
        )

        feature_cols = [
            col for col in df_features.columns
            if col not in ["datetime", "timestamp"]
            and not col.startswith("target_")
            and pd.api.types.is_numeric_dtype(df_features[col])
        ]

        X = df_features[feature_cols]

        prediction = pred_service.get_ensemble_prediction(
            symbol=model_scope,
            X=X,
            df_with_dates=df,
            trade_type=profile["trade_type"],
        )

        if not prediction["success"]:
            current_price = df["close"].iloc[-1]
            ma20 = df["close"].rolling(20).mean().iloc[-1]
            if current_price > ma20:
                direction = "up"
                confidence = 0.6
            else:
                direction = "down"
                confidence = 0.6

            prediction = {
                "success": True,
                "symbol": symbol,
                "trade_type": profile["trade_type"],
                "direction": direction,
                "confidence": confidence,
                "predicted_return": 0.01 if direction == "up" else -0.01,
                "individual_predictions": {},
                "model_weights": {},
                "agreement_score": 0.5,
                "prediction_interval": {
                    "lower_return": -0.02,
                    "upper_return": 0.02,
                    "lower_price": float(current_price * 0.98),
                    "upper_price": float(current_price * 1.02),
                },
                "market_regime": {
                    "trend_regime": "sideways",
                    "volatility_regime": "normal_volatility",
                },
                "prediction_history": [],
                "model_count": 0,
                "note": "使用基础预测，建议先训练模型"
            }
        else:
            prediction["symbol"] = symbol

        top_features = {}
        for model_type in ["xgboost", "lightgbm", "random_forest"]:
            model_key = f"{model_scope}_{model_type}"
            features = pred_service.get_top_features(model_key, top_n=5)
            if features:
                top_features[model_type] = features

        return {
            **prediction,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "interval": profile["interval"],
            "target_horizon": horizon,
            "target_bars": target_steps[horizon],
            "model_scope": model_scope,
            "top_features": top_features,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@router.get("/features/{symbol}")
async def get_feature_importance(
    symbol: str = "BTCUSDT",
    trade_type: str = Query("intraday", description="交易模式: realtime, intraday, longterm"),
):
    """
    获取特征重要性
    """
    try:
        pred_service = get_advanced_prediction_service()
        profile = _resolve_trade_profile(trade_type)
        model_scope = f"{symbol}__{profile['trade_type']}"

        feature_importance = {}
        for model_type in ["xgboost", "lightgbm", "random_forest"]:
            model_key = f"{model_scope}_{model_type}"
            features = pred_service.get_top_features(model_key, top_n=10)
            if features:
                feature_importance[model_type] = features

        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "interval": profile["interval"],
            "feature_importance": feature_importance,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
