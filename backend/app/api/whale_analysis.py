"""
巨鲸/庄家分析 API
"""

import asyncio
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd

from app.services.whale_analysis_service import (
    get_whale_analysis_service
)
from app.services.onchain_whale_service import get_onchain_whale_service
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/whale-analysis", tags=["巨鲸分析"])
binance_service = BinanceService()
onchain_service = get_onchain_whale_service()


async def _get_kline_df(
    symbol: str,
    interval: str = "1h",
    limit: int = 240,
    market_type: str = "spot",
) -> pd.DataFrame:
    klines = await binance_service.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
        market_type=market_type,
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
    top_trader_accounts=None,
    top_trader_positions=None,
    taker_ratio_series=None,
    premium_index=None,
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

    top_account_ratio = 0.0
    if top_trader_accounts:
        sorted_top = sorted(top_trader_accounts, key=lambda x: x.get("timestamp", 0))
        top_account_ratio = float(sorted_top[-1].get("long_short_ratio", 0.0))

    top_position_ratio = 0.0
    if top_trader_positions:
        sorted_top = sorted(top_trader_positions, key=lambda x: x.get("timestamp", 0))
        top_position_ratio = float(sorted_top[-1].get("long_short_ratio", 0.0))

    taker_buy_ratio = 0.0
    if taker_ratio_series:
        sorted_taker = sorted(taker_ratio_series, key=lambda x: x.get("timestamp", 0))
        taker_buy_ratio = float(sorted_taker[-1].get("taker_buy_ratio", 0.0))

    premium_index_value = 0.0
    if premium_index:
        premium_index_value = float(premium_index.get("premium_index", 0.0) or 0.0)

    return {
        "open_interest": open_interest,
        "long_short_ratio": long_short_ratio,
        "funding_rate": funding_rate,
        "open_interest_change_pct": float(open_interest_change_pct),
        "top_trader_ls_ratio_accounts": top_account_ratio,
        "top_trader_ls_ratio_positions": top_position_ratio,
        "taker_buy_sell_ratio": taker_buy_ratio,
        "premium_index": premium_index_value,
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
            "applicable": True,
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


def _build_analysis_health(
    data_quality: Dict[str, Any],
    large_orders: Dict[str, Any],
    order_flow: Dict[str, Any],
    onchain_metrics: Dict[str, Any],
    market_type: str,
) -> Dict[str, Any]:
    """输出分析可用性与降级原因，避免在弱数据条件下给出过度结论。"""
    quality_score = float((data_quality or {}).get("quality_score", 0.0) or 0.0)
    sources = (data_quality or {}).get("sources", {}) or {}
    trades_count = int(((sources.get("agg_trades", {}) or {}).get("count", 0) or 0))
    order_book_depth = int(((sources.get("order_book", {}) or {}).get("depth_levels", 0) or 0))
    derivatives_enabled = bool(((sources.get("derivatives", {}) or {}).get("enabled", False)))
    onchain_available = bool((onchain_metrics or {}).get("available", False))
    onchain_applicable = bool((onchain_metrics or {}).get("applicable", True))

    blockers: List[str] = []
    if trades_count < 80:
        blockers.append(f"逐笔成交样本不足（当前 {trades_count}）")
    if order_book_depth < 8:
        blockers.append(f"订单簿深度不足（当前 {order_book_depth} 档）")
    if not derivatives_enabled and market_type == "futures":
        blockers.append("合约指标缺失（资金费率/OI/多空比不可用）")
    if not onchain_available and onchain_applicable:
        blockers.append("链上真实指标不可用")

    # 低质量 + 核心微观结构缺失时，判定为降级模式
    is_degraded = bool(quality_score < 0.55 or (trades_count < 50 and order_book_depth < 5))

    if is_degraded:
        mode = "degraded"
        mode_label = "降级分析"
        summary = "关键微观结构数据不足，当前结论仅供参考，不建议重仓。"
    elif quality_score < 0.8:
        mode = "cautious"
        mode_label = "谨慎可用"
        summary = "数据可用但完整性一般，建议轻仓并等待确认信号。"
    else:
        mode = "full"
        mode_label = "完整分析"
        summary = "数据完整度较好，可按信号执行但仍需风控。"

    return {
        "mode": mode,
        "mode_label": mode_label,
        "is_degraded": is_degraded,
        "quality_score": quality_score,
        "summary": summary,
        "blockers": blockers,
        "input_snapshot": {
            "trades_count": trades_count,
            "order_book_depth": order_book_depth,
            "onchain_available": onchain_available,
            "onchain_applicable": onchain_applicable,
            "derivatives_enabled": derivatives_enabled,
            "large_order_source": large_orders.get("data_source", "unknown"),
            "order_flow_source": order_flow.get("data_source", "unknown"),
        },
    }


def _build_action_plan(
    profile: Dict[str, Any],
    aice_summary: Dict[str, Any],
    large_orders: Dict[str, Any],
    order_flow: Dict[str, Any],
    phase: Dict[str, Any],
    indicator_matrix: Dict[str, Any],
    analysis_health: Dict[str, Any],
) -> Dict[str, Any]:
    """基于当前结果输出可执行建议，明确触发条件与失效条件。"""
    summary_block = (indicator_matrix or {}).get("summary", {}) or {}
    matrix_score = float(summary_block.get("smart_money_score", 0.0) or 0.0)
    combined_imbalance = float(order_flow.get("combined_imbalance", order_flow.get("order_imbalance", 0.0)) or 0.0)
    phase_name = str(phase.get("phase", "normal"))
    quality_score = float(analysis_health.get("quality_score", 0.0) or 0.0)

    bullish_votes = 0
    bearish_votes = 0
    reasons: List[str] = []

    if large_orders.get("direction") == "inflow":
        bullish_votes += 1
        reasons.append("大单净流入")
    elif large_orders.get("direction") == "outflow":
        bearish_votes += 1
        reasons.append("大单净流出")

    if combined_imbalance > 0.08:
        bullish_votes += 1
        reasons.append(f"订单流偏多（{combined_imbalance:.3f}）")
    elif combined_imbalance < -0.08:
        bearish_votes += 1
        reasons.append(f"订单流偏空（{combined_imbalance:.3f}）")

    if matrix_score > 20:
        bullish_votes += 1
        reasons.append(f"SmartMoney得分偏多（{matrix_score:.1f}）")
    elif matrix_score < -20:
        bearish_votes += 1
        reasons.append(f"SmartMoney得分偏空（{matrix_score:.1f}）")

    if phase_name in {"accumulation", "pump"}:
        bullish_votes += 1
        reasons.append(f"阶段识别为 {phase.get('phase_label', phase_name)}")
    elif phase_name in {"distribution", "washout"}:
        bearish_votes += 1
        reasons.append(f"阶段识别为 {phase.get('phase_label', phase_name)}")

    if bullish_votes >= bearish_votes + 2:
        bias = "long"
        bias_label = "顺势偏多"
    elif bearish_votes >= bullish_votes + 2:
        bias = "short"
        bias_label = "顺势偏空"
    else:
        bias = "neutral"
        bias_label = "观望等待"

    actionable = bool(not analysis_health.get("is_degraded", False) and bias != "neutral")
    confidence = min(0.95, max(0.2, quality_score * (0.55 + 0.1 * max(bullish_votes, bearish_votes))))

    entry_price = aice_summary.get("entry_price")
    stop_loss = aice_summary.get("stop_loss")
    take_profit = aice_summary.get("take_profit")
    entry_text = f"参考入场位 {entry_price:.4f}" if isinstance(entry_price, (int, float)) else "等待形态确认后入场"
    sl_text = f"失效位 {stop_loss:.4f}" if isinstance(stop_loss, (int, float)) else "固定风险后入场"
    tp_text = f"目标位 {take_profit:.4f}" if isinstance(take_profit, (int, float)) else "分批止盈"

    if analysis_health.get("mode") == "full":
        size_advice = "中等仓位（30%-50%）"
    elif analysis_health.get("mode") == "cautious":
        size_advice = "轻仓试单（15%-30%）"
    else:
        size_advice = "观望或极轻仓（<15%）"

    trigger_points: List[str] = []
    if bias == "long":
        trigger_points.extend(
            [
                "订单流继续维持正不平衡且主动买盘占优",
                "价格回踩不破入场区域并重新放量",
            ]
        )
    elif bias == "short":
        trigger_points.extend(
            [
                "订单流继续维持负不平衡且主动卖盘占优",
                "反弹受阻并出现放量回落",
            ]
        )
    else:
        trigger_points.extend(
            [
                "等待大单方向与订单流方向重新同向",
                "等待SmartMoney得分绝对值突破 25 再执行",
            ]
        )

    return {
        "trade_type": profile.get("trade_type", "realtime"),
        "trade_type_label": profile.get("label", "实时短线"),
        "bias": bias,
        "bias_label": bias_label,
        "actionable": actionable,
        "confidence": float(confidence),
        "position_size_advice": size_advice,
        "entry": entry_text,
        "stop_loss": sl_text,
        "take_profit": tp_text,
        "trigger_points": trigger_points,
        "reasons": reasons[:6],
        "votes": {
            "bullish_votes": bullish_votes,
            "bearish_votes": bearish_votes,
        },
    }


def _build_mode_note(trade_type: str) -> str:
    mode = (trade_type or "realtime").lower()
    notes = {
        "realtime": "实时短线：以订单流/大单/盘口为核心，适合短线信号跟踪。",
        "intraday": "日内博弈：侧重 24H 趋势与关键位确认，避免高频追单。",
        "longterm": "趋势布局：关注宏观趋势与成本带，强调风险控制与持仓周期。",
    }
    return notes.get(mode, "实时分析模式。")


def _build_report_block(
    profile: Dict[str, Any],
    market_type: str,
    market_label: str,
    aice_summary: Dict[str, Any],
    analysis_health: Dict[str, Any],
    action_plan: Dict[str, Any],
    risk_level: str,
    entry_price: Any,
    stop_loss: Any,
    take_profit: Any,
    generated_at: str,
) -> Dict[str, Any]:
    invalidations: List[str] = []
    if isinstance(stop_loss, (int, float)) and stop_loss > 0:
        invalidations.append(f"价格跌破止损位 {stop_loss:.4f}")
    if analysis_health.get("is_degraded", False):
        invalidations.append("关键数据不足，信号需重新确认")

    return {
        "mode": profile.get("trade_type", "realtime"),
        "mode_label": profile.get("label", "实时短线"),
        "mode_note": _build_mode_note(profile.get("trade_type", "realtime")),
        "market_type": market_type,
        "market_label": market_label,
        "direction": aice_summary.get("whale_direction", "震荡博弈"),
        "action": aice_summary.get("whale_action", "主力观望"),
        "advice": aice_summary.get("trade_advice", ""),
        "risk_control": aice_summary.get("risk_control", "中风险"),
        "risk_level": risk_level,
        "confidence": float(action_plan.get("confidence", 0.0) or 0.0),
        "key_levels": {
            "entry": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        },
        "entry_conditions": action_plan.get("trigger_points", []) or [],
        "invalidation_conditions": invalidations,
        "signal_explanation": aice_summary.get("signal_explanation", []) or [],
        "extreme_events": aice_summary.get("extreme_30day", []) or [],
        "analysis_health_summary": analysis_health.get("summary", ""),
        "analysis_health_blockers": analysis_health.get("blockers", []) or [],
        "generated_at": generated_at,
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
    market_type: str = "spot",
):
    """
    检测大单交易
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df, agg_trades, ticker_24h = await asyncio.gather(
            _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]), market_type=market_type),
            binance_service.get_agg_trades(symbol, limit=1000, market_type=market_type),
            binance_service.get_ticker(symbol, market_type=market_type),
        )
        result = whale_service.detect_large_orders(
            symbol,
            trades=agg_trades,
            klines=df,
            trade_type=profile["trade_type"],
            ticker_24h=ticker_24h,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order-flow/{symbol}")
async def analyze_order_flow(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
    market_type: str = "spot",
):
    """
    订单流分析
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df, order_book, agg_trades = await asyncio.gather(
            _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]), market_type=market_type),
            binance_service.get_order_book(symbol, limit=100, market_type=market_type),
            binance_service.get_agg_trades(symbol, limit=1000, market_type=market_type),
        )
        result = whale_service.analyze_order_flow(
            symbol,
            df,
            order_book=order_book,
            trades=agg_trades,
            trade_type=profile["trade_type"]
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phase/{symbol}")
async def detect_manipulation_phase(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
    market_type: str = "spot",
):
    """
    检测庄家操作阶段
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        df = await _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]), market_type=market_type)
        result = whale_service.detect_manipulation_phase(symbol, df, trade_type=profile["trade_type"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full/{symbol}")
async def get_full_whale_analysis(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
    market_type: str = "spot",
):
    """
    获取完整的巨鲸分析（包含所有分析）
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        normalized_market = str(market_type or "spot").lower()
        if normalized_market not in {"spot", "futures"}:
            normalized_market = "spot"
        market_label = "合约" if normalized_market == "futures" else "现货"

        df, agg_trades, order_book, ticker_24h, onchain_metrics = await asyncio.gather(
            _get_kline_df(
                symbol,
                interval=profile["interval"],
                limit=int(profile["limit"]),
                market_type=normalized_market,
            ),
            binance_service.get_agg_trades(symbol, limit=1000, market_type=normalized_market),
            binance_service.get_order_book(symbol, limit=100, market_type=normalized_market),
            binance_service.get_ticker(symbol, market_type=normalized_market),
            _get_onchain_metrics_safe(symbol=symbol, trade_type=profile["trade_type"]),
        )

        if normalized_market == "futures":
            (
                open_interest_data,
                long_short_series,
                funding_series,
                oi_hist_series,
                top_trader_accounts,
                top_trader_positions,
                taker_ratio_series,
                premium_index,
            ) = await asyncio.gather(
                binance_service.get_futures_open_interest(symbol),
                binance_service.get_global_long_short_ratio(symbol, period="1h", limit=30),
                binance_service.get_funding_rate(symbol, limit=20),
                binance_service.get_open_interest_hist(symbol, period="1h", limit=30),
                binance_service.get_top_trader_long_short_ratio(symbol, period="1h", limit=30, kind="account"),
                binance_service.get_top_trader_long_short_ratio(symbol, period="1h", limit=30, kind="position"),
                binance_service.get_taker_buy_sell_ratio(symbol, period="1h", limit=30),
                binance_service.get_premium_index(symbol),
            )
        else:
            open_interest_data = None
            long_short_series = []
            funding_series = []
            oi_hist_series = []
            top_trader_accounts = []
            top_trader_positions = []
            taker_ratio_series = []
            premium_index = None

        derivatives = _build_derivatives_metrics(
            open_interest_data,
            long_short_series,
            funding_series,
            oi_hist_series,
            top_trader_accounts=top_trader_accounts,
            top_trader_positions=top_trader_positions,
            taker_ratio_series=taker_ratio_series,
            premium_index=premium_index,
        )
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(
            symbol,
            trades=agg_trades,
            klines=df,
            trade_type=profile["trade_type"],
            ticker_24h=ticker_24h,
        )
        order_flow = whale_service.analyze_order_flow(
            symbol,
            df,
            order_book=order_book,
            trades=agg_trades,
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
        trend_forecast = whale_service.build_trend_forecast(
            klines=df,
            trade_type=profile["trade_type"],
        )
        key_levels = whale_service.build_key_levels(
            klines=df,
            trade_type=profile["trade_type"],
        )
        cost_band = whale_service.build_cost_band(
            klines=df,
            trade_type=profile["trade_type"],
        )
        data_quality = whale_service.build_data_quality_report(
            symbol=symbol,
            klines=df,
            trades=agg_trades,
            order_book=order_book,
            derivatives=derivatives,
            market_type=normalized_market,
        )
        analysis_health = _build_analysis_health(
            data_quality=data_quality,
            large_orders=large_orders,
            order_flow=order_flow,
            onchain_metrics=onchain_metrics,
            market_type=normalized_market,
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

        # 新增：持续性大户追踪
        persistent_whales = whale_service.track_persistent_whales(
            symbol=symbol,
            trades=agg_trades,
            large_orders=large_orders,
            window_minutes=60,
        )

        # 新增：聪明钱估算
        smart_money_distribution = whale_service.estimate_smart_money_distribution(
            symbol=symbol,
            trades=agg_trades,
            klines=df,
            large_orders=large_orders,
        )

        # 新增：Volume Profile
        volume_profile = whale_service.calculate_volume_profile(
            klines=df,
            bins=50,
        )

        # 新增：订单簿不平衡
        order_book_imbalance = whale_service.calculate_order_book_imbalance(
            order_book=order_book,
            depth_levels=10,
        )

        # 新增：流动性墙检测
        liquidity_walls = whale_service.detect_liquidity_walls(
            order_book=order_book,
            threshold_multiplier=3.0,
        )

        # 新增：主力成本估算
        whale_cost_basis = whale_service.estimate_whale_cost_basis(
            large_orders=large_orders,
        )

        data_quality = whale_service.build_data_quality_report(
            symbol=symbol,
            klines=df,
            trades=agg_trades,
            order_book=order_book,
            derivatives=derivatives,
            market_type=normalized_market,
        )
        analysis_health = _build_analysis_health(
            data_quality=data_quality,
            large_orders=large_orders,
            order_flow=order_flow,
            onchain_metrics=onchain_metrics,
            market_type=normalized_market,
        )
        action_plan = _build_action_plan(
            profile=profile,
            aice_summary=aice_summary,
            large_orders=large_orders,
            order_flow=order_flow,
            phase=phase,
            indicator_matrix=indicator_matrix,
            analysis_health=analysis_health,
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

        analysis_mode = "degraded" if analysis_health.get("is_degraded", False) else "ai"
        trade_advice = aice_summary.get("trade_advice", "等待更清晰信号")
        if analysis_mode == "degraded":
            risk_level = "neutral"
            risk_emoji = "🟡"
            risk_message = "数据源受限，当前为降级分析"
            trade_advice = "关键数据不足，建议观望或极轻仓试单，等待真实成交和盘口恢复。"
        elif analysis_health.get("mode") == "cautious":
            trade_advice = f"{trade_advice}（数据完整性一般，建议轻仓执行）"

        generated_at = datetime.now().isoformat()
        report = _build_report_block(
            profile=profile,
            market_type=normalized_market,
            market_label=market_label,
            aice_summary={
                "whale_direction": aice_summary.get("whale_direction", "震荡博弈"),
                "whale_action": aice_summary.get("whale_action", "主力观望"),
                "trade_advice": trade_advice,
                "risk_control": risk_control,
                "signal_explanation": aice_summary.get("signal_explanation", []),
                "extreme_30day": aice_summary.get("extreme_30day", []),
            },
            analysis_health=analysis_health,
            action_plan=action_plan,
            risk_level=risk_level,
            entry_price=aice_summary.get("entry_price"),
            stop_loss=aice_summary.get("stop_loss"),
            take_profit=aice_summary.get("take_profit"),
            generated_at=generated_at,
        )

        def _format_level(value: Any) -> str:
            if isinstance(value, (int, float)):
                if abs(value) >= 1:
                    return f"{value:.2f}"
                return f"{value:.6f}"
            return "-"

        share_text = (
            f"{symbol} {market_label}·{profile['label']} | "
            f"方向: {report.get('direction')} | 动作: {report.get('action')} | "
            f"建议: {report.get('advice')} | 风险: {report.get('risk_control')} | "
            f"入场: {_format_level(aice_summary.get('entry_price'))} / "
            f"止损: {_format_level(aice_summary.get('stop_loss'))} / "
            f"止盈: {_format_level(aice_summary.get('take_profit'))} | "
            f"时间: {generated_at[:19]}"
        )

        recent_queries = whale_service.record_query(
            symbol=symbol,
            trade_type=profile["trade_type"],
            market_type=normalized_market,
        )

        return {
            "success": True,
            "symbol": symbol,
            "market_type": normalized_market,
            "market_label": market_label,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "analysis_mode": analysis_mode,
            "overall": {
                "risk_level": risk_level,
                "risk_emoji": risk_emoji,
                "risk_message": risk_message,
                "bullish_signals": bullish_signals,
                "bearish_signals": bearish_signals
            },
            "whale_direction": aice_summary.get("whale_direction", "震荡博弈"),
            "whale_action": aice_summary.get("whale_action", "主力观望"),
            "trade_advice": trade_advice,
            "risk_control": risk_control,
            "signal_explanation": aice_summary.get("signal_explanation", []),
            "summary": aice_summary.get("summary", ""),
            "extreme_30day": aice_summary.get("extreme_30day", []),
            "smart_money": smart_money,
            "smart_money_full": True,
            "indicator_matrix": indicator_matrix,
            "derivatives": derivatives,
            "position_regime": (indicator_matrix.get("derivatives_metrics", {}) or {}).get("position_regime"),
            "trend_forecast": trend_forecast,
            "key_levels": key_levels,
            "cost_band": cost_band,
            "onchain_metrics": onchain_metrics,
            "data_quality": data_quality,
            "analysis_health": analysis_health,
            "action_plan": action_plan,
            "report": report,
            "share_text": share_text,
            "recent_queries": recent_queries,
            "references": whale_service.get_research_references(),
            "entry_price": aice_summary.get("entry_price"),
            "stop_loss": aice_summary.get("stop_loss"),
            "take_profit": aice_summary.get("take_profit"),
            "large_orders": large_orders,
            "order_flow": order_flow,
            "manipulation_phase": phase,
            "alerts": alerts,
            "alert_count": len(alerts),
            # 新增优化指标
            "persistent_whales": persistent_whales,
            "smart_money_distribution": smart_money_distribution,
            "volume_profile": volume_profile,
            "order_book_imbalance": order_book_imbalance,
            "liquidity_walls": liquidity_walls,
            "whale_cost_basis": whale_cost_basis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{symbol}")
async def get_whale_alerts_api(
    symbol: str = "BTCUSDT",
    trade_type: str = "realtime",
    market_type: str = "spot",
):
    """
    获取巨鲸预警
    """
    try:
        whale_service = get_whale_analysis_service()
        profile = whale_service.get_trade_profile(trade_type)
        normalized_market = str(market_type or "spot").lower()
        if normalized_market not in {"spot", "futures"}:
            normalized_market = "spot"
        market_label = "合约" if normalized_market == "futures" else "现货"

        df, agg_trades, order_book, ticker_24h, onchain_metrics = await asyncio.gather(
            _get_kline_df(symbol, interval=profile["interval"], limit=int(profile["limit"]), market_type=normalized_market),
            binance_service.get_agg_trades(symbol, limit=1000, market_type=normalized_market),
            binance_service.get_order_book(symbol, limit=100, market_type=normalized_market),
            binance_service.get_ticker(symbol, market_type=normalized_market),
            _get_onchain_metrics_safe(symbol=symbol, trade_type=profile["trade_type"]),
        )

        if normalized_market == "futures":
            (
                open_interest_data,
                long_short_series,
                funding_series,
                oi_hist_series,
                top_trader_accounts,
                top_trader_positions,
                taker_ratio_series,
                premium_index,
            ) = await asyncio.gather(
                binance_service.get_futures_open_interest(symbol),
                binance_service.get_global_long_short_ratio(symbol, period="1h", limit=30),
                binance_service.get_funding_rate(symbol, limit=20),
                binance_service.get_open_interest_hist(symbol, period="1h", limit=30),
                binance_service.get_top_trader_long_short_ratio(symbol, period="1h", limit=30, kind="account"),
                binance_service.get_top_trader_long_short_ratio(symbol, period="1h", limit=30, kind="position"),
                binance_service.get_taker_buy_sell_ratio(symbol, period="1h", limit=30),
                binance_service.get_premium_index(symbol),
            )
        else:
            open_interest_data = None
            long_short_series = []
            funding_series = []
            oi_hist_series = []
            top_trader_accounts = []
            top_trader_positions = []
            taker_ratio_series = []
            premium_index = None

        derivatives = _build_derivatives_metrics(
            open_interest_data,
            long_short_series,
            funding_series,
            oi_hist_series,
            top_trader_accounts=top_trader_accounts,
            top_trader_positions=top_trader_positions,
            taker_ratio_series=taker_ratio_series,
            premium_index=premium_index,
        )
        
        # 执行各项分析
        large_orders = whale_service.detect_large_orders(
            symbol,
            trades=agg_trades,
            klines=df,
            trade_type=profile["trade_type"],
            ticker_24h=ticker_24h,
        )
        order_flow = whale_service.analyze_order_flow(
            symbol,
            df,
            order_book=order_book,
            trades=agg_trades,
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

        data_quality = whale_service.build_data_quality_report(
            symbol=symbol,
            klines=df,
            trades=agg_trades,
            order_book=order_book,
            derivatives=derivatives,
            market_type=normalized_market,
        )
        analysis_health = _build_analysis_health(
            data_quality=data_quality,
            large_orders=large_orders,
            order_flow=order_flow,
            onchain_metrics=onchain_metrics,
            market_type=normalized_market,
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
            "market_type": normalized_market,
            "market_label": market_label,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "derivatives": derivatives,
            "position_regime": (indicator_matrix.get("derivatives_metrics", {}) or {}).get("position_regime"),
            "onchain_metrics": onchain_metrics,
            "indicator_matrix": indicator_matrix,
            "data_quality": data_quality,
            "analysis_health": analysis_health,
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": generated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

