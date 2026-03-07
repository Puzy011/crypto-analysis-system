import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple


class PredictionService:
    """AI 预测服务 - 基础版"""
    
    @staticmethod
    def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
        """准备特征"""
        df = df.copy()
        
        # 价格特征
        df['price_change'] = df['close'].pct_change()
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        
        # 简单移动平均
        for period in [5, 10, 20, 60]:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        
        # 波动率
        df['volatility'] = df['price_change'].rolling(window=20).std()
        
        # RSI (简单版)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD (简单版)
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 成交量特征
        df['volume_change'] = df['volume'].pct_change()
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        
        return df
    
    @staticmethod
    def predict_basic_trend(df: pd.DataFrame) -> Dict[str, Any]:
        """基础趋势预测 - 基于技术指标"""
        df = PredictionService.prepare_features(df)
        
        latest = df.iloc[-1]
        
        # 简单规则预测
        signals = []
        confidence = 0.0
        
        # MA 信号
        if pd.notna(latest.get('MA5')) and pd.notna(latest.get('MA20')):
            if latest['MA5'] > latest['MA20']:
                signals.append('bullish')
                confidence += 0.2
            elif latest['MA5'] < latest['MA20']:
                signals.append('bearish')
                confidence += 0.2
        
        # RSI 信号
        if pd.notna(latest.get('RSI')):
            if latest['RSI'] < 30:
                signals.append('bullish')  # 超卖，可能反弹
                confidence += 0.3
            elif latest['RSI'] > 70:
                signals.append('bearish')  # 超买，可能回调
                confidence += 0.3
        
        # MACD 信号
        if pd.notna(latest.get('MACD')) and pd.notna(latest.get('Signal')):
            if latest['MACD'] > latest['Signal']:
                signals.append('bullish')
                confidence += 0.25
            elif latest['MACD'] < latest['Signal']:
                signals.append('bearish')
                confidence += 0.25
        
        # 综合判断
        bullish_count = signals.count('bullish')
        bearish_count = signals.count('bearish')
        
        if bullish_count > bearish_count:
            prediction = 'up'
            trend_strength = min(confidence, 0.9)
        elif bearish_count > bullish_count:
            prediction = 'down'
            trend_strength = min(confidence, 0.9)
        else:
            prediction = 'sideways'
            trend_strength = 0.5
        
        # 支撑阻力位（简单版）
        recent = df.tail(20)
        support = recent['low'].min()
        resistance = recent['high'].max()
        
        return {
            'prediction': prediction,
            'confidence': trend_strength,
            'signals': {
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'total_signals': len(signals)
            },
            'levels': {
                'support': float(support) if pd.notna(support) else None,
                'resistance': float(resistance) if pd.notna(resistance) else None
            },
            'current_price': float(latest['close']),
            'model': 'rule_based_v1',
            'timestamp': int(pd.Timestamp.now().timestamp() * 1000)
        }
    
    @staticmethod
    def predict_price_range(df: pd.DataFrame, horizon: int = 24) -> Dict[str, Any]:
        """预测价格区间"""
        latest_close = df['close'].iloc[-1]
        
        # 基于历史波动率的简单区间预测
        returns = df['close'].pct_change().dropna()
        volatility = returns.std()
        
        # 简单的正态分布假设
        z_score = 1.96  # 95% 置信区间
        
        lower_bound = latest_close * (1 - z_score * volatility * np.sqrt(horizon/24))
        upper_bound = latest_close * (1 + z_score * volatility * np.sqrt(horizon/24))
        
        return {
            'horizon_hours': horizon,
            'current_price': float(latest_close),
            'lower_bound': float(max(lower_bound, 0)),
            'upper_bound': float(upper_bound),
            'volatility': float(volatility),
            'confidence_level': '95%'
        }
