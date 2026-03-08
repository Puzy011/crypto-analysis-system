"""
巨鲸/庄家分析 API
"""

import asyncio
from fastapi import APIRouter, HTTPException
from datetime import datetime
import pandas as pd

from app.services.whale_analysis_service import (
    get_whale_analysis_service
)
from app.services.onchain_whale_service import get_onchain_whale_service
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/whale-analysis", tags=["巨鲸分析"])
binance_service = BinanceService()
onchain_service = get_onchain_whale_service()


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


def _build_derivatives_metrics(
    open_interest_data,
    long_short_series,
    funding_series,
    oi_hist_series,
):
    long_short_ratio = 0.0
    if long_short_series:
        sorted_ls = sorted(long_short_series, key=lambda x: x.get("timestamp", 0))
        long_short_ratio = float(sorted_ls[-1].get("long_short_ratio", 0.0))

    funding_rate = 0.0
    if funding_series:
        sorted_fr = sorted(funding_series, key=lambda x: x.get("timestamp", 0))
        funding_rate = float(sorted_fr[-1].get("funding_rate", 0.0))

    open_interest = float((open_interest_data or {}).get("open_interest", 0.0) or 0.0)
    open_interest_change_pct = 0.0
    if oi_hist_series and len(oi_hist_series) >= 2:
        sorted_hist = sorted(oi_hist_series, key=lambda x: x.get("timestamp", 0))
        prev_oi = float(sorted_hist[-2].get("sum_open_interest", 0.0) or 0.0)
        last_oi = float(sorted_hist[-1].get("sum_open_interest", 0.0) or 0.0)
        if prev_oi > 0:
            open_interest_change_pct = (last_oi - prev_oi) / prev_oi
        if open_interest <= 0:
            open_interest = last_oi

    return {
        "open_interest": open_interest,
        "long_short_ratio": long_short_ratio,
        "funding_rate": funding_rate,
        "open_interest_change_pct": float(open_interest_change_pct),
    }


async def _get_onchain_metrics_safe(symbol: str, trade_type: str):
    """链上指标容错获取，避免外部 RPC 异常直接中断主分析。"""
    try:
        return await onchain_service.get_onchain_metrics(symbol=symbol, trade_type=trade_type)
    except Exception as exc:
        return {
            "symbol": symbol.upper(),
            "trade_type": trade_type,
            "available": False,
            "reason": f"onchain_fetch_failed:{str(exc)[:120]}",
            "exchange_netflow": {
                "inflow_eth": 0.0,
                "outflow_eth": 0.0,
                "net_flow_eth": 0.0,
                "direction": "neutral",
                "direction_label": "链上数据暂不可用",
                "large_transfer_threshold_eth": 0.0,
                "large_transfer_count": 0,
                "top_transfers": [],
            },
            "activity": {
                "active_addresses": 0,
                "sample_tx_count": 0,
                "active_addresses_change_pct": 0.0,
                "history_avg": 0.0,
            },
            "gas": {
                "available": False,
                "base_fee_gwei": 0.0,
                "priority_fee_gwei": 0.0,
                "anomaly_zscore": 0.0,
                "anomaly_level": "unknown",
            },
            "holder_concentration": {
                "available": False,
                "tracked_addresses": 0,
                "total_balance_eth": 0.0,
                "top3_ratio": 0.0,
                "max_single_ratio": 0.0,
                "top_balances": [],
            },
            "updated_at": datetime.now().isoformat(),
        }


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


@router.get("/references")
async def get_whale_references():
    """获取庄家分析参考文献/资料来源"""
    whale_service = get_whale_analysis_service()
    return {
        "references": whale_service.get_research_references(),
        "timestamp": datetime.now().isoformat(),
    }


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
        df, agg_trades = await asyncio.gather(
            _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"])),
            binance_service.get_agg_trades(symbol, limit=1000),
        )
        result = whale_service.detect_large_orders(
            symbol,
            trades=agg_trades,
            klines=df,
            trade_type=profile["trade_type"]
        )
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
        df, order_book = await asyncio.gather(
            _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"])),
            binance_service.get_order_book(symbol, limit=100),
        )
        result = whale_service.analyze_order_flow(
            symbol,
            df,
            order_book=order_book,
            trade_type=profile["trade_type"]
        )
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
        (
            df,
            agg_trades,
            order_book,
            open_interest_data,
            long_short_series,
            funding_series,
            oi_hist_series,
            onchain_metrics,
        ) = await asyncio.gather(
            _get_kline_df(
                symbol,
                interval=profile["interval"],
                limit=int(profile["limit"])
            ),
            binance_service.get_agg_trades(symbol, limit=1000),
            binance_service.get_order_book(symbol, limit=100),
            binance_service.get_futures_open_interest(symbol),
            binance_service.get_global_long_short_ratio(symbol, period="1h", limit=30),
            binance_service.get_funding_rate(symbol, limit=20),
            binance_service.get_open_interest_hist(symbol, period="1h", limit=30),
            _get_onchain_metrics_safe(symbol=symbol, trade_type=profile["trade_type"]),
        )
        derivatives = _build_derivatives_metrics(
            open_interest_data,
            long_short_series,
            funding_series,
            oi_hist_series,
        )
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(
            symbol,
            trades=agg_trades,
            klines=df,
            trade_type=profile["trade_type"]
        )
        order_flow = whale_service.analyze_order_flow(
            symbol,
            df,
            order_book=order_book,
            trade_type=profile["trade_type"]
        )
        phase = whale_service.detect_manipulation_phase(symbol, df, trade_type=profile["trade_type"])
        smart_money = whale_service.build_smart_money_profile(
            symbol=symbol,
            klines=df,
            large_orders=large_orders,
            order_flow=order_flow,
            derivatives=derivatives,
            trade_type=profile["trade_type"],
        )
        indicator_matrix = whale_service.build_whale_indicator_matrix(
            symbol=symbol,
            klines=df,
            large_orders=large_orders,
            order_flow=order_flow,
            order_book=order_book,
            trades=agg_trades,
            derivatives=derivatives,
            onchain_metrics=onchain_metrics,
            trade_type=profile["trade_type"],
        )
        aice_summary = whale_service.build_aice_style_summary(
            symbol=symbol,
            klines=df,
            large_orders=large_orders,
            order_flow=order_flow,
            phase_data=phase,
            derivatives=derivatives,
            indicator_matrix=indicator_matrix,
            trade_type=profile["trade_type"],
        )
        
        # 获取预警
        alerts = whale_service.get_whale_alerts(
            symbol,
            large_orders,
            order_flow,
            phase,
            derivatives=derivatives,
            trade_type=profile["trade_type"],
        )
        data_quality = whale_service.build_data_quality_report(
            symbol=symbol,
            klines=df,
            trades=agg_trades,
            order_book=order_book,
            derivatives=derivatives,
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

        matrix_score = float((indicator_matrix.get("summary", {}) or {}).get("smart_money_score", 0.0) or 0.0)
        if matrix_score > 20:
            bullish_signals += 1
        elif matrix_score < -20:
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
            "indicator_matrix": indicator_matrix,
            "derivatives": derivatives,
            "onchain_metrics": onchain_metrics,
            "data_quality": data_quality,
            "references": whale_service.get_research_references(),
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
        (
            df,
            agg_trades,
            order_book,
            open_interest_data,
            long_short_series,
            funding_series,
            oi_hist_series,
            onchain_metrics,
        ) = await asyncio.gather(
            _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"])),
            binance_service.get_agg_trades(symbol, limit=1000),
            binance_service.get_order_book(symbol, limit=100),
            binance_service.get_futures_open_interest(symbol),
            binance_service.get_global_long_short_ratio(symbol, period="1h", limit=30),
            binance_service.get_funding_rate(symbol, limit=20),
            binance_service.get_open_interest_hist(symbol, period="1h", limit=30),
            _get_onchain_metrics_safe(symbol=symbol, trade_type=profile["trade_type"]),
        )
        derivatives = _build_derivatives_metrics(
            open_interest_data,
            long_short_series,
            funding_series,
            oi_hist_series,
        )
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(
            symbol,
            trades=agg_trades,
            klines=df,
            trade_type=profile["trade_type"]
        )
        order_flow = whale_service.analyze_order_flow(
            symbol,
            df,
            order_book=order_book,
            trade_type=profile["trade_type"]
        )
        phase = whale_service.detect_manipulation_phase(symbol, df, trade_type=profile["trade_type"])
        indicator_matrix = whale_service.build_whale_indicator_matrix(
            symbol=symbol,
            klines=df,
            large_orders=large_orders,
            order_flow=order_flow,
            order_book=order_book,
            trades=agg_trades,
            derivatives=derivatives,
            onchain_metrics=onchain_metrics,
            trade_type=profile["trade_type"],
        )
        
        # 获取预警
        alerts = whale_service.get_whale_alerts(
            symbol,
            large_orders,
            order_flow,
            phase,
            derivatives=derivatives,
            trade_type=profile["trade_type"],
        )
        
        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "derivatives": derivatives,
            "onchain_metrics": onchain_metrics,
            "indicator_matrix": indicator_matrix,
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

