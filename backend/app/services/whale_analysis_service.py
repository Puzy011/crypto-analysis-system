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
    
    def detect_large_orders(
        self,
        symbol: str,
        trades: List[Dict[str, Any]] = None,
        klines: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        检测大单交易
        
        参考: OrderFlow Analysis Tools
        """
        if trades is None and klines is None:
            # 生成模拟数据
            return self._generate_mock_large_orders(symbol)
        
        threshold = self.large_order_thresholds.get(
            symbol,
            self.large_order_thresholds["DEFAULT"]
        )
        
        large_orders = []
        buy_volume = 0.0
        sell_volume = 0.0
        buy_count = 0
        sell_count = 0
        
        if trades:
            for trade in trades:
                amount = trade.get("amount", 0)
                is_buy = trade.get("is_buyer_maker", False)
                
                if amount >= threshold:
                    large_orders.append({
                        "price": trade.get("price"),
                        "amount": amount,
                        "value": trade.get("price", 0) * amount,
                        "side": "buy" if is_buy else "sell",
                        "timestamp": trade.get("timestamp")
                    })
                    
                    if is_buy:
                        buy_volume += amount
                        buy_count += 1
                    else:
                        sell_volume += amount
                        sell_count += 1
        
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
            "large_orders": large_orders[:20],  # 最新20个大单
            "analyzed_at": datetime.now().isoformat()
        }
        
        # 记录历史
        self.whale_history[symbol].append({
            "timestamp": int(datetime.now().timestamp() * 1000),
            **result
        })
        
        return result
    
    def _generate_mock_large_orders(self, symbol: str) -> Dict[str, Any]:
        """生成模拟大单数据"""
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
        
        buy_volume = sum(o["amount"] for o in buy_orders)
        sell_volume = sum(o["amount"] for o in sell_orders)
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
        klines: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        订单流分析
        
        参考: OrderFlow Analysis Tools
        """
        if klines is None or len(klines) < 20:
            # 使用模拟分析
            return self._generate_mock_order_flow(symbol)
        
        df = klines.copy()
        
        # 1. 计算成交量指标
        df["volume_ma"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma"]
        
        # 2. 买卖盘力度
        df["buy_pressure"] = np.where(
            df["close"] > df["open"],
            df["volume"] * (df["close"] - df["low"]) / (df["high"] - df["low"] + 1e-8),
            df["volume"] * (df["high"] - df["close"]) / (df["high"] - df["low"] + 1e-8)
        )
        df["sell_pressure"] = df["volume"] - df["buy_pressure"]
        
        # 3. 订单不平衡
        df["order_imbalance"] = (df["buy_pressure"] - df["sell_pressure"]) / (df["volume"] + 1e-8)
        
        # 4. 成交量分布
        recent = df.iloc[-20:]
        
        avg_volume = float(recent["volume"].mean())
        max_volume = float(recent["volume"].max())
        min_volume = float(recent["volume"].min())
        
        avg_imbalance = float(recent["order_imbalance"].mean())
        net_buy_pressure = float(recent["buy_pressure"].sum() - recent["sell_pressure"].sum())
        
        # 5. 确定订单流状态
        if avg_imbalance > 0.2:
            flow_state = "strong_buy"
            flow_label = "🟢 强势买盘"
        elif avg_imbalance > 0.1:
            flow_state = "moderate_buy"
            flow_label = "🟢 温和买盘"
        elif avg_imbalance < -0.2:
            flow_state = "strong_sell"
            flow_label = "🔴 强势卖盘"
        elif avg_imbalance < -0.1:
            flow_state = "moderate_sell"
            flow_label = "🔴 温和卖盘"
        else:
            flow_state = "balanced"
            flow_label = "⚪ 买卖平衡"
        
        result = {
            "symbol": symbol,
            "flow_state": flow_state,
            "flow_label": flow_label,
            "average_volume": avg_volume,
            "volume_spike_ratio": float(max_volume / avg_volume) if avg_volume > 0 else 0,
            "order_imbalance": avg_imbalance,
            "net_buy_pressure": float(net_buy_pressure),
            "buy_dominance": float(max(0, avg_imbalance + 0.5)),
            "sell_dominance": float(max(0, -avg_imbalance + 0.5)),
            "analyzed_at": datetime.now().isoformat()
        }
        
        self.order_flow_history[symbol].append({
            "timestamp": int(datetime.now().timestamp() * 1000),
            **result
        })
        
        return result
    
    def _generate_mock_order_flow(self, symbol: str) -> Dict[str, Any]:
        """生成模拟订单流数据"""
        order_imbalance = random.uniform(-0.3, 0.3)
        
        if order_imbalance > 0.2:
            flow_state = "strong_buy"
            flow_label = "🟢 强势买盘"
        elif order_imbalance > 0.1:
            flow_state = "moderate_buy"
            flow_label = "🟢 温和买盘"
        elif order_imbalance < -0.2:
            flow_state = "strong_sell"
            flow_label = "🔴 强势卖盘"
        elif order_imbalance < -0.1:
            flow_state = "moderate_sell"
            flow_label = "🔴 温和卖盘"
        else:
            flow_state = "balanced"
            flow_label = "⚪ 买卖平衡"
        
        return {
            "symbol": symbol,
            "flow_state": flow_state,
            "flow_label": flow_label,
            "average_volume": random.uniform(1000, 5000),
            "volume_spike_ratio": random.uniform(1.0, 3.0),
            "order_imbalance": float(order_imbalance),
            "net_buy_pressure": float(order_imbalance * 10000),
            "buy_dominance": float(max(0, order_imbalance + 0.5)),
            "sell_dominance": float(max(0, -order_imbalance + 0.5)),
            "is_mock": True,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def detect_manipulation_phase(
        self,
        symbol: str,
        klines: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        检测庄家操作阶段
        
        参考: TradingView Pine Script 合集、庄家追踪指标
        """
        if klines is None or len(klines) < 50:
            return self._generate_mock_phase_detection(symbol)
        
        df = klines.copy()
        prices = df["close"].values
        volumes = df["volume"].values
        
        # 1. 计算价格波动
        price_range = (prices.max() - prices.min()) / prices.mean()
        
        # 2. 成交量变化
        volume_ma = pd.Series(volumes).rolling(window=20).mean()
        volume_ratio = volumes[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1
        
        # 3. 价格趋势
        recent_prices = prices[-10:]
        price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # 4. 阶段判断
        phase = "unknown"
        phase_label = "❓ 未知阶段"
        confidence = 0.3
        
        # 吸筹阶段：低位横盘，成交量温和放大
        if (price_range < 0.08 and 
            volume_ratio > 1.1 and 
            abs(price_trend) < 0.03):
            phase = "accumulation"
            phase_label = "💰 吸筹阶段"
            confidence = 0.7
        
        # 洗盘阶段：快速下跌后收回
        elif (price_trend < -0.03 and 
              volume_ratio > 1.5 and
              len(prices) > 5 and
              prices[-1] > prices[-5] * 0.95):
            phase = "washout"
            phase_label = "🧹 洗盘阶段"
            confidence = 0.6
        
        # 拉升阶段：快速上涨，成交量配合
        elif (price_trend > 0.05 and 
              volume_ratio > 1.3):
            phase = "pump"
            phase_label = "🚀 拉升阶段"
            confidence = 0.8
        
        # 出货阶段：高位震荡，资金流出
        elif (price_range < 0.05 and 
              price_trend > 0 and 
              price_trend < 0.02 and
              volume_ratio < 0.9):
            phase = "distribution"
            phase_label = "📦 出货阶段"
            confidence = 0.6
        
        # 正常阶段
        if phase == "unknown":
            phase = "normal"
            phase_label = "📊 正常波动"
            confidence = 0.5
        
        return {
            "symbol": symbol,
            "phase": phase,
            "phase_label": phase_label,
            "confidence": float(confidence),
            "price_range": float(price_range),
            "volume_ratio": float(volume_ratio),
            "price_trend": float(price_trend),
            "indicators": {
                "price_stability": float(1 - price_range),
                "volume_confirmation": float(min(volume_ratio, 2.0) / 2.0),
                "trend_strength": float(min(abs(price_trend) * 10, 1.0))
            },
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _generate_mock_phase_detection(self, symbol: str) -> Dict[str, Any]:
        """生成模拟阶段检测"""
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
    
    def get_whale_alerts(
        self,
        symbol: str,
        whale_data: Dict[str, Any],
        order_flow_data: Dict[str, Any],
        phase_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """获取巨鲸预警"""
        alerts = []
        
        # 1. 大单异常流入
        if whale_data.get("direction") == "inflow" and whale_data.get("buy_ratio", 0) > 0.7:
            alerts.append({
                "type": "large_inflow",
                "level": "info",
                "title": "🐋 大单持续流入",
                "message": f"大单买入占比 {whale_data['buy_ratio']*100:.1f}%，注意主力动向",
                "suggestion": "可关注后续走势，确认是否有持续资金流入"
            })
        
        # 2. 大单异常流出
        if whale_data.get("direction") == "outflow" and whale_data.get("sell_ratio", 0) > 0.7:
            alerts.append({
                "type": "large_outflow",
                "level": "warning",
                "title": "🐋 大单持续流出",
                "message": f"大单卖出占比 {whale_data['sell_ratio']*100:.1f}%，注意风险",
                "suggestion": "考虑适当减仓，控制风险"
            })
        
        # 3. 强势买盘
        if order_flow_data.get("flow_state") == "strong_buy":
            alerts.append({
                "type": "strong_buy_flow",
                "level": "info",
                "title": "🟢 强势买盘",
                "message": "订单流显示强势买盘，买方力量较强",
                "suggestion": "可顺势操作，但避免追高"
            })
        
        # 4. 强势卖盘
        if order_flow_data.get("flow_state") == "strong_sell":
            alerts.append({
                "type": "strong_sell_flow",
                "level": "warning",
                "title": "🔴 强势卖盘",
                "message": "订单流显示强势卖盘，卖方力量较强",
                "suggestion": "谨慎操作，等待局势明朗"
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
        
        return alerts


# 全局实例
_whale_analysis_service = None


def get_whale_analysis_service() -> WhaleAnalysisService:
    """获取巨鲸分析服务单例"""
    global _whale_analysis_service
    if _whale_analysis_service is None:
        _whale_analysis_service = WhaleAnalysisService()
    return _whale_analysis_service

