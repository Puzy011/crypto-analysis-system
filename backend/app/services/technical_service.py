import pandas as pd
import numpy as np
from typing import Dict, Any, List


class TechnicalIndicatorsService:
    """技术指标计算服务"""
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """计算所有技术指标"""
        result = {}
        
        # 确保数据按时间排序
        df = df.sort_index()
        
        # 计算移动平均线
        result['ma'] = TechnicalIndicatorsService.calculate_ma(df)
        
        # 计算 MACD
        result['macd'] = TechnicalIndicatorsService.calculate_macd(df)
        
        # 计算 RSI
        result['rsi'] = TechnicalIndicatorsService.calculate_rsi(df)
        
        # 计算布林带
        result['boll'] = TechnicalIndicatorsService.calculate_bollinger_bands(df)
        
        # 计算 KDJ
        result['kdj'] = TechnicalIndicatorsService.calculate_kdj(df)
        
        return result
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: List[int] = None) -> Dict[str, List[float]]:
        """计算移动平均线 MA"""
        if periods is None:
            periods = [5, 10, 20, 60]
        
        close_prices = df['close'].values
        result = {}
        
        for period in periods:
            ma = []
            for i in range(len(close_prices)):
                if i < period - 1:
                    ma.append(None)
                else:
                    ma.append(float(np.mean(close_prices[i-period+1:i+1])))
            result[f'MA{period}'] = ma
        
        return result
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """计算 MACD"""
        close_prices = df['close'].values
        
        # 计算 EMA
        def ema(data, period):
            ema_values = []
            multiplier = 2 / (period + 1)
            ema_values.append(float(data[0]))
            for i in range(1, len(data)):
                ema_val = float(data[i] * multiplier + ema_values[i-1] * (1 - multiplier))
                ema_values.append(ema_val)
            return ema_values
        
        ema_fast = ema(close_prices, fast)
        ema_slow = ema(close_prices, slow)
        
        # 计算 DIF (MACD line)
        dif = []
        for i in range(len(ema_fast)):
            dif.append(float(ema_fast[i] - ema_slow[i]))
        
        # 计算 DEA (Signal line)
        dea = ema(np.array(dif), signal)
        
        # 计算 MACD 柱状图
        macd_hist = []
        for i in range(len(dif)):
            macd_hist.append(float((dif[i] - dea[i]) * 2))
        
        return {
            'DIF': dif,
            'DEA': dea,
            'MACD': macd_hist
        }
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Dict[str, List[float]]:
        """计算 RSI"""
        close_prices = df['close'].values
        
        # 计算价格变化
        deltas = np.diff(close_prices)
        gains = []
        losses = []
        
        for delta in deltas:
            if delta > 0:
                gains.append(float(delta))
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(float(-delta))
        
        # 计算初始平均
        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))
        
        rsi_values = [None] * (period + 1)
        
        # 计算 RSI
        for i in range(period, len(gains)):
            if i > period:
                avg_gain = float((avg_gain * (period - 1) + gains[i]) / period)
                avg_loss = float((avg_loss * (period - 1) + losses[i]) / period)
            
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = float(100.0 - (100.0 / (1.0 + rs)))
            
            rsi_values.append(rsi)
        
        return {'RSI': rsi_values}
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, List[float]]:
        """计算布林带"""
        close_prices = df['close'].values
        
        middle_band = []
        upper_band = []
        lower_band = []
        
        for i in range(len(close_prices)):
            if i < period - 1:
                middle_band.append(None)
                upper_band.append(None)
                lower_band.append(None)
            else:
                window = close_prices[i-period+1:i+1]
                middle = float(np.mean(window))
                std = float(np.std(window))
                
                middle_band.append(middle)
                upper_band.append(middle + std_dev * std)
                lower_band.append(middle - std_dev * std)
        
        return {
            'BOLL_MID': middle_band,
            'BOLL_UP': upper_band,
            'BOLL_LOW': lower_band
        }
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, List[float]]:
        """计算 KDJ"""
        high_prices = df['high'].values
        low_prices = df['low'].values
        close_prices = df['close'].values
        
        # 计算 RSV
        rsv = []
        for i in range(len(close_prices)):
            if i < n - 1:
                rsv.append(None)
            else:
                high_n = max(high_prices[i-n+1:i+1])
                low_n = min(low_prices[i-n+1:i+1])
                if high_n == low_n:
                    rsv_val = 50.0
                else:
                    rsv_val = float((close_prices[i] - low_n) / (high_n - low_n) * 100)
                rsv.append(rsv_val)
        
        # 计算 K 值
        k_values = []
        prev_k = 50.0
        for val in rsv:
            if val is None:
                k_values.append(None)
            else:
                if k_values and k_values[-1] is not None:
                    prev_k = k_values[-1]
                k = float((prev_k * (m1 - 1) + val) / m1)
                k_values.append(k)
        
        # 计算 D 值
        d_values = []
        prev_d = 50.0
        for val in k_values:
            if val is None:
                d_values.append(None)
            else:
                if d_values and d_values[-1] is not None:
                    prev_d = d_values[-1]
                d = float((prev_d * (m2 - 1) + val) / m2)
                d_values.append(d)
        
        # 计算 J 值
        j_values = []
        for k, d in zip(k_values, d_values):
            if k is None or d is None:
                j_values.append(None)
            else:
                j = float(3 * k - 2 * d)
                j_values.append(j)
        
        return {
            'K': k_values,
            'D': d_values,
            'J': j_values
        }
