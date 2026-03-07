"""
巨鲸/庄家分析 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import pandas as pd

from app.services.whale_analysis_service import (
    get_whale_analysis_service
)
from app.services.mock_binance_service import get_mock_binance_service


router = APIRouter(prefix="/api/whale-analysis", tags=["巨鲸分析"])


@router.get("/large-orders/{symbol}")
async def detect_large_orders(
    symbol: str = "BTCUSDT"
):
    """
    检测大单交易
    """
    try:
        whale_service = get_whale_analysis_service()
        result = whale_service.detect_large_orders(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order-flow/{symbol}")
async def analyze_order_flow(
    symbol: str = "BTCUSDT"
):
    """
    订单流分析
    """
    try:
        whale_service = get_whale_analysis_service()
        mock_service = get_mock_binance_service()
        
        # 获取 K线数据
        klines = mock_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=100
        )
        
        df = pd.DataFrame(klines)
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]
        
        result = whale_service.analyze_order_flow(symbol, df)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phase/{symbol}")
async def detect_manipulation_phase(
    symbol: str = "BTCUSDT"
):
    """
    检测庄家操作阶段
    """
    try:
        whale_service = get_whale_analysis_service()
        mock_service = get_mock_binance_service()
        
        # 获取 K线数据
        klines = mock_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=100
        )
        
        df = pd.DataFrame(klines)
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]
        
        result = whale_service.detect_manipulation_phase(symbol, df)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full/{symbol}")
async def get_full_whale_analysis(
    symbol: str = "BTCUSDT"
):
    """
    获取完整的巨鲸分析（包含所有分析）
    """
    try:
        whale_service = get_whale_analysis_service()
        mock_service = get_mock_binance_service()
        
        # 获取 K线数据
        klines = mock_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=100
        )
        
        df = pd.DataFrame(klines)
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(symbol)
        order_flow = whale_service.analyze_order_flow(symbol, df)
        phase = whale_service.detect_manipulation_phase(symbol, df)
        
        # 获取预警
        alerts = whale_service.get_whale_alerts(
            symbol,
            large_orders,
            order_flow,
            phase
        )
        
        # 综合判断
        risk_level = "normal"
        risk_emoji = "🟢"
        risk_message = "市场状态正常"
        
        # 根据各项指标综合判断
        bullish_signals = 0
        bearish_signals = 0
        
        if large_orders.get("direction") == "inflow":
            bullish_signals += 1
        elif large_orders.get("direction") == "outflow":
            bearish_signals += 1
        
        if "buy" in order_flow.get("flow_state", ""):
            bullish_signals += 1
        elif "sell" in order_flow.get("flow_state", ""):
            bearish_signals += 1
        
        if phase.get("phase") in ["pump", "accumulation"]:
            bullish_signals += 1
        elif phase.get("phase") in ["distribution", "washout"]:
            bearish_signals += 1
        
        if bullish_signals > bearish_signals + 1:
            risk_level = "bullish"
            risk_emoji = "🟢"
            risk_message = "多头信号较强"
        elif bearish_signals > bullish_signals + 1:
            risk_level = "bearish"
            risk_emoji = "🔴"
            risk_message = "空头信号较强"
        else:
            risk_level = "neutral"
            risk_emoji = "🟡"
            risk_message = "多空信号平衡"
        
        return {
            "symbol": symbol,
            "overall": {
                "risk_level": risk_level,
                "risk_emoji": risk_emoji,
                "risk_message": risk_message,
                "bullish_signals": bullish_signals,
                "bearish_signals": bearish_signals
            },
            "large_orders": large_orders,
            "order_flow": order_flow,
            "manipulation_phase": phase,
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{symbol}")
async def get_whale_alerts_api(
    symbol: str = "BTCUSDT"
):
    """
    获取巨鲸预警
    """
    try:
        whale_service = get_whale_analysis_service()
        mock_service = get_mock_binance_service()
        
        # 获取 K线数据
        klines = mock_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=100
        )
        
        df = pd.DataFrame(klines)
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(symbol)
        order_flow = whale_service.analyze_order_flow(symbol, df)
        phase = whale_service.detect_manipulation_phase(symbol, df)
        
        # 获取预警
        alerts = whale_service.get_whale_alerts(
            symbol,
            large_orders,
            order_flow,
            phase
        )
        
        return {
            "symbol": symbol,
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

