"""
增强回测 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

from app.services.enhanced_backtest_service import get_enhanced_backtest_service
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/enhanced-backtest", tags=["增强回测"])
binance_service = BinanceService()


class BacktestRequest(BaseModel):
    symbol: str = "BTCUSDT"
    strategy: str = "ma_crossover"  # ma_crossover, rsi, bollinger
    initial_balance: float = 10000.0
    interval: str = "1h"
    limit: int = 500


@router.post("/run")
async def run_backtest(
    request: BacktestRequest
):
    """
    运行回测
    """
    try:
        backtest_service = get_enhanced_backtest_service()
        
        # 获取 K线数据
        klines = await binance_service.get_klines(
            symbol=request.symbol,
            interval=request.interval,
            limit=request.limit
        )
        
        df = pd.DataFrame(klines)
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["close"] = df["close"]
        df["volume"] = df["volume"]
        
        # 选择策略
        if request.strategy == "ma_crossover":
            signal_func = lambda df, idx: backtest_service.simple_ma_crossover_strategy(df, idx)
        elif request.strategy == "rsi":
            signal_func = lambda df, idx: backtest_service.rsi_strategy(df, idx)
        elif request.strategy == "bollinger":
            signal_func = lambda df, idx: backtest_service.bollinger_bands_strategy(df, idx)
        else:
            raise HTTPException(status_code=400, detail="无效的策略")
        
        # 运行回测
        result = backtest_service.run_backtest(
            df=df,
            signal_func=signal_func,
            initial_balance=request.initial_balance,
            symbol=request.symbol
        )
        
        return {
            "symbol": request.symbol,
            "strategy": request.strategy,
            "initial_balance": request.initial_balance,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_available_strategies():
    """
    获取可用策略列表
    """
    return {
        "strategies": [
            {
                "id": "ma_crossover",
                "name": "均线交叉策略",
                "description": "短期均线上穿长期均线买入，下穿卖出",
                "parameters": {
                    "fast_period": "短期均线周期",
                    "slow_period": "长期均线周期"
                }
            },
            {
                "id": "rsi",
                "name": "RSI 策略",
                "description": "RSI 超卖买入，超买卖出",
                "parameters": {
                    "period": "RSI 周期",
                    "oversold": "超卖阈值",
                    "overbought": "超买阈值"
                }
            },
            {
                "id": "bollinger",
                "name": "布林带策略",
                "description": "价格跌破下轨买入，突破上轨卖出",
                "parameters": {
                    "period": "布林带周期",
                    "std_dev": "标准差倍数"
                }
            }
        ]
    }


@router.get("/quick-test/{symbol}")
async def quick_backtest_test(
    symbol: str = "BTCUSDT",
    strategy: str = Query("ma_crossover", description="策略名称")
):
    """
    快速回测测试（简化版）
    """
    try:
        backtest_service = get_enhanced_backtest_service()
        
        klines = await binance_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=300
        )
        
        df = pd.DataFrame(klines)
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["close"] = df["close"]
        df["volume"] = df["volume"]
        
        # 简单的测试策略
        def test_strategy(df, idx):
            if idx < 50:
                return None
            
            # 50% 概率随机买卖
            import random
            if random.random() < 0.02:
                return "buy"
            elif random.random() < 0.02:
                return "sell"
            return None
        
        result = backtest_service.run_backtest(
            df=df,
            signal_func=test_strategy,
            initial_balance=10000.0,
            symbol=symbol
        )
        
        return {
            "symbol": symbol,
            "strategy": "quick_test",
            "note": "这是一个随机测试策略，用于演示回测功能",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

