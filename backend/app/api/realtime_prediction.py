from fastapi import APIRouter, HTTPException, Query
from app.services.realtime_prediction_service import get_realtime_prediction_service
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# 服务实例
realtime_service = get_realtime_prediction_service()


class PredictionUpdate(BaseModel):
    symbol: str
    prediction: dict
    source: Optional[str] = "manual"


@router.post("/update")
async def update_prediction(update: PredictionUpdate):
    """更新预测"""
    try:
        result = realtime_service.update_prediction(
            update.symbol,
            update.prediction,
            update.source
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest/{symbol}")
async def get_latest_prediction(symbol: str):
    """获取最新预测"""
    try:
        prediction = realtime_service.get_latest_prediction(symbol)
        if prediction is None:
            return {
                "success": True,
                "data": None,
                "message": "暂无该交易对的预测数据"
            }
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}")
async def get_prediction_history(
    symbol: str,
    limit: int = Query(50, ge=1, le=200)
):
    """获取预测历史"""
    try:
        history = realtime_service.get_prediction_history(symbol, limit)
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_latest_predictions():
    """获取所有最新预测"""
    try:
        predictions = realtime_service.get_all_latest_predictions()
        return {
            "success": True,
            "data": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/changes/{symbol}")
async def get_prediction_changes(
    symbol: str,
    lookback: int = Query(10, ge=2, le=50)
):
    """获取预测变化分析"""
    try:
        changes = realtime_service.get_prediction_changes(symbol, lookback)
        return {
            "success": True,
            "data": changes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary(symbol: Optional[str] = None):
    """获取实时预测摘要"""
    try:
        summary = realtime_service.get_summary(symbol)
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "realtime_prediction",
        "timestamp": int(datetime.now().timestamp() * 1000)
    }
