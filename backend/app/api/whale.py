from fastapi import APIRouter, HTTPException
import pandas as pd
from app.services.binance_service import BinanceService
from app.services.whale_service import WhaleAnalysisService

router = APIRouter()
binance_service = BinanceService()
whale_service = WhaleAnalysisService()


@router.get("/analyze/{symbol}")
async def get_whale_analysis(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100
):
    """获取庄家分析"""
    try:
        # 获取 K线数据
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        
        # 进行分析
        analysis = whale_service.analyze(df, symbol.upper())
        
        return {
            "success": True,
            "data": analysis,
            "symbol": symbol.upper(),
            "interval": interval
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/large-orders/{symbol}")
async def get_large_orders(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100
):
    """获取大单检测"""
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
        
        # 检测大单
        large_orders = whale_service.detect_large_orders(df)
        
        return {
            "success": True,
            "data": large_orders,
            "symbol": symbol.upper(),
            "count": len(large_orders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/money-flow/{symbol}")
async def get_money_flow(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100
):
    """获取资金流向分析"""
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
        
        # 资金流向分析
        money_flow = whale_service.analyze_money_flow(df)
        
        return {
            "success": True,
            "data": money_flow,
            "symbol": symbol.upper()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "whale"
    }
