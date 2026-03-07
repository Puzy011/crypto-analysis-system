import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta


class MultiTimeframeService:
    """多时间周期分析服务"""
    
    @staticmethod
    def analyze_multi_timeframe(
        symbol: str,
        timeframes: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]
    ) -> Dict[str, Any]:
        """多时间周期综合分析"""
        
        results = {}
        
        for tf in timeframes:
            results[tf] = MultiTimeframeService._analyze_single_timeframe(symbol, tf)
        
        # 综合分析
        overall = MultiTimeframeService._synthesize_analysis(results)
        
        return {
            "symbol": symbol,
            "timeframes": timeframes,
            "results": results,
            "overall": overall,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    @staticmethod
    def _analyze_single_timeframe(symbol: str, timeframe: str) -> Dict[str, Any]:
        """分析单个时间周期"""
        
        # 生成模拟数据
        count = {
            "1m": 1000,
            "5m": 500,
            "15m": 300,
            "1h": 200,
            "4h": 100,
            "1d": 50
        }.get(timeframe, 200)
        
        klines = MultiTimeframeService._generate_mock_klines(symbol, timeframe, count)
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 计算技术指标
        df = MultiTimeframeService._calculate_indicators(df)
        
        # 分析趋势
        trend = MultiTimeframeService._analyze_trend(df)
        
        # 计算支撑阻力
        levels = MultiTimeframeService._calculate_support_resistance(df)
        
        # 计算技术指标信号
        signals = MultiTimeframeService._generate_signals(df)
        
        return {
            "timeframe": timeframe,
            "data_points": len(df),
            "current_price": df['close'].iloc[-1],
            "trend": trend,
            "levels": levels,
            "signals": signals,
            "indicators": {
                "rsi": df['rsi'].iloc[-1],
                "macd": df['macd'].iloc[-1],
                "macd_signal": df['macd_signal'].iloc[-1],
                "bb_upper": df['bb_upper'].iloc[-1],
                "bb_lower": df['bb_lower'].iloc[-1],
                "bb_middle": df['bb_middle'].iloc[-1]
            }
        }
    
    @staticmethod
    def _generate_mock_klines(symbol: str, timeframe: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟K线数据"""
        
        np.random.seed(hash(symbol + timeframe) % 10000)
        
        base_price = 0.5 if symbol.upper().startswith("RIVER") else 50000
        
        prices = [base_price]
        for i in range(1, count):
            trend = 0.00005
            noise = np.random.normal(0, {
                "1m": 0.002,
                "5m": 0.004,
                "15m": 0.006,
                "1h": 0.008,
                "4h": 0.012,
                "1d": 0.02
            }.get(timeframe, 0.01))
            change = trend + noise
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # 生成K线数据
        klines = []
        now = datetime.now()
        
        # 时间增量
        delta = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1)
        }.get(timeframe, timedelta(hours=1))
        
        for i in range(count):
            timestamp = int((now - delta * (count - i)).timestamp() * 1000)
            
            open_p = prices[i]
            close_p = prices[i]
            high_p = prices[i] * (1 + abs(np.random.normal(0, 0.005)))
            low_p = prices[i] * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(1000, 100000)
            
            klines.append({
                "timestamp": timestamp,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": volume
            })
        
        return klines
    
    @staticmethod
    def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        
        # MA
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        return df
    
    @staticmethod
    def _analyze_trend(df: pd.DataFrame) -> Dict[str, Any]:
        """分析趋势"""
        
        current = df['close'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]
        ma50 = df['ma50'].iloc[-1]
        
        if current > ma20 and ma20 > ma50:
            direction = "up"
            label = "📈 上涨趋势"
            strength = min(1.0, (current - ma50) / ma50 / 0.05)
        elif current < ma20 and ma20 < ma50:
            direction = "down"
            label = "📉 下跌趋势"
            strength = min(1.0, (ma50 - current) / ma50 / 0.05)
        else:
            direction = "sideways"
            label = "➡️ 震荡趋势"
            strength = 0.3
        
        return {
            "direction": direction,
            "label": label,
            "strength": float(strength)
        }
    
    @staticmethod
    def _calculate_support_resistance(df: pd.DataFrame) -> Dict[str, Any]:
        """计算支撑阻力位"""
        
        recent = df.tail(50)
        
        support = recent['low'].min()
        resistance = recent['high'].max()
        
        # 近期高点低点
        last_10 = df.tail(10)
        recent_support = last_10['low'].min()
        recent_resistance = last_10['high'].max()
        
        return {
            "support": float(support),
            "resistance": float(resistance),
            "recent_support": float(recent_support),
            "recent_resistance": float(recent_resistance)
        }
    
    @staticmethod
    def _generate_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """生成交易信号"""
        
        signals = {
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "details": []
        }
        
        # RSI 信号
        rsi = df['rsi'].iloc[-1]
        if rsi < 30:
            signals["bullish"] += 1
            signals["details"].append({"indicator": "RSI", "type": "bullish", "value": float(rsi)})
        elif rsi > 70:
            signals["bearish"] += 1
            signals["details"].append({"indicator": "RSI", "type": "bearish", "value": float(rsi)})
        else:
            signals["neutral"] += 1
        
        # MACD 信号
        macd = df['macd'].iloc[-1]
        macd_signal = df['macd_signal'].iloc[-1]
        if macd > macd_signal:
            signals["bullish"] += 1
            signals["details"].append({"indicator": "MACD", "type": "bullish"})
        elif macd < macd_signal:
            signals["bearish"] += 1
            signals["details"].append({"indicator": "MACD", "type": "bearish"})
        else:
            signals["neutral"] += 1
        
        # 布林带信号
        current = df['close'].iloc[-1]
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        if current < bb_lower:
            signals["bullish"] += 1
            signals["details"].append({"indicator": "BB", "type": "bullish"})
        elif current > bb_upper:
            signals["bearish"] += 1
            signals["details"].append({"indicator": "BB", "type": "bearish"})
        else:
            signals["neutral"] += 1
        
        return signals
    
    @staticmethod
    def _synthesize_analysis(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """综合分析各时间周期"""
        
        # 权重（大周期权重更高）
        weights = {
            "1m": 0.05,
            "5m": 0.1,
            "15m": 0.15,
            "1h": 0.25,
            "4h": 0.25,
            "1d": 0.2
        }
        
        # 计算综合得分
        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0
        
        for tf, result in results.items():
            weight = weights.get(tf, 0.1)
            total_weight += weight
            
            signals = result["signals"]
            bullish_score += signals["bullish"] * weight
            bearish_score += signals["bearish"] * weight
        
        # 综合判断
        if bullish_score > bearish_score * 1.2:
            overall_direction = "up"
            overall_label = "📈 综合看涨"
        elif bearish_score > bullish_score * 1.2:
            overall_direction = "down"
            overall_label = "📉 综合看跌"
        else:
            overall_direction = "neutral"
            overall_label = "➡️ 综合震荡"
        
        # 各周期一致性
        directions = [result["trend"]["direction"] for result in results.values()]
        consistency = len(set(directions)) == 1
        
        return {
            "direction": overall_direction,
            "label": overall_label,
            "bullish_score": float(bullish_score),
            "bearish_score": float(bearish_score),
            "consistency": consistency,
            "timeframe_summary": {tf: result["trend"]["label"] for tf, result in results.items()}
        }
