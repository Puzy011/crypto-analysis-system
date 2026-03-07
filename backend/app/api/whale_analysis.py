"""
巨鲸/庄家分析 API
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import pandas as pd

from app.services.whale_analysis_service import (
    get_whale_analysis_service
)
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/whale-analysis", tags=["巨鲸分析"])
binance_service = BinanceService()


async def _get_kline_df(symbol: str, interval: str = "1h", limit: int = 240) -> pd.DataFrame:
    klines = await binance_service.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    df = pd.DataFrame(klines)
    if df.empty:
        raise ValueError("未获取到有效 K 线数据")
    for col in ["open", "high", "low", "close", "volume", "quoteVolume", "takerBuyQuote"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "timestamp" not in df.columns:
        raise ValueError("K 线缺少 timestamp 字段")
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).copy()
    return df


@router.get("/trade-modes")
async def get_trade_modes():
    """获取支持的交易模式配置"""
    whale_service = get_whale_analysis_service()
    modes = []
    for mode_key in ["realtime", "intraday", "longterm"]:
        profile = whale_service.get_trade_profile(mode_key)
        modes.append(
            {
                "trade_type": profile["trade_type"],
                "label": profile["label"],
                "interval": profile["interval"],
                "limit": profile["limit"],
            }
        )
    return {"modes": modes, "default": "realtime"}


@router.get("/large-orders/{symbol}")
async def detect_large_orders(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
):
    """
    检测大单交易
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df = await _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]))
        result = whale_service.detect_large_orders(symbol, klines=df, trade_type=profile["trade_type"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order-flow/{symbol}")
async def analyze_order_flow(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
):
    """
    订单流分析
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df = await _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]))
        result = whale_service.analyze_order_flow(symbol, df, trade_type=profile["trade_type"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phase/{symbol}")
async def detect_manipulation_phase(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
):
    """
    检测庄家操作阶段
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df = await _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]))
        result = whale_service.detect_manipulation_phase(symbol, df, trade_type=profile["trade_type"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full/{symbol}")
async def get_full_whale_analysis(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
):
    """
    获取完整的巨鲸分析（包含所有分析）
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df = await _get_kline_df(
            symbol,
            interval=profile["interval"],
            limit=int(profile["limit"])
        )
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(symbol, klines=df, trade_type=profile["trade_type"])
        order_flow = whale_service.analyze_order_flow(symbol, df, trade_type=profile["trade_type"])
        phase = whale_service.detect_manipulation_phase(symbol, df, trade_type=profile["trade_type"])
        smart_money = whale_service.build_smart_money_profile(
            symbol=symbol,
            klines=df,
            large_orders=large_orders,
            order_flow=order_flow,
            trade_type=profile["trade_type"],
        )
        aice_summary = whale_service.build_aice_style_summary(
            symbol=symbol,
            klines=df,
            large_orders=large_orders,
            order_flow=order_flow,
            phase_data=phase,
            trade_type=profile["trade_type"],
        )
        
        # 获取预警
        alerts = whale_service.get_whale_alerts(
            symbol,
            large_orders,
            order_flow,
            phase,
            trade_type=profile["trade_type"],
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

        risk_control = aice_summary.get("risk_control", "中风险")
        if "高" in risk_control:
            risk_level = "bearish"
            risk_emoji = "🔴"
            risk_message = "主力行为风险偏高"
        elif "低" in risk_control:
            risk_level = "bullish" if bullish_signals >= bearish_signals else "neutral"
            risk_emoji = "🟢" if risk_level == "bullish" else "🟡"
            risk_message = "主力风险偏低，可跟踪"
        
        return {
            "success": True,
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "analysis_mode": "ai",
            "overall": {
                "risk_level": risk_level,
                "risk_emoji": risk_emoji,
                "risk_message": risk_message,
                "bullish_signals": bullish_signals,
                "bearish_signals": bearish_signals
            },
            "whale_direction": aice_summary.get("whale_direction", "震荡博弈"),
            "whale_action": aice_summary.get("whale_action", "主力观望"),
            "trade_advice": aice_summary.get("trade_advice", "等待更清晰信号"),
            "risk_control": risk_control,
            "signal_explanation": aice_summary.get("signal_explanation", []),
            "summary": aice_summary.get("summary", ""),
            "extreme_30day": aice_summary.get("extreme_30day", []),
            "smart_money": smart_money,
            "smart_money_full": True,
            "entry_price": aice_summary.get("entry_price"),
            "stop_loss": aice_summary.get("stop_loss"),
            "take_profit": aice_summary.get("take_profit"),
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
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
):
    """
    获取巨鲸预警
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df = await _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]))
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(symbol, klines=df, trade_type=profile["trade_type"])
        order_flow = whale_service.analyze_order_flow(symbol, df, trade_type=profile["trade_type"])
        phase = whale_service.detect_manipulation_phase(symbol, df, trade_type=profile["trade_type"])
        
        # 获取预警
        alerts = whale_service.get_whale_alerts(
            symbol,
            large_orders,
            order_flow,
            phase,
            trade_type=profile["trade_type"],
        )
        
        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

