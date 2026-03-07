from fastapi import APIRouter, HTTPException, Query
from app.services.prediction_backtest_service import get_prediction_backtest_service
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

# 服务实例
backtest_service = get_prediction_backtest_service()


class PredictionRecord(BaseModel):
    symbol: str
    prediction: dict
    actual_price: Optional[float] = None


class PredictionVerification(BaseModel):
    prediction_id: int
    actual_price: float
    actual_direction: Optional[str] = None


@router.post("/record")
async def record_prediction(record: PredictionRecord):
    """记录一个新的预测"""
    try:
        result = backtest_service.record_prediction(
            record.symbol,
            record.prediction,
            record.actual_price
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_prediction(verification: PredictionVerification):
    """验证一个预测"""
    try:
        result = backtest_service.verify_prediction(
            verification.prediction_id,
            verification.actual_price,
            verification.actual_direction
        )
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_predictions(
    symbol: Optional[str] = None,
    verified: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """获取预测历史"""
    try:
        predictions = backtest_service.get_predictions(symbol, verified, limit)
        return {
            "success": True,
            "data": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{symbol}")
async def get_backtest_report(symbol: Optional[str] = None):
    """获取回测报告"""
    try:
        report = backtest_service.get_backtest_report(symbol)
        return {
            "success": True,
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mock/{symbol}")
async def run_mock_backtest(
    symbol: str,
    num_predictions: int = Query(50, ge=10, le=200)
):
    """运行模拟回测（用于测试）"""
    try:
        result = backtest_service.run_mock_backtest(symbol, num_predictions)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "prediction_backtest",
        "timestamp": int(datetime.now().timestamp() * 1000)
    }
