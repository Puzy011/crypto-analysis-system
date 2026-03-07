from fastapi import APIRouter, HTTPException
import pandas as pd
from app.services.binance_service import BinanceService
from app.services.prediction_service import PredictionService

router = APIRouter()
binance_service = BinanceService()
prediction_service = PredictionService()


@router.get("/trend/{symbol}")
async def get_trend_prediction(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 200
):
    """获取趋势预测"""
    try:
        # 获取 K线数据
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 进行预测
        prediction = prediction_service.predict_basic_trend(df)
        
        return {
            "success": True,
            "data": prediction,
            "symbol": symbol.upper(),
            "interval": interval
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/range/{symbol}")
async def get_price_range_prediction(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 200,
    horizon: int = 24
):
    """获取价格区间预测"""
    try:
        # 获取 K线数据
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 进行预测
        prediction = prediction_service.predict_price_range(df, horizon)
        
        return {
            "success": True,
            "data": prediction,
            "symbol": symbol.upper(),
            "interval": interval
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "prediction"
    }
