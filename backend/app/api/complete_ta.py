"""
完整技术指标 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import pandas as pd
from datetime import datetime

from app.services.complete_ta_service import get_complete_ta_service
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/complete-ta", tags=["完整技术指标"])
binance_service = BinanceService()


@router.get("/indicators/{symbol}")
async def get_complete_indicators(
    symbol: str = "BTCUSDT",
    interval: str = Query("1h", description="K线间隔"),
    limit: int = Query(200, ge=50, le=1000, description="K线数量")
):
    """
    获取完整技术指标
    """
    try:
        ta_service = get_complete_ta_service()
        
        # 获取 K线数据
        klines = await binance_service.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        df = pd.DataFrame(klines)
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["close"] = df["close"]
        df["volume"] = df["volume"]
        
        # 计算所有指标
        df_with_indicators = ta_service.calculate_all_indicators(df)
        
        # 获取最新指标
        latest = ta_service.get_latest_indicators(df)
        
        # 转换为字典列表
        indicators_list = df_with_indicators.fillna(0).to_dict('records')
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data_count": len(indicators_list),
            "latest_indicators": latest,
            "all_indicators": indicators_list[-50:],  # 返回最近50条
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest/{symbol}")
async def get_latest_indicators(
    symbol: str = "BTCUSDT"
):
    """
    获取最新技术指标（快速接口）
    """
    try:
        ta_service = get_complete_ta_service()
        
        klines = await binance_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=200
        )
        
        df = pd.DataFrame(klines)
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["close"] = df["close"]
        df["volume"] = df["volume"]
        
        latest = ta_service.get_latest_indicators(df)
        
        return {
            "symbol": symbol,
            **latest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sma/{symbol}")
async def get_sma(
    symbol: str = "BTCUSDT",
    period: int = Query(20, ge=2, le=200, description="周期")
):
    """获取 SMA"""
    try:
        ta_service = get_complete_ta_service()
        klines = await binance_service.get_klines(symbol=symbol, limit=200)
        df = pd.DataFrame(klines)
        
        sma = ta_service.sma(df["close"], period)
        
        return {
            "symbol": symbol,
            "period": period,
            "sma": sma.fillna(0).tolist()[-50:],
            "latest": float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ema/{symbol}")
async def get_ema(
    symbol: str = "BTCUSDT",
    period: int = Query(20, ge=2, le=200, description="周期")
):
    """获取 EMA"""
    try:
        ta_service = get_complete_ta_service()
        klines = await binance_service.get_klines(symbol=symbol, limit=200)
        df = pd.DataFrame(klines)
        
        ema = ta_service.ema(df["close"], period)
        
        return {
            "symbol": symbol,
            "period": period,
            "ema": ema.fillna(0).tolist()[-50:],
            "latest": float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rsi/{symbol}")
async def get_rsi(
    symbol: str = "BTCUSDT",
    period: int = Query(14, ge=2, le=50, description="周期")
):
    """获取 RSI"""
    try:
        ta_service = get_complete_ta_service()
        klines = await binance_service.get_klines(symbol=symbol, limit=200)
        df = pd.DataFrame(klines)
        
        rsi = ta_service.rsi(df["close"], period)
        
        return {
            "symbol": symbol,
            "period": period,
            "rsi": rsi.fillna(50).tolist()[-50:],
            "latest": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macd/{symbol}")
async def get_macd(
    symbol: str = "BTCUSDT"
):
    """获取 MACD"""
    try:
        ta_service = get_complete_ta_service()
        klines = await binance_service.get_klines(symbol=symbol, limit=200)
        df = pd.DataFrame(klines)
        
        macd_data = ta_service.macd(df["close"])
        
        return {
            "symbol": symbol,
            "macd": macd_data["macd"].fillna(0).tolist()[-50:],
            "signal": macd_data["signal"].fillna(0).tolist()[-50:],
            "histogram": macd_data["histogram"].fillna(0).tolist()[-50:],
            "latest_macd": float(macd_data["macd"].iloc[-1]) if not pd.isna(macd_data["macd"].iloc[-1]) else 0,
            "latest_signal": float(macd_data["signal"].iloc[-1]) if not pd.isna(macd_data["signal"].iloc[-1]) else 0,
            "latest_histogram": float(macd_data["histogram"].iloc[-1]) if not pd.isna(macd_data["histogram"].iloc[-1]) else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bollinger/{symbol}")
async def get_bollinger_bands(
    symbol: str = "BTCUSDT",
    period: int = Query(20, ge=5, le=50),
    std_dev: float = Query(2.0, ge=0.5, le=4.0)
):
    """获取布林带"""
    try:
        ta_service = get_complete_ta_service()
        klines = await binance_service.get_klines(symbol=symbol, limit=200)
        df = pd.DataFrame(klines)
        
        bb = ta_service.bollinger_bands(df["close"], period, std_dev)
        
        return {
            "symbol": symbol,
            "period": period,
            "std_dev": std_dev,
            "upper": bb["upper"].fillna(0).tolist()[-50:],
            "middle": bb["middle"].fillna(0).tolist()[-50:],
            "lower": bb["lower"].fillna(0).tolist()[-50:],
            "bandwidth": bb["bandwidth"].fillna(0).tolist()[-50:],
            "percent_b": bb["percent_b"].fillna(0).tolist()[-50:],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

