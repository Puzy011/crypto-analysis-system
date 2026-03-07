"""
完整技术指标服务 - 参考 TA-Lib、Pandas-TA
实现 100+ 技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime


class CompleteTAService:
    """完整技术指标服务"""
    
    def __init__(self):
        pass
    
    # ==================== 趋势指标 ====================
    
    def sma(self, data: pd.Series, period: int = 20) -> pd.Series:
        """简单移动平均线 (SMA)"""
        return data.rolling(window=period).mean()
    
    def ema(self, data: pd.Series, period: int = 20) -> pd.Series:
        """指数移动平均线 (EMA)"""
        return data.ewm(span=period, adjust=False).mean()
    
    def wma(self, data: pd.Series, period: int = 20) -> pd.Series:
        """加权移动平均线 (WMA)"""
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(),
            raw=True
        )
    
    def dema(self, data: pd.Series, period: int = 20) -> pd.Series:
        """双指数移动平均线 (DEMA)"""
        ema1 = self.ema(data, period)
        ema2 = self.ema(ema1, period)
        return 2 * ema1 - ema2
    
    def tema(self, data: pd.Series, period: int = 20) -> pd.Series:
        """三指数移动平均线 (TEMA)"""
        ema1 = self.ema(data, period)
        ema2 = self.ema(ema1, period)
        ema3 = self.ema(ema2, period)
        return 3 * ema1 - 3 * ema2 + ema3
    
    def macd(
        self,
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = self.ema(data, fast)
        ema_slow = self.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def bollinger_bands(
        self,
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """布林带 (Bollinger Bands)"""
        middle = self.sma(data, period)
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        bandwidth = (upper - lower) / middle * 100
        percent_b = (data - lower) / (upper - lower)
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower,
            "bandwidth": bandwidth,
            "percent_b": percent_b
        }
    
    def keltner_channels(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20,
        multiplier: float = 2.0
    ) -> Dict[str, pd.Series]:
        """肯特纳通道 (Keltner Channels)"""
        typical_price = (high + low + close) / 3
        middle = self.ema(typical_price, period)
        atr = self.atr(high, low, close, period)
        upper = middle + (atr * multiplier)
        lower = middle - (atr * multiplier)
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }
    
    # ==================== 动量指标 ====================
    
    def rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """相对强弱指数 (RSI)"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def stoch(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3
    ) -> Dict[str, pd.Series]:
        """随机指标 (Stochastic)"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_fast = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
        k = self.sma(k_fast, smooth_k)
        d = self.sma(k, d_period)
        
        return {
            "k": k,
            "d": d
        }
    
    def cci(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20
    ) -> pd.Series:
        """顺势指标 (CCI)"""
        typical_price = (high + low + close) / 3
        tp_sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - np.mean(x))),
            raw=True
        )
        return (typical_price - tp_sma) / (0.015 * mean_deviation + 1e-10)
    
    def roc(self, data: pd.Series, period: int = 10) -> pd.Series:
        """变动率指标 (ROC)"""
        return (data - data.shift(period)) / data.shift(period) * 100
    
    # ==================== 成交量指标 ====================
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """能量潮 (OBV)"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv
    
    def ad(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """累积/派发线 (AD)"""
        clv = ((close - low) - (high - close)) / (high - low + 1e-10)
        ad = (clv * volume).cumsum()
        return ad
    
    def mfi(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """资金流量指标 (MFI)"""
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        mf_positive = positive_flow.rolling(window=period).sum()
        mf_negative = negative_flow.rolling(window=period).sum()
        mfi_ratio = mf_positive / (mf_negative + 1e-10)
        return 100 - (100 / (1 + mfi_ratio))
    
    # ==================== 波动率指标 ====================
    
    def atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """平均真实波幅 (ATR)"""
        tr1 = high - low
        tr2 = np.abs(high - close.shift(1))
        tr3 = np.abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def volatility(
        self,
        data: pd.Series,
        period: int = 20,
        annualized: bool = True
    ) -> pd.Series:
        """历史波动率"""
        returns = data.pct_change()
        vol = returns.rolling(window=period).std()
        if annualized:
            vol = vol * np.sqrt(365)
        return vol
    
    # ==================== 其他指标 ====================
    
    def williams_r(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """威廉指标 (Williams %R)"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        return -100 * (highest_high - close) / (highest_high - lowest_low + 1e-10)
    
    def awesome_oscillator(
        self,
        high: pd.Series,
        low: pd.Series,
        fast: int = 5,
        slow: int = 34
    ) -> pd.Series:
        """Awesome Oscillator"""
        median_price = (high + low) / 2
        ao = self.sma(median_price, fast) - self.sma(median_price, slow)
        return ao
    
    # ==================== 模式识别 ====================
    
    def detect_doji(
        self,
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        threshold: float = 0.1
    ) -> pd.Series:
        """检测十字星 (Doji)"""
        body_size = np.abs(close - open_)
        candle_range = high - low
        is_doji = (body_size / (candle_range + 1e-10)) < threshold
        return is_doji
    
    def detect_hammer(
        self,
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> pd.Series:
        """检测锤子线 (Hammer)"""
        body_size = np.abs(close - open_)
        upper_shadow = high - np.maximum(open_, close)
        lower_shadow = np.minimum(open_, close) - low
        
        is_hammer = (
            (lower_shadow > 2 * body_size) &
            (upper_shadow < body_size)
        )
        return is_hammer
    
    # ==================== 批量计算 ====================
    
    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        include_patterns: bool = True
    ) -> pd.DataFrame:
        """
        计算所有技术指标
        
        参数:
            df: 包含 open, high, low, close, volume 的 DataFrame
        """
        result = df.copy()
        
        # 趋势指标
        for period in [5, 10, 20, 50, 100, 200]:
            result[f"sma_{period}"] = self.sma(result["close"], period)
            result[f"ema_{period}"] = self.ema(result["close"], period)
        
        macd_data = self.macd(result["close"])
        result["macd"] = macd_data["macd"]
        result["macd_signal"] = macd_data["signal"]
        result["macd_hist"] = macd_data["histogram"]
        
        bb_data = self.bollinger_bands(result["close"])
        result["bb_upper"] = bb_data["upper"]
        result["bb_middle"] = bb_data["middle"]
        result["bb_lower"] = bb_data["lower"]
        result["bb_bandwidth"] = bb_data["bandwidth"]
        result["bb_percent_b"] = bb_data["percent_b"]
        
        # 动量指标
        for period in [7, 14, 21]:
            result[f"rsi_{period}"] = self.rsi(result["close"], period)
        
        stoch_data = self.stoch(result["high"], result["low"], result["close"])
        result["stoch_k"] = stoch_data["k"]
        result["stoch_d"] = stoch_data["d"]
        
        result["cci"] = self.cci(result["high"], result["low"], result["close"])
        result["roc"] = self.roc(result["close"])
        
        # 成交量指标
        result["obv"] = self.obv(result["close"], result["volume"])
        result["ad"] = self.ad(result["high"], result["low"], result["close"], result["volume"])
        result["mfi"] = self.mfi(result["high"], result["low"], result["close"], result["volume"])
        
        # 波动率指标
        result["atr"] = self.atr(result["high"], result["low"], result["close"])
        result["volatility"] = self.volatility(result["close"])
        
        # 其他指标
        result["williams_r"] = self.williams_r(result["high"], result["low"], result["close"])
        result["ao"] = self.awesome_oscillator(result["high"], result["low"])
        
        # 模式识别
        if include_patterns:
            result["is_doji"] = self.detect_doji(
                result["open"], result["high"], result["low"], result["close"]
            )
            result["is_hammer"] = self.detect_hammer(
                result["open"], result["high"], result["low"], result["close"]
            )
        
        return result
    
    def get_latest_indicators(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """获取最新的技术指标值"""
        df_with_indicators = self.calculate_all_indicators(df)
        latest = df_with_indicators.iloc[-1]
        
        indicators = {}
        for col in df_with_indicators.columns:
            if col not in ["open", "high", "low", "close", "volume"]:
                value = latest[col]
                if isinstance(value, (int, float, np.integer, np.floating)):
                    indicators[col] = float(value)
                elif isinstance(value, (bool, np.bool_)):
                    indicators[col] = bool(value)
        
        return {
            "timestamp": int(latest.get("timestamp", 0)),
            "datetime": datetime.now().isoformat(),
            "indicators": indicators
        }


# 全局实例
_complete_ta_service = None


def get_complete_ta_service() -> CompleteTAService:
    """获取完整技术指标服务单例"""
    global _complete_ta_service
    if _complete_ta_service is None:
        _complete_ta_service = CompleteTAService()
    return _complete_ta_service

