from fastapi import APIRouter, HTTPException
import pandas as pd
from app.services.binance_service import BinanceService
from app.services.technical_service import TechnicalIndicatorsService

router = APIRouter()
binance_service = BinanceService()
tech_service = TechnicalIndicatorsService()

@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str = "BTCUSDT"):
    """获取指定交易对的实时行情"""
    try:
        ticker = await binance_service.get_ticker(symbol.upper())
        return {
            "success": True,
            "data": ticker
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickers")
async def get_tickers(symbols: str = "BTCUSDT,ETHUSDT"):
    """获取多个交易对的实时行情"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        tickers = await binance_service.get_tickers(symbol_list)
        return {
            "success": True,
            "data": tickers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100
):
    """获取K线数据"""
    try:
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit
        )
        return {
            "success": True,
            "data": klines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{symbol}/indicators")
async def get_klines_with_indicators(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 200
):
    """获取K线数据及技术指标"""
    try:
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 计算技术指标
        indicators = tech_service.calculate_all_indicators(df)
        
        return {
            "success": True,
            "data": {
                "klines": klines,
                "indicators": indicators
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "market"
    }
