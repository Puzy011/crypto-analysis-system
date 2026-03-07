"""
高级预测 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

from app.services.advanced_prediction_service import (
    get_advanced_prediction_service
)
from app.services.mock_binance_service import get_mock_binance_service


router = APIRouter(prefix="/api/advanced-prediction", tags=["高级预测"])


class PredictionRequest(BaseModel):
    symbol: str = "BTCUSDT"
    target_horizon: str = "1h"  # 1h, 4h, 24h
    use_xgboost: bool = True
    use_lightgbm: bool = True
    use_random_forest: bool = True
    use_prophet: bool = True


@router.post("/train")
async def train_advanced_models(
    request: PredictionRequest
):
    """
    训练高级预测模型
    """
    try:
        pred_service = get_advanced_prediction_service()
        mock_service = get_mock_binance_service()
        
        # 获取历史数据
        klines = mock_service.get_klines(
            symbol=request.symbol,
            interval="1h",
            limit=500
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        df["timestamp"] = df["timestamp"]
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]
        
        # 创建特征
        df_features = pred_service.create_advanced_features(df)
        
        # 准备数据
        target_col = f"target_{request.target_horizon}"
        X_train, X_test, y_train, y_test, feature_cols = pred_service.prepare_ml_data(
            df_features,
            target_col=target_col
        )
        
        results = {
            "symbol": request.symbol,
            "target_horizon": request.target_horizon,
            "models_trained": [],
            "feature_count": len(feature_cols),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "timestamp": datetime.now().isoformat()
        }
        
        # 训练各模型
        if request.use_xgboost:
            xgb_result = pred_service.train_xgboost(X_train, y_train, request.symbol)
            if xgb_result["success"]:
                # 评估
                y_pred = pred_service.predict_with_model(
                    f"{request.symbol}_xgboost",
                    X_test
                )
                if y_pred is not None:
                    metrics = pred_service.evaluate_model(y_test, y_pred)
                    results["models_trained"].append({
                        "model": "xgboost",
                        "status": "success",
                        "metrics": metrics
                    })
        
        if request.use_lightgbm:
            lgb_result = pred_service.train_lightgbm(X_train, y_train, request.symbol)
            if lgb_result["success"]:
                y_pred = pred_service.predict_with_model(
                    f"{request.symbol}_lightgbm",
                    X_test
                )
                if y_pred is not None:
                    metrics = pred_service.evaluate_model(y_test, y_pred)
                    results["models_trained"].append({
                        "model": "lightgbm",
                        "status": "success",
                        "metrics": metrics
                    })
        
        if request.use_random_forest:
            rf_result = pred_service.train_random_forest(X_train, y_train, request.symbol)
            if rf_result["success"]:
                y_pred = pred_service.predict_with_model(
                    f"{request.symbol}_random_forest",
                    X_test
                )
                if y_pred is not None:
                    metrics = pred_service.evaluate_model(y_test, y_pred)
                    results["models_trained"].append({
                        "model": "random_forest",
                        "status": "success",
                        "metrics": metrics
                    })
        
        if request.use_prophet:
            prophet_result = pred_service.train_prophet(df, "close", request.symbol)
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
    target_horizon: str = Query("1h", description="预测时间跨度: 1h, 4h, 24h")
):
    """
    获取高级预测结果
    """
    try:
        pred_service = get_advanced_prediction_service()
        mock_service = get_mock_binance_service()
        
        # 获取历史数据
        klines = mock_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=200
        )
        
        df = pd.DataFrame(klines)
        df["timestamp"] = df["timestamp"]
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]
        
        # 创建特征（不包含目标变量）
        df_features = pred_service.create_advanced_features(df)
        
        # 移除目标列用于预测
        feature_cols = [
            col for col in df_features.columns
            if col not in ["datetime", "timestamp", "target_1h", "target_4h", "target_24h"]
            and pd.api.types.is_numeric_dtype(df_features[col])
        ]
        
        X = df_features[feature_cols]
        
        # 获取集成预测
        prediction = pred_service.get_ensemble_prediction(
            symbol=symbol,
            X=X,
            df_with_dates=df
        )
        
        if not prediction["success"]:
            # 如果没有训练好的模型，返回基于技术分析的预测
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
                "direction": direction,
                "confidence": confidence,
                "predicted_return": 0.01 if direction == "up" else -0.01,
                "individual_predictions": {},
                "model_count": 0,
                "note": "使用基础预测，建议先训练模型"
            }
        
        # 获取特征重要性
        top_features = {}
        for model_type in ["xgboost", "lightgbm", "random_forest"]:
            model_key = f"{symbol}_{model_type}"
            features = pred_service.get_top_features(model_key, top_n=5)
            if features:
                top_features[model_type] = features
        
        return {
            **prediction,
            "top_features": top_features,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


@router.get("/features/{symbol}")
async def get_feature_importance(
    symbol: str = "BTCUSDT"
):
    """
    获取特征重要性
    """
    try:
        pred_service = get_advanced_prediction_service()
        
        feature_importance = {}
        for model_type in ["xgboost", "lightgbm", "random_forest"]:
            model_key = f"{symbol}_{model_type}"
            features = pred_service.get_top_features(model_key, top_n=10)
            if features:
                feature_importance[model_type] = features
        
        return {
            "symbol": symbol,
            "feature_importance": feature_importance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

