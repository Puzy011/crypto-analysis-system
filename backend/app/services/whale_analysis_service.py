"""
庄家/巨鲸分析服务 - 参考 OrderFlow Analysis Tools、Crypto Whale Watcher
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import random


class WhaleAnalysisService:
    """巨鲸/庄家分析服务"""
    
    def __init__(self):
        # 历史数据
        self.whale_history = defaultdict(lambda: deque(maxlen=1000))
        self.order_flow_history = defaultdict(lambda: deque(maxlen=1000))
        
        # 大单阈值（可配置）
        self.large_order_thresholds = {
            "BTCUSDT": 1.0,  # 1 BTC 以上算大单
            "ETHUSDT": 20.0,  # 20 ETH 以上算大单
            "DEFAULT": 50000  # 5万美元以上算大单
        }
        
        # 庄家阶段识别配置
        self.phase_config = {
            "accumulation": {
                "price_range": 0.05,  # 价格波动幅度 < 5%
                "volume_increase": 1.2,  # 成交量增加 > 20%
                "duration_min": 24  # 持续至少 24 小时
            },
            "washout": {
                "price_drop": 0.05,  # 下跌 > 5%
                "volume_spike": 1.5,  # 成交量放大 > 50%
                "quick_recovery": True  # 快速收回
            },
            "pump": {
                "price_rise": 0.10,  # 上涨 > 10%
                "angle": 45,  # 上涨角度 > 45度
                "volume_confirm": 1.3  # 成交量确认 > 30%
            },
            "distribution": {
                "high_range": 0.03,  # 高位震荡 < 3%
                "volume_decline": 0.8,  # 阳线缩量 < 80%
                "net_outflow": True  # 资金净流出
            }
        }

        # 交易模式参数（对齐 aice100 的 realtime/intraday/longterm）
        self.trade_profiles: Dict[str, Dict[str, Any]] = {
            "realtime": {
                "label": "实时短线",
                "interval": "15m",
                "limit": 384,  # 约 4 天
                "large_order_quantile": 0.93,
                "large_order_median_mult": 1.6,
                "large_order_lookback": 240,
                "flow_window": 18,
                "strong_imbalance": 0.18,
                "moderate_imbalance": 0.08,
                "strong_buy_ratio": 0.56,
                "strong_sell_ratio": 0.44,
                "phase_lookback": 64,
                "phase_fast_window": 8,
                "phase_mid_window": 24,
                "accumulation_range": 0.06,
                "accumulation_fast_trend": 0.018,
                "pump_fast_trend": 0.03,
                "pump_mid_trend": 0.05,
                "distribution_mid_trend": 0.03,
                "distribution_fast_abs": 0.012,
                "washout_drop": -0.03,
                "washout_rebound": 0.02,
                "bars_per_day": 96,
            },
            "intraday": {
                "label": "日内波段",
                "interval": "1h",
                "limit": 720,  # 约 30 天
                "large_order_quantile": 0.92,
                "large_order_median_mult": 1.8,
                "large_order_lookback": 300,
                "flow_window": 24,
                "strong_imbalance": 0.22,
                "moderate_imbalance": 0.10,
                "strong_buy_ratio": 0.58,
                "strong_sell_ratio": 0.42,
                "phase_lookback": 96,
                "phase_fast_window": 10,
                "phase_mid_window": 30,
                "accumulation_range": 0.07,
                "accumulation_fast_trend": 0.02,
                "pump_fast_trend": 0.04,
                "pump_mid_trend": 0.06,
                "distribution_mid_trend": 0.04,
                "distribution_fast_abs": 0.015,
                "washout_drop": -0.035,
                "washout_rebound": 0.03,
                "bars_per_day": 24,
            },
            "longterm": {
                "label": "中长线",
                "interval": "4h",
                "limit": 720,  # 约 120 天
                "large_order_quantile": 0.90,
                "large_order_median_mult": 2.0,
                "large_order_lookback": 360,
                "flow_window": 30,
                "strong_imbalance": 0.26,
                "moderate_imbalance": 0.12,
                "strong_buy_ratio": 0.60,
                "strong_sell_ratio": 0.40,
                "phase_lookback": 120,
                "phase_fast_window": 12,
                "phase_mid_window": 42,
                "accumulation_range": 0.09,
                "accumulation_fast_trend": 0.028,
                "pump_fast_trend": 0.06,
                "pump_mid_trend": 0.10,
                "distribution_mid_trend": 0.06,
                "distribution_fast_abs": 0.02,
                "washout_drop": -0.05,
                "washout_rebound": 0.045,
                "bars_per_day": 6,
            },
        }

    def get_trade_profile(self, trade_type: Optional[str] = "realtime") -> Dict[str, Any]:
        """获取交易模式配置，未知模式回退 realtime。"""
        mode = (trade_type or "realtime").lower()
        if mode not in self.trade_profiles:
            mode = "realtime"
        profile = dict(self.trade_profiles[mode])
        profile["trade_type"] = mode
        return profile
    
    def detect_large_orders(
        self,
        symbol: str,
        trades: List[Dict[str, Any]] = None,
        klines: pd.DataFrame = None,
        trade_type: str = "realtime"
    ) -> Dict[str, Any]:
        """
        检测大单交易
        
        参考: OrderFlow Analysis Tools
        """
        profile = self.get_trade_profile(trade_type)
        if trades is None and klines is None:
            return self._generate_mock_large_orders(symbol, profile["trade_type"])

        large_orders = []
        buy_volume = 0.0
        sell_volume = 0.0
        buy_count = 0
        sell_count = 0

        # 1) 成交逐笔数据优先
        if trades:
            values = [float(t.get("price", 0)) * float(t.get("amount", 0)) for t in trades]
            threshold = (
                np.quantile(values, profile["large_order_quantile"])
                if values
                else self.large_order_thresholds["DEFAULT"]
            )
            threshold = max(float(threshold), float(self.large_order_thresholds.get(symbol, self.large_order_thresholds["DEFAULT"])))
            for trade in trades:
                amount = float(trade.get("amount", 0))
                price = float(trade.get("price", 0))
                value = price * amount
                is_buyer_maker = bool(trade.get("is_buyer_maker", False))
                if value < threshold:
                    continue
                # Binance m=true 表示买方为挂单方，即主动成交方向偏卖出
                side = "sell" if is_buyer_maker else "buy"
                large_orders.append(
                    {
                        "price": price,
                        "amount": amount,
                        "value": value,
                        "side": side,
                        "timestamp": int(trade.get("timestamp", int(datetime.now().timestamp() * 1000))),
                    }
                )
                if side == "buy":
                    buy_volume += value
                    buy_count += 1
                else:
                    sell_volume += value
                    sell_count += 1
        # 2) 无逐笔时使用 K 线近似（按 quoteVolume + takerBuyQuote）
        elif klines is not None and not klines.empty:
            df = klines.copy()
            if "quoteVolume" not in df.columns:
                df["quoteVolume"] = df["close"] * df["volume"]
            if "takerBuyQuote" not in df.columns:
                df["takerBuyQuote"] = df["quoteVolume"] * 0.5
            if "timestamp" not in df.columns:
                df["timestamp"] = np.arange(len(df))

            df = df.sort_values("timestamp")
            recent = df.tail(min(int(profile["large_order_lookback"]), len(df)))
            dynamic_threshold = float(
                max(
                    recent["quoteVolume"].quantile(profile["large_order_quantile"]),
                    recent["quoteVolume"].median() * profile["large_order_median_mult"],
                    self.large_order_thresholds["DEFAULT"],
                )
            )
            threshold = dynamic_threshold

            for _, row in recent.iterrows():
                value = float(row.get("quoteVolume", 0))
                if value < dynamic_threshold:
                    continue
                buy_quote = float(row.get("takerBuyQuote", value * 0.5))
                sell_quote = max(0.0, value - buy_quote)
                side = "buy" if buy_quote >= sell_quote else "sell"
                amount = float(row.get("volume", 0))
                price = float(row.get("close", row.get("open", 0)))
                ts = int(row.get("timestamp", int(datetime.now().timestamp() * 1000)))

                large_orders.append(
                    {
                        "price": price,
                        "amount": amount,
                        "value": value,
                        "side": side,
                        "timestamp": ts,
                    }
                )
                if side == "buy":
                    buy_volume += buy_quote
                    buy_count += 1
                else:
                    sell_volume += sell_quote
                    sell_count += 1
        else:
            threshold = self.large_order_thresholds.get(symbol, self.large_order_thresholds["DEFAULT"])
        
        # 计算大单比率
        total_large_volume = buy_volume + sell_volume
        net_flow = buy_volume - sell_volume
        
        if total_large_volume > 0:
            buy_ratio = buy_volume / total_large_volume
            sell_ratio = sell_volume / total_large_volume
        else:
            buy_ratio = sell_ratio = 0.5
        
        # 确定大单方向
        if net_flow > 0:
            direction = "inflow"
            direction_label = "🟢 大单净流入"
        elif net_flow < 0:
            direction = "outflow"
            direction_label = "🔴 大单净流出"
        else:
            direction = "neutral"
            direction_label = "⚪ 大单平衡"
        
        result = {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "data_source": "agg_trades" if trades else "kline_estimation",
            "large_order_threshold": threshold,
            "total_large_orders": len(large_orders),
            "buy_orders": buy_count,
            "sell_orders": sell_count,
            "buy_volume": float(buy_volume),
            "sell_volume": float(sell_volume),
            "net_flow": float(net_flow),
            "buy_ratio": float(buy_ratio),
            "sell_ratio": float(sell_ratio),
            "direction": direction,
            "direction_label": direction_label,
            "large_orders": sorted(large_orders, key=lambda x: x["timestamp"], reverse=True)[:20],
            "analyzed_at": datetime.now().isoformat()
        }
        
        # 记录历史
        self.whale_history[symbol].append({
            "timestamp": int(datetime.now().timestamp() * 1000),
            **result
        })
        
        return result
    
    def _generate_mock_large_orders(self, symbol: str, trade_type: str = "realtime") -> Dict[str, Any]:
        """生成模拟大单数据"""
        profile = self.get_trade_profile(trade_type)
        base_price = 65000 if "BTC" in symbol else 3500 if "ETH" in symbol else 1
        threshold = self.large_order_thresholds.get(
            symbol,
            self.large_order_thresholds["DEFAULT"]
        )
        
        large_orders = []
        num_orders = random.randint(5, 20)
        
        for i in range(num_orders):
            price = base_price * (1 + random.uniform(-0.02, 0.02))
            amount = threshold * random.uniform(1, 5)
            side = random.choice(["buy", "sell"])
            
            large_orders.append({
                "price": float(price),
                "amount": float(amount),
                "value": float(price * amount),
                "side": side,
                "timestamp": int((datetime.now() - timedelta(minutes=random.randint(0, 60))).timestamp() * 1000)
            })
        
        buy_orders = [o for o in large_orders if o["side"] == "buy"]
        sell_orders = [o for o in large_orders if o["side"] == "sell"]
        
        buy_volume = sum(o["value"] for o in buy_orders)
        sell_volume = sum(o["value"] for o in sell_orders)
        net_flow = buy_volume - sell_volume
        
        total = buy_volume + sell_volume
        if total > 0:
            buy_ratio = buy_volume / total
            sell_ratio = sell_volume / total
        else:
            buy_ratio = sell_ratio = 0.5
        
        if net_flow > 0:
            direction = "inflow"
            direction_label = "🟢 大单净流入"
        elif net_flow < 0:
            direction = "outflow"
            direction_label = "🔴 大单净流出"
        else:
            direction = "neutral"
            direction_label = "⚪ 大单平衡"
        
        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "large_order_threshold": threshold,
            "total_large_orders": len(large_orders),
            "buy_orders": len(buy_orders),
            "sell_orders": len(sell_orders),
            "buy_volume": float(buy_volume),
            "sell_volume": float(sell_volume),
            "net_flow": float(net_flow),
            "buy_ratio": float(buy_ratio),
            "sell_ratio": float(sell_ratio),
            "direction": direction,
            "direction_label": direction_label,
            "large_orders": large_orders,
            "is_mock": True,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def analyze_order_flow(
        self,
        symbol: str,
        klines: pd.DataFrame = None,
        order_book: Dict[str, Any] = None,
        trade_type: str = "realtime"
    ) -> Dict[str, Any]:
        """
        订单流分析
        
        参考: OrderFlow Analysis Tools
        """
        profile = self.get_trade_profile(trade_type)
        if klines is None or len(klines) < 20:
            return self._generate_mock_order_flow(symbol, profile["trade_type"])
        
        df = klines.copy()
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                return self._generate_mock_order_flow(symbol, profile["trade_type"])
        if "quoteVolume" not in df.columns:
            df["quoteVolume"] = df["close"] * df["volume"]
        if "takerBuyQuote" not in df.columns:
            df["takerBuyQuote"] = df["quoteVolume"] * 0.5
        
        # 1. 计算成交量指标
        df["volume_ma"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma"]
        
        # 2. 买卖盘力度（优先 taker 主动买入）
        df["buy_pressure_quote"] = df["takerBuyQuote"].clip(lower=0)
        df["sell_pressure_quote"] = (df["quoteVolume"] - df["buy_pressure_quote"]).clip(lower=0)
        df["order_imbalance"] = (
            (df["buy_pressure_quote"] - df["sell_pressure_quote"])
            / (df["quoteVolume"] + 1e-8)
        )
        df["cvd_step"] = df["buy_pressure_quote"] - df["sell_pressure_quote"]
        df["cvd"] = df["cvd_step"].cumsum()
        
        # 3. 统计
        recent = df.iloc[-min(int(profile["flow_window"]), len(df)):]
        
        avg_volume = float(recent["volume"].mean())
        max_volume = float(recent["volume"].max())
        avg_imbalance = float(recent["order_imbalance"].mean())
        net_buy_pressure = float(
            recent["buy_pressure_quote"].sum() - recent["sell_pressure_quote"].sum()
        )
        aggressive_buy_ratio = float(
            recent["buy_pressure_quote"].sum() / (recent["quoteVolume"].sum() + 1e-8)
        )
        cvd_change = float(recent["cvd"].iloc[-1] - recent["cvd"].iloc[0])

        # 盘口买卖盘不平衡（可提升短线方向判断）
        book_buy_notional = 0.0
        book_sell_notional = 0.0
        book_imbalance = 0.0
        if order_book and isinstance(order_book, dict):
            bids = order_book.get("bids", [])[:20]
            asks = order_book.get("asks", [])[:20]
            for bid in bids:
                book_buy_notional += float(bid.get("price", 0)) * float(bid.get("amount", 0))
            for ask in asks:
                book_sell_notional += float(ask.get("price", 0)) * float(ask.get("amount", 0))
            denom = book_buy_notional + book_sell_notional
            if denom > 0:
                book_imbalance = float((book_buy_notional - book_sell_notional) / denom)

        combined_imbalance = float(avg_imbalance * 0.75 + book_imbalance * 0.25)
        
        # 4. 确定订单流状态
        if combined_imbalance > profile["strong_imbalance"] and aggressive_buy_ratio > profile["strong_buy_ratio"]:
            flow_state = "strong_buy"
            flow_label = "🟢 强势买盘"
        elif combined_imbalance > profile["moderate_imbalance"]:
            flow_state = "moderate_buy"
            flow_label = "🟢 温和买盘"
        elif combined_imbalance < -profile["strong_imbalance"] and aggressive_buy_ratio < profile["strong_sell_ratio"]:
            flow_state = "strong_sell"
            flow_label = "🔴 强势卖盘"
        elif combined_imbalance < -profile["moderate_imbalance"]:
            flow_state = "moderate_sell"
            flow_label = "🔴 温和卖盘"
        else:
            flow_state = "balanced"
            flow_label = "⚪ 买卖平衡"
        
        result = {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "flow_state": flow_state,
            "flow_label": flow_label,
            "average_volume": avg_volume,
            "volume_spike_ratio": float(max_volume / avg_volume) if avg_volume > 0 else 0,
            "order_imbalance": avg_imbalance,
            "combined_imbalance": combined_imbalance,
            "book_imbalance": book_imbalance,
            "book_buy_notional": float(book_buy_notional),
            "book_sell_notional": float(book_sell_notional),
            "net_buy_pressure": float(net_buy_pressure),
            "aggressive_buy_ratio": aggressive_buy_ratio,
            "cvd_change": cvd_change,
            "buy_dominance": float(max(0, combined_imbalance + 0.5)),
            "sell_dominance": float(max(0, -combined_imbalance + 0.5)),
            "data_source": "kline+orderbook" if order_book else "kline",
            "analyzed_at": datetime.now().isoformat()
        }
        
        self.order_flow_history[symbol].append({
            "timestamp": int(datetime.now().timestamp() * 1000),
            **result
        })
        
        return result
    
    def _generate_mock_order_flow(self, symbol: str, trade_type: str = "realtime") -> Dict[str, Any]:
        """生成模拟订单流数据"""
        profile = self.get_trade_profile(trade_type)
        order_imbalance = random.uniform(-0.3, 0.3)
        
        if order_imbalance > profile["strong_imbalance"]:
            flow_state = "strong_buy"
            flow_label = "🟢 强势买盘"
        elif order_imbalance > profile["moderate_imbalance"]:
            flow_state = "moderate_buy"
            flow_label = "🟢 温和买盘"
        elif order_imbalance < -profile["strong_imbalance"]:
            flow_state = "strong_sell"
            flow_label = "🔴 强势卖盘"
        elif order_imbalance < -profile["moderate_imbalance"]:
            flow_state = "moderate_sell"
            flow_label = "🔴 温和卖盘"
        else:
            flow_state = "balanced"
            flow_label = "⚪ 买卖平衡"
        
        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "flow_state": flow_state,
            "flow_label": flow_label,
            "average_volume": random.uniform(1000, 5000),
            "volume_spike_ratio": random.uniform(1.0, 3.0),
            "order_imbalance": float(order_imbalance),
            "combined_imbalance": float(order_imbalance),
            "book_imbalance": float(order_imbalance * 0.6),
            "book_buy_notional": float(max(0.0, 1_200_000 * (0.5 + order_imbalance))),
            "book_sell_notional": float(max(0.0, 1_200_000 * (0.5 - order_imbalance))),
            "net_buy_pressure": float(order_imbalance * 10000),
            "aggressive_buy_ratio": float(max(0.0, min(1.0, 0.5 + order_imbalance))),
            "cvd_change": float(order_imbalance * 50000),
            "buy_dominance": float(max(0, order_imbalance + 0.5)),
            "sell_dominance": float(max(0, -order_imbalance + 0.5)),
            "data_source": "mock",
            "is_mock": True,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def detect_manipulation_phase(
        self,
        symbol: str,
        klines: pd.DataFrame = None,
        trade_type: str = "realtime"
    ) -> Dict[str, Any]:
        """
        检测庄家操作阶段
        
        参考: TradingView Pine Script 合集、庄家追踪指标
        """
        profile = self.get_trade_profile(trade_type)
        min_bars = max(30, int(profile["phase_mid_window"]) + 2)
        if klines is None or len(klines) < min_bars:
            return self._generate_mock_phase_detection(symbol, profile["trade_type"])
        
        df = klines.copy()
        prices = df["close"].astype(float).values
        volumes = df["volume"].astype(float).values
        highs = df["high"].astype(float).values if "high" in df.columns else prices
        lows = df["low"].astype(float).values if "low" in df.columns else prices

        lookback = min(int(profile["phase_lookback"]), len(df))
        fast_window = max(3, min(int(profile["phase_fast_window"]), lookback - 1))
        mid_window = max(fast_window + 1, min(int(profile["phase_mid_window"]), lookback - 1))

        price_range = (np.max(highs[-lookback:]) - np.min(lows[-lookback:])) / (np.mean(prices[-lookback:]) + 1e-8)
        vol_ma20 = pd.Series(volumes).rolling(window=20).mean().iloc[-1]
        volume_ratio = float(volumes[-1] / vol_ma20) if vol_ma20 and vol_ma20 > 0 else 1.0
        price_trend_fast = float((prices[-1] - prices[-fast_window]) / (prices[-fast_window] + 1e-8))
        price_trend_mid = float((prices[-1] - prices[-mid_window]) / (prices[-mid_window] + 1e-8))

        recent_returns = pd.Series(prices).pct_change().dropna().tail(max(20, fast_window * 2))
        volatility = float(recent_returns.std())
        spike_down = float(np.min(recent_returns)) if len(recent_returns) else 0.0
        rebound_window = min(max(10, fast_window), len(prices))
        rebound_strength = float((prices[-1] - np.min(prices[-rebound_window:])) / (np.min(prices[-rebound_window:]) + 1e-8))

        phase = "normal"
        phase_label = "📊 正常波动"
        confidence = 0.5
        signals = []

        # 吸筹：低波动横盘 + 量能慢增
        if (
            price_range < profile["accumulation_range"]
            and abs(price_trend_fast) < profile["accumulation_fast_trend"]
            and 1.02 <= volume_ratio <= 1.48
        ):
            phase = "accumulation"
            phase_label = "💰 吸筹阶段"
            confidence = 0.72 if profile["trade_type"] != "longterm" else 0.68
            signals = ["低位横盘", "成交量温和放大", "波动率收敛"]

        # 洗盘：短时急跌 + 放量 + 快速回收
        elif (
            spike_down < profile["washout_drop"]
            and volume_ratio > 1.25
            and rebound_strength > profile["washout_rebound"]
        ):
            phase = "washout"
            phase_label = "🧹 洗盘阶段"
            confidence = 0.68 if profile["trade_type"] != "longterm" else 0.63
            signals = ["急跌放量", "快速收回", "甩筹特征明显"]

        # 拉升：短中期共振上行 + 放量
        elif (
            price_trend_fast > profile["pump_fast_trend"]
            and price_trend_mid > profile["pump_mid_trend"]
            and volume_ratio > 1.15
        ):
            phase = "pump"
            phase_label = "🚀 拉升阶段"
            confidence = 0.81
            signals = ["趋势突破", "量价齐升", "主力推动迹象"]

        # 出货：高位窄幅 + 量能下降 + 上攻乏力
        elif (
            price_trend_mid > profile["distribution_mid_trend"]
            and abs(price_trend_fast) < profile["distribution_fast_abs"]
            and price_range < profile["accumulation_range"]
            and volume_ratio < 0.96
        ):
            phase = "distribution"
            phase_label = "📦 出货阶段"
            confidence = 0.66
            signals = ["高位震荡", "缩量滞涨", "上行动能衰减"]
        
        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "phase": phase,
            "phase_label": phase_label,
            "confidence": float(confidence),
            "price_range": float(price_range),
            "volume_ratio": float(volume_ratio),
            "price_trend": float(price_trend_fast),
            "signals": signals,
            "indicators": {
                "price_stability": float(max(0.0, 1 - price_range)),
                "volume_confirmation": float(min(volume_ratio, 2.0) / 2.0),
                "trend_strength": float(min(abs(price_trend_fast) * 10, 1.0)),
                "volatility": volatility,
                "trend_mid": price_trend_mid,
            },
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _generate_mock_phase_detection(self, symbol: str, trade_type: str = "realtime") -> Dict[str, Any]:
        """生成模拟阶段检测"""
        profile = self.get_trade_profile(trade_type)
        phases = [
            ("accumulation", "💰 吸筹阶段", 0.7),
            ("washout", "🧹 洗盘阶段", 0.6),
            ("pump", "🚀 拉升阶段", 0.8),
            ("distribution", "📦 出货阶段", 0.6),
            ("normal", "📊 正常波动", 0.5)
        ]
        
        phase, phase_label, confidence = random.choice(phases)
        
        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "phase": phase,
            "phase_label": phase_label,
            "confidence": float(confidence),
            "price_range": random.uniform(0.02, 0.10),
            "volume_ratio": random.uniform(0.8, 2.0),
            "price_trend": random.uniform(-0.05, 0.05),
            "indicators": {
                "price_stability": random.uniform(0.3, 0.9),
                "volume_confirmation": random.uniform(0.4, 0.9),
                "trend_strength": random.uniform(0.2, 0.8)
            },
            "is_mock": True,
            "analyzed_at": datetime.now().isoformat()
        }

    def build_smart_money_profile(
        self,
        symbol: str,
        klines: pd.DataFrame,
        large_orders: Dict[str, Any],
        order_flow: Dict[str, Any],
        derivatives: Dict[str, Any] = None,
        trade_type: str = "realtime"
    ) -> Dict[str, Any]:
        """
        生成 aice100 风格的聪明钱画像字段。
        """
        if klines is None or klines.empty:
            return {}

        profile = self.get_trade_profile(trade_type)
        df = klines.copy()
        if "quoteVolume" not in df.columns:
            df["quoteVolume"] = df["close"] * df["volume"]
        if "takerBuyQuote" not in df.columns:
            df["takerBuyQuote"] = df["quoteVolume"] * 0.5
        if "trades" not in df.columns:
            df["trades"] = np.maximum(100, (df["volume"] * 0.8).astype(int))

        profile_window = max(24, int(profile["flow_window"]) * 2)
        recent = df.tail(min(profile_window, len(df)))
        current_price = float(df["close"].iloc[-1])

        total_positions = float(recent["quoteVolume"].sum())
        long_positions = float(recent["takerBuyQuote"].sum())
        short_positions = max(0.0, total_positions - long_positions)
        long_short_ratio_percent = float(
            (long_positions / (short_positions + 1e-8)) * 100
        )

        total_traders = int(max(100, recent["trades"].mean() * 0.65))
        long_share = long_positions / (total_positions + 1e-8)
        long_traders = int(total_traders * long_share)
        short_traders = max(1, total_traders - long_traders)

        bullish_candles = recent[recent["close"] >= recent["open"]]
        bearish_candles = recent[recent["close"] < recent["open"]]
        long_avg_price = float(
            np.average(
                bullish_candles["close"],
                weights=np.maximum(bullish_candles["quoteVolume"], 1e-8)
            )
        ) if not bullish_candles.empty else current_price
        short_avg_price = float(
            np.average(
                bearish_candles["close"],
                weights=np.maximum(bearish_candles["quoteVolume"], 1e-8)
            )
        ) if not bearish_candles.empty else current_price

        long_pnl = (current_price - long_avg_price) / (long_avg_price + 1e-8) * long_positions
        short_pnl = (short_avg_price - current_price) / (short_avg_price + 1e-8) * short_positions

        long_profit_ratio = float(
            np.mean((recent["close"] > recent["open"]).astype(int)) * 100
        )
        short_profit_ratio = float(100 - long_profit_ratio)
        long_profit_traders = int(long_traders * long_profit_ratio / 100)
        short_profit_traders = int(short_traders * short_profit_ratio / 100)

        whale_orders = large_orders.get("large_orders", [])
        long_whales = sum(1 for o in whale_orders if o.get("side") == "buy")
        short_whales = sum(1 for o in whale_orders if o.get("side") == "sell")
        long_whale_values = [float(o.get("value", 0)) for o in whale_orders if o.get("side") == "buy"]
        short_whale_values = [float(o.get("value", 0)) for o in whale_orders if o.get("side") == "sell"]
        long_whales_qty = float(sum(long_whale_values))
        short_whales_qty = float(sum(short_whale_values))
        long_whales_avg_price = (
            float(np.mean([float(o.get("price", 0)) for o in whale_orders if o.get("side") == "buy"]))
            if long_whales > 0 else current_price
        )
        short_whales_avg_price = (
            float(np.mean([float(o.get("price", 0)) for o in whale_orders if o.get("side") == "sell"]))
            if short_whales > 0 else current_price
        )
        long_whales_profit_ratio = float(
            max(0.0, min(100.0, (current_price / (long_whales_avg_price + 1e-8) - 1) * 100))
        )
        short_whales_profit_ratio = float(
            max(0.0, min(100.0, (short_whales_avg_price / (current_price + 1e-8) - 1) * 100))
        )

        whale_direction = "偏多" if large_orders.get("net_flow", 0) > 0 else ("偏空" if large_orders.get("net_flow", 0) < 0 else "中性")
        whale_strength = float(min(100, abs(order_flow.get("combined_imbalance", order_flow.get("order_imbalance", 0))) * 260))

        derivatives = derivatives or {}
        futures_open_interest = float(derivatives.get("open_interest", 0.0) or 0.0)
        futures_ls_ratio = float(derivatives.get("long_short_ratio", 0.0) or 0.0)
        funding_rate = float(derivatives.get("funding_rate", 0.0) or 0.0)

        return {
            "symbol": symbol,
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "total_positions_m": total_positions / 1_000_000,
            "total_traders": total_traders,
            "long_short_ratio_percent": long_short_ratio_percent,
            "whale_direction": whale_direction,
            "whale_strength": whale_strength,
            "long_positions_m": long_positions / 1_000_000,
            "short_positions_m": short_positions / 1_000_000,
            "long_traders": long_traders,
            "short_traders": short_traders,
            "long_profit_ratio": long_profit_ratio,
            "short_profit_ratio": short_profit_ratio,
            "long_profit_traders": long_profit_traders,
            "short_profit_traders": short_profit_traders,
            "long_avg_price": long_avg_price,
            "short_avg_price": short_avg_price,
            "long_pnl": float(long_pnl),
            "short_pnl": float(short_pnl),
            "long_whales": int(long_whales),
            "short_whales": int(short_whales),
            "long_whales_qty": long_whales_qty,
            "short_whales_qty": short_whales_qty,
            "long_whales_avg_price": float(long_whales_avg_price),
            "short_whales_avg_price": float(short_whales_avg_price),
            "long_whales_profit_ratio": long_whales_profit_ratio,
            "short_whales_profit_ratio": short_whales_profit_ratio,
            "futures_open_interest_m": futures_open_interest / 1_000_000 if futures_open_interest else 0.0,
            "futures_long_short_ratio": futures_ls_ratio,
            "funding_rate": funding_rate,
        }

    def detect_extreme_events(
        self,
        klines: pd.DataFrame,
        limit: int = 5,
        trade_type: str = "realtime",
    ) -> List[str]:
        """提取近期极端波动事件描述"""
        if klines is None or klines.empty or len(klines) < 20:
            return []

        profile = self.get_trade_profile(trade_type)
        df = klines.copy()
        if "timestamp" not in df.columns:
            df["timestamp"] = np.arange(len(df))
        df["ret"] = df["close"].pct_change()
        df["vol_ma"] = df["volume"].rolling(20).mean()
        df["vol_spike"] = df["volume"] / (df["vol_ma"] + 1e-8)
        bars_30d = int(profile["bars_per_day"] * 30)
        df = df.dropna().tail(max(bars_30d, limit * 6))
        if df.empty:
            return []

        candidates = df.sort_values(by="ret", key=lambda s: s.abs(), ascending=False).head(limit * 2)
        events = []
        kline_label = profile["interval"]
        for _, row in candidates.iterrows():
            ts = datetime.fromtimestamp(int(row["timestamp"]) / 1000).strftime("%m-%d %H:%M")
            direction = "上涨" if row["ret"] > 0 else "下跌"
            msg = f"{ts} 出现单根 {kline_label} K 线{direction} {abs(row['ret']) * 100:.2f}%（量比 {row['vol_spike']:.2f}x）"
            if msg not in events:
                events.append(msg)
            if len(events) >= limit:
                break
        return events

    def build_aice_style_summary(
        self,
        symbol: str,
        klines: pd.DataFrame,
        large_orders: Dict[str, Any],
        order_flow: Dict[str, Any],
        phase_data: Dict[str, Any],
        derivatives: Dict[str, Any] = None,
        trade_type: str = "realtime"
    ) -> Dict[str, Any]:
        """
        输出 aice100 风格核心字段：方向/动作/建议/风险/信号解释。
        """
        profile = self.get_trade_profile(trade_type)
        derivatives = derivatives or {}
        if klines is None or klines.empty:
            return {}
        current_price = float(klines["close"].iloc[-1])
        atr = float((klines["high"] - klines["low"]).rolling(14).mean().iloc[-1]) if len(klines) >= 14 else current_price * 0.01

        sl_tp_map = {
            "realtime": (1.4, 2.0),
            "intraday": (1.8, 2.6),
            "longterm": (2.4, 3.8),
        }
        sl_mult, tp_mult = sl_tp_map.get(profile["trade_type"], (1.8, 2.6))
        stop_loss = max(0.0, current_price - sl_mult * atr)
        take_profit = current_price + tp_mult * atr

        bullish_score = 0
        bearish_score = 0

        if large_orders.get("direction") == "inflow":
            bullish_score += 2
        elif large_orders.get("direction") == "outflow":
            bearish_score += 2

        flow_state = order_flow.get("flow_state", "")
        if "buy" in flow_state:
            bullish_score += 2
        elif "sell" in flow_state:
            bearish_score += 2

        phase = phase_data.get("phase")
        if phase in {"accumulation", "pump"}:
            bullish_score += 1
        elif phase in {"distribution", "washout"}:
            bearish_score += 1

        funding_rate = float(derivatives.get("funding_rate", 0.0) or 0.0)
        long_short_ratio = float(derivatives.get("long_short_ratio", 0.0) or 0.0)
        open_interest_change_pct = float(derivatives.get("open_interest_change_pct", 0.0) or 0.0)
        if funding_rate < -0.00015 and long_short_ratio < 1:
            bullish_score += 1
        elif funding_rate > 0.00015 and long_short_ratio > 1.3:
            bearish_score += 1

        if open_interest_change_pct > 0.03 and abs(order_flow.get("combined_imbalance", 0)) > profile["moderate_imbalance"]:
            if order_flow.get("combined_imbalance", 0) > 0:
                bullish_score += 1
            else:
                bearish_score += 1

        if bullish_score >= bearish_score + 2:
            whale_direction = "多头主导"
            whale_action = "巨鲸吸筹"
            trade_advice = f"{profile['label']}建议：回调关注做多机会，止损 {stop_loss:.2f}，目标 {take_profit:.2f}"
            risk_control = "中风险" if profile["trade_type"] != "realtime" else "中高风险"
        elif bearish_score >= bullish_score + 2:
            whale_direction = "空头主导"
            whale_action = "主力派发"
            trade_advice = f"{profile['label']}建议：反弹谨慎追高，防守位 {take_profit:.2f}，下方观察 {stop_loss:.2f}"
            risk_control = "高风险"
        else:
            whale_direction = "震荡博弈"
            whale_action = "主力观望"
            trade_advice = f"{profile['label']}建议：区间交易为主，突破再跟随；参考支撑 {stop_loss:.2f} / 阻力 {take_profit:.2f}"
            risk_control = "低风险" if profile["trade_type"] != "realtime" else "中风险"

        signal_explanation = [
            f"模式：{profile['label']}（{profile['interval']} K 线）",
            f"大单方向：{large_orders.get('direction_label', '未知')}",
            f"订单流状态：{order_flow.get('flow_label', '未知')}，主动买入占比 {order_flow.get('aggressive_buy_ratio', 0)*100:.1f}%",
            f"阶段识别：{phase_data.get('phase_label', '未知')}（置信度 {phase_data.get('confidence', 0)*100:.0f}%）",
            f"订单不平衡：{order_flow.get('combined_imbalance', order_flow.get('order_imbalance', 0)):.3f}，CVD 变化 {order_flow.get('cvd_change', 0):.2f}",
            f"合约数据：资金费率 {funding_rate*100:.4f}%，多空比 {long_short_ratio:.3f}，OI变化 {open_interest_change_pct*100:.2f}%",
        ]

        summary = (
            f"{symbol} 当前{whale_direction}，疑似 {whale_action}。"
            f" 建议：{trade_advice}，风险评估：{risk_control}。"
        )

        return {
            "trade_type": profile["trade_type"],
            "trade_type_label": profile["label"],
            "whale_direction": whale_direction,
            "whale_action": whale_action,
            "trade_advice": trade_advice,
            "risk_control": risk_control,
            "signal_explanation": signal_explanation,
            "summary": summary,
            "extreme_30day": self.detect_extreme_events(klines, limit=5, trade_type=profile["trade_type"]),
            "entry_price": current_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }
    
    def get_whale_alerts(
        self,
        symbol: str,
        whale_data: Dict[str, Any],
        order_flow_data: Dict[str, Any],
        phase_data: Dict[str, Any],
        derivatives: Dict[str, Any] = None,
        trade_type: str = "realtime"
    ) -> List[Dict[str, Any]]:
        """获取巨鲸预警"""
        profile = self.get_trade_profile(trade_type)
        derivatives = derivatives or {}
        alerts = []
        
        # 1. 大单异常流入
        if whale_data.get("direction") == "inflow" and whale_data.get("buy_ratio", 0) > 0.7:
            alerts.append({
                "type": "large_inflow",
                "level": "info",
                "title": "🐋 大单持续流入",
                "message": f"大单买入占比 {whale_data['buy_ratio']*100:.1f}%，注意主力动向",
                "suggestion": f"{profile['label']}可关注后续走势，确认是否有持续资金流入"
            })
        
        # 2. 大单异常流出
        if whale_data.get("direction") == "outflow" and whale_data.get("sell_ratio", 0) > 0.7:
            alerts.append({
                "type": "large_outflow",
                "level": "warning",
                "title": "🐋 大单持续流出",
                "message": f"大单卖出占比 {whale_data['sell_ratio']*100:.1f}%，注意风险",
                "suggestion": f"{profile['label']}建议考虑适当减仓，控制风险"
            })
        
        # 3. 强势买盘
        if order_flow_data.get("flow_state") == "strong_buy":
            alerts.append({
                "type": "strong_buy_flow",
                "level": "info",
                "title": "🟢 强势买盘",
                "message": "订单流显示强势买盘，买方力量较强",
                "suggestion": f"{profile['label']}可顺势操作，但避免追高"
            })
        
        # 4. 强势卖盘
        if order_flow_data.get("flow_state") == "strong_sell":
            alerts.append({
                "type": "strong_sell_flow",
                "level": "warning",
                "title": "🔴 强势卖盘",
                "message": "订单流显示强势卖盘，卖方力量较强",
                "suggestion": f"{profile['label']}谨慎操作，等待局势明朗"
            })
        
        # 5. 拉升阶段预警
        if phase_data.get("phase") == "pump" and phase_data.get("confidence", 0) > 0.7:
            alerts.append({
                "type": "pump_phase",
                "level": "info",
                "title": "🚀 拉升阶段",
                "message": "检测到可能处于拉升阶段，注意趋势延续性",
                "suggestion": "可持有等待，但设置好止盈"
            })
        
        # 6. 出货阶段预警
        if phase_data.get("phase") == "distribution" and phase_data.get("confidence", 0) > 0.6:
            alerts.append({
                "type": "distribution_phase",
                "level": "warning",
                "title": "📦 出货阶段",
                "message": "检测到可能处于出货阶段，注意风险",
                "suggestion": "考虑分批止盈，保住利润"
            })

        funding_rate = float(derivatives.get("funding_rate", 0.0) or 0.0)
        long_short_ratio = float(derivatives.get("long_short_ratio", 0.0) or 0.0)
        oi_change = float(derivatives.get("open_interest_change_pct", 0.0) or 0.0)
        if funding_rate > 0.00025 and long_short_ratio > 1.4:
            alerts.append({
                "type": "overheated_longs",
                "level": "warning",
                "title": "🔥 多头拥挤风险",
                "message": f"资金费率 {funding_rate*100:.4f}% 且多空比 {long_short_ratio:.2f}，存在挤兑回撤风险",
                "suggestion": f"{profile['label']}建议控制杠杆，避免追高"
            })
        elif funding_rate < -0.00025 and long_short_ratio < 0.85:
            alerts.append({
                "type": "short_crowded",
                "level": "info",
                "title": "🧊 空头拥挤",
                "message": f"资金费率 {funding_rate*100:.4f}% 且多空比 {long_short_ratio:.2f}，警惕逼空反弹",
                "suggestion": f"{profile['label']}可关注反弹条件是否成立"
            })

        if abs(oi_change) > 0.05:
            alerts.append({
                "type": "open_interest_surge",
                "level": "warning" if oi_change > 0 else "info",
                "title": "📈 持仓量异动",
                "message": f"Open Interest 近阶段变化 {oi_change*100:.2f}%，市场杠杆参与度明显变化",
                "suggestion": "结合价格方向确认是真突破还是假突破"
            })
        
        return alerts

    def build_data_quality_report(
        self,
        symbol: str,
        klines: pd.DataFrame = None,
        trades: List[Dict[str, Any]] = None,
        order_book: Dict[str, Any] = None,
        derivatives: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """输出数据源覆盖与质量评分，便于前端展示可信度。"""
        derivatives = derivatives or {}
        kline_ok = klines is not None and not klines.empty and len(klines) >= 60
        trades_count = len(trades) if trades else 0
        bids = (order_book or {}).get("bids", []) if order_book else []
        asks = (order_book or {}).get("asks", []) if order_book else []
        order_book_depth = min(len(bids), len(asks))

        source_scores = {
            "kline": 0.35 if kline_ok else 0.0,
            "agg_trades": 0.25 if trades_count >= 200 else (0.12 if trades_count >= 50 else 0.0),
            "order_book": 0.20 if order_book_depth >= 20 else (0.08 if order_book_depth >= 5 else 0.0),
            "derivatives": 0.20 if derivatives.get("open_interest") or derivatives.get("long_short_ratio") else 0.0,
        }
        quality_score = float(sum(source_scores.values()))

        if quality_score >= 0.8:
            quality_level = "high"
            quality_label = "高可信"
        elif quality_score >= 0.5:
            quality_level = "medium"
            quality_label = "中可信"
        else:
            quality_level = "low"
            quality_label = "低可信"

        return {
            "symbol": symbol,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "quality_label": quality_label,
            "sources": {
                "kline": {
                    "enabled": bool(kline_ok),
                    "bars": int(len(klines)) if klines is not None else 0,
                },
                "agg_trades": {
                    "enabled": trades_count > 0,
                    "count": trades_count,
                },
                "order_book": {
                    "enabled": order_book_depth > 0,
                    "depth_levels": int(order_book_depth),
                },
                "derivatives": {
                    "enabled": bool(source_scores["derivatives"] > 0),
                    "open_interest": float(derivatives.get("open_interest", 0.0) or 0.0),
                    "long_short_ratio": float(derivatives.get("long_short_ratio", 0.0) or 0.0),
                    "funding_rate": float(derivatives.get("funding_rate", 0.0) or 0.0),
                },
            },
        }


# 全局实例
_whale_analysis_service = None


def get_whale_analysis_service() -> WhaleAnalysisService:
    """获取巨鲸分析服务单例"""
    global _whale_analysis_service
    if _whale_analysis_service is None:
        _whale_analysis_service = WhaleAnalysisService()
    return _whale_analysis_service

