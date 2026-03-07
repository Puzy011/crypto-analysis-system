import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class EnhancedPredictionService:
    """增强版趋势预测服务"""
    
    @staticmethod
    def predict_enhanced_trend(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """增强版趋势预测"""
        
        # 生成模拟数据
        klines = EnhancedPredictionService._generate_mock_klines(symbol, 300)
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 计算高级指标
        df = EnhancedPredictionService._calculate_advanced_indicators(df)
        
        # 多模型预测
        predictions = {
            "technical": EnhancedPredictionService._predict_technical(df),
            "machine_learning": EnhancedPredictionService._predict_ml(df),
            "pattern": EnhancedPredictionService._predict_pattern(df),
            "sentiment": EnhancedPredictionService._predict_sentiment(df)
        }
        
        # 综合预测
        overall = EnhancedPredictionService._synthesize_predictions(predictions)
        
        # 价格预测
        price_prediction = EnhancedPredictionService._predict_price_levels(df, overall)
        
        # 风险评估
        risk_assessment = EnhancedPredictionService._assess_risk(df, overall)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "overall": overall,
            "predictions": predictions,
            "price_prediction": price_prediction,
            "risk_assessment": risk_assessment,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    @staticmethod
    def _generate_mock_klines(symbol: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟K线数据"""
        
        np.random.seed(42)
        
        base_price = 0.5 if symbol.upper().startswith("RIVER") else 50000
        
        # 生成带趋势的价格序列
        prices = [base_price]
        for i in range(1, count):
            # 多周期趋势叠加
            long_trend = 0.0001 * np.sin(i * 0.05)
            medium_trend = 0.0003 * np.sin(i * 0.1)
            short_noise = np.random.normal(0, 0.008)
            
            change = long_trend + medium_trend + short_noise
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # 生成K线数据
        klines = []
        now = datetime.now()
        
        for i in range(count):
            timestamp = int((now - timedelta(hours=count-i)).timestamp() * 1000)
            
            open_p = prices[i]
            close_p = prices[i]
            high_p = prices[i] * (1 + abs(np.random.normal(0, 0.006)))
            low_p = prices[i] * (1 - abs(np.random.normal(0, 0.006)))
            volume = np.random.uniform(10000, 100000)
            
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
    def _calculate_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """计算高级技术指标"""
        
        # 基础指标
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma100'] = df['close'].rolling(window=100).mean()
        
        # EMA
        df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # RSI 不同周期
        df['rsi7'] = 100 - (100 / (1 + (delta.where(delta > 0, 0)).rolling(window=7).mean() / (-delta.where(delta < 0, 0)).rolling(window=7).mean()))
        df['rsi21'] = 100 - (100 / (1 + (delta.where(delta > 0, 0)).rolling(window=21).mean() / (-delta.where(delta < 0, 0)).rolling(window=21).mean()))
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # KDJ
        low_min = df['low'].rolling(window=9).min()
        high_max = df['high'].rolling(window=9).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        df['k'] = rsv.ewm(com=2, adjust=False).mean()
        df['d'] = df['k'].ewm(com=2, adjust=False).mean()
        df['j'] = 3 * df['k'] - 2 * df['d']
        
        # 威廉指标
        df['wr'] = (high_max - df['close']) / (high_max - low_min) * -100
        
        # CCI
        tp = (df['high'] + df['low'] + df['close']) / 3
        ma_tp = tp.rolling(window=20).mean()
        md = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        df['cci'] = (tp - ma_tp) / (0.015 * md)
        
        # OBV
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        df['obv'] = obv
        df['obv_ma'] = obv.rolling(window=10).mean()
        
        # 波动率
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(24)  # 小时级年化
        
        # 趋势强度
        df['trend_strength'] = abs(df['close'] - df['ma50']) / df['ma50']
        
        return df
    
    @staticmethod
    def _predict_technical(df: pd.DataFrame) -> Dict[str, Any]:
        """技术分析预测"""
        
        current = df['close'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]
        ma50 = df['ma50'].iloc[-1]
        ma100 = df['ma100'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        macd = df['macd'].iloc[-1]
        macd_signal = df['macd_signal'].iloc[-1]
        
        bullish_signals = 0
        bearish_signals = 0
        
        # MA 信号
        if current > ma20 > ma50 > ma100:
            bullish_signals += 3
        elif current < ma20 < ma50 < ma100:
            bearish_signals += 3
        elif current > ma20:
            bullish_signals += 1
        elif current < ma20:
            bearish_signals += 1
        
        # RSI 信号
        if rsi < 30:
            bullish_signals += 2
        elif rsi > 70:
            bearish_signals += 2
        elif rsi < 40:
            bullish_signals += 1
        elif rsi > 60:
            bearish_signals += 1
        
        # MACD 信号
        if macd > macd_signal and macd > 0:
            bullish_signals += 2
        elif macd < macd_signal and macd < 0:
            bearish_signals += 2
        elif macd > macd_signal:
            bullish_signals += 1
        elif macd < macd_signal:
            bearish_signals += 1
        
        # KDJ 信号
        k = df['k'].iloc[-1]
        d = df['d'].iloc[-1]
        j = df['j'].iloc[-1]
        if k < 20 and d < 20 and k > d:
            bullish_signals += 2
        elif k > 80 and d > 80 and k < d:
            bearish_signals += 2
        
        total_signals = bullish_signals + bearish_signals
        confidence = abs(bullish_signals - bearish_signals) / max(total_signals, 1)
        
        if bullish_signals > bearish_signals:
            direction = "up"
            label = "📈 技术看涨"
        elif bearish_signals > bullish_signals:
            direction = "down"
            label = "📉 技术看跌"
        else:
            direction = "sideways"
            label = "➡️ 技术震荡"
        
        return {
            "direction": direction,
            "label": label,
            "confidence": float(confidence),
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals
        }
    
    @staticmethod
    def _predict_ml(df: pd.DataFrame) -> Dict[str, Any]:
        """机器学习预测（模拟）"""
        
        # 模拟机器学习预测
        features = {
            "trend_strength": float(df['trend_strength'].iloc[-1]),
            "volatility": float(df['volatility'].iloc[-1]),
            "rsi": float(df['rsi'].iloc[-1]),
            "macd_hist": float(df['macd_hist'].iloc[-1]),
            "bb_width": float(df['bb_width'].iloc[-1])
        }
        
        # 模拟模型输出
        np.random.seed(int(datetime.now().timestamp()) % 10000)
        up_prob = 0.3 + features['trend_strength'] * 2 + (50 - features['rsi']) / 100
        up_prob = max(0.1, min(0.9, up_prob + np.random.normal(0, 0.1)))
        down_prob = 1 - up_prob
        
        if up_prob > 0.6:
            direction = "up"
            label = "🤖 ML 看涨"
        elif down_prob > 0.6:
            direction = "down"
            label = "🤖 ML 看跌"
        else:
            direction = "sideways"
            label = "🤖 ML 震荡"
        
        return {
            "direction": direction,
            "label": label,
            "confidence": float(max(up_prob, down_prob)),
            "probabilities": {
                "up": float(up_prob),
                "down": float(down_prob)
            },
            "features": features
        }
    
    @staticmethod
    def _predict_pattern(df: pd.DataFrame) -> Dict[str, Any]:
        """形态识别预测"""
        
        patterns = []
        
        # 检查常见形态（简化）
        current = df['close'].iloc[-1]
        recent = df.tail(20)
        
        # 双顶/双底
        highs = recent['high'].nlargest(2)
        lows = recent['low'].nsmallest(2)
        
        if len(highs) == 2 and abs(highs.iloc[0] - highs.iloc[1]) / highs.iloc[0] < 0.02:
            patterns.append({
                "pattern": "double_top",
                "label": "双顶形态",
                "bias": "bearish",
                "confidence": 0.7
            })
        
        if len(lows) == 2 and abs(lows.iloc[0] - lows.iloc[1]) / lows.iloc[0] < 0.02:
            patterns.append({
                "pattern": "double_bottom",
                "label": "双底形态",
                "bias": "bullish",
                "confidence": 0.7
            })
        
        # 头肩形态（简化）
        if len(recent) >= 15:
            mid_high = recent['high'].iloc[7:10].max()
            left_high = recent['high'].iloc[0:7].max()
            right_high = recent['high'].iloc[10:15].max()
            
            if mid_high > left_high and mid_high > right_high and abs(left_high - right_high) / left_high < 0.03:
                patterns.append({
                    "pattern": "head_shoulders",
                    "label": "头肩顶形态",
                    "bias": "bearish",
                    "confidence": 0.8
                })
        
        # 综合判断
        bullish_patterns = [p for p in patterns if p['bias'] == 'bullish']
        bearish_patterns = [p for p in patterns if p['bias'] == 'bearish']
        
        if bullish_patterns and not bearish_patterns:
            direction = "up"
            label = "📊 形态看涨"
            confidence = max(p['confidence'] for p in bullish_patterns)
        elif bearish_patterns and not bullish_patterns:
            direction = "down"
            label = "📊 形态看跌"
            confidence = max(p['confidence'] for p in bearish_patterns)
        else:
            direction = "sideways"
            label = "📊 形态中性"
            confidence = 0.5
        
        return {
            "direction": direction,
            "label": label,
            "confidence": float(confidence),
            "patterns": patterns
        }
    
    @staticmethod
    def _predict_sentiment(df: pd.DataFrame) -> Dict[str, Any]:
        """市场情绪预测"""
        
        # 模拟市场情绪
        volatility = df['volatility'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        
        # 情绪指数
        sentiment_score = (50 - rsi) / 50 + (0.5 - volatility * 2)
        sentiment_score = max(-1, min(1, sentiment_score))
        
        if sentiment_score > 0.3:
            direction = "up"
            label = "😊 情绪看涨"
        elif sentiment_score < -0.3:
            direction = "down"
            label = "😰 情绪看跌"
        else:
            direction = "sideways"
            label = "😐 情绪中性"
        
        # 恐惧贪婪指数
        fear_greed = 50 + sentiment_score * 30
        fear_greed = max(0, min(100, fear_greed))
        
        return {
            "direction": direction,
            "label": label,
            "confidence": float(abs(sentiment_score)),
            "sentiment_score": float(sentiment_score),
            "fear_greed": float(fear_greed)
        }
    
    @staticmethod
    def _synthesize_predictions(predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """综合各模型预测"""
        
        # 权重
        weights = {
            "technical": 0.35,
            "machine_learning": 0.30,
            "pattern": 0.20,
            "sentiment": 0.15
        }
        
        # 计分
        up_score = 0.0
        down_score = 0.0
        
        for model, pred in predictions.items():
            weight = weights.get(model, 0.2)
            confidence = pred["confidence"]
            
            if pred["direction"] == "up":
                up_score += confidence * weight
            elif pred["direction"] == "down":
                down_score += confidence * weight
        
        total = up_score + down_score
        if total > 0:
            up_score /= total
            down_score /= total
        
        # 综合判断
        if up_score > down_score * 1.2:
            direction = "up"
            label = "🚀 综合看涨"
        elif down_score > up_score * 1.2:
            direction = "down"
            label = "🔻 综合看跌"
        else:
            direction = "sideways"
            label = "➡️ 综合震荡"
        
        # 一致性检查
        directions = [pred["direction"] for pred in predictions.values()]
        consistency = len(set(directions)) == 1
        
        return {
            "direction": direction,
            "label": label,
            "confidence": float(max(up_score, down_score)),
            "consistency": consistency,
            "model_votes": {model: pred["label"] for model, pred in predictions.items()},
            "score_breakdown": {
                "up": float(up_score),
                "down": float(down_score)
            }
        }
    
    @staticmethod
    def _predict_price_levels(df: pd.DataFrame, overall: Dict[str, Any]) -> Dict[str, Any]:
        """预测价格水平"""
        
        current = df['close'].iloc[-1]
        volatility = df['volatility'].iloc[-1]
        
        # 基于波动率的价格预测
        if overall["direction"] == "up":
            target_multiplier = 1 + volatility * 0.5
            stop_multiplier = 1 - volatility * 0.3
        elif overall["direction"] == "down":
            target_multiplier = 1 - volatility * 0.5
            stop_multiplier = 1 + volatility * 0.3
        else:
            target_multiplier = 1 + volatility * 0.2
            stop_multiplier = 1 - volatility * 0.2
        
        # 支撑阻力位
        recent = df.tail(50)
        support = recent['low'].min()
        resistance = recent['high'].max()
        
        return {
            "current_price": float(current),
            "target_price": float(current * target_multiplier),
            "stop_loss": float(current * stop_multiplier),
            "support": float(support),
            "resistance": float(resistance),
            "risk_reward_ratio": float(abs(target_multiplier - 1) / abs(stop_multiplier - 1))
        }
    
    @staticmethod
    def _assess_risk(df: pd.DataFrame, overall: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        
        volatility = df['volatility'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        
        # 风险评分
        risk_score = 0.0
        
        # 波动率风险
        if volatility > 0.05:
            risk_score += 0.3
        elif volatility > 0.03:
            risk_score += 0.2
        
        # RSI 极端风险
        if rsi > 80 or rsi < 20:
            risk_score += 0.3
        elif rsi > 70 or rsi < 30:
            risk_score += 0.15
        
        # 趋势一致性风险
        if not overall.get("consistency", False):
            risk_score += 0.2
        
        risk_score = min(1.0, risk_score)
        
        # 风险等级
        if risk_score < 0.3:
            level = "low"
            label = "🟢 低风险"
        elif risk_score < 0.6:
            level = "medium"
            label = "🟡 中风险"
        else:
            level = "high"
            label = "🔴 高风险"
        
        return {
            "risk_score": float(risk_score),
            "risk_level": level,
            "risk_label": label,
            "volatility": float(volatility),
            "rsi": float(rsi),
            "suggestion": "建议轻仓操作，设置止损" if risk_score > 0.5 else "风险可控，可适度参与"
        }
