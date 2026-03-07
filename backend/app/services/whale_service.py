import pandas as pd
import numpy as np
from typing import Dict, Any, List


class WhaleAnalysisService:
    """庄家分析服务 - 基础版"""
    
    @staticmethod
    def detect_large_orders(df: pd.DataFrame, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """检测大单"""
        if 'volume' not in df.columns:
            return []
        
        avg_volume = df['volume'].mean()
        threshold = avg_volume * threshold_multiplier
        
        large_orders = []
        for idx, row in df.iterrows():
            if pd.notna(row['volume']) and row['volume'] > threshold:
                large_orders.append({
                    'timestamp': int(idx.timestamp() * 1000) if hasattr(idx, 'timestamp') else int(idx),
                    'volume': float(row['volume']),
                    'price': float(row['close']) if pd.notna(row.get('close')) else None,
                    'is_buy': WhaleAnalysisService._is_buy_order(row)
                })
        
        return large_orders
    
    @staticmethod
    def _is_buy_order(row: pd.Series) -> bool:
        """简单判断是否为买单（基于价格变化）"""
        if pd.notna(row.get('open')) and pd.notna(row.get('close')):
            return row['close'] >= row['open']
        return True
    
    @staticmethod
    def analyze_money_flow(df: pd.DataFrame) -> Dict[str, Any]:
        """资金流向分析"""
        result = {
            'periods': {}
        }
        
        # 计算不同周期的资金流向
        for period in [5, 10, 20, 60]:
            if len(df) < period:
                continue
            
            recent = df.tail(period)
            
            # 简单资金流向计算
            price_changes = recent['close'].pct_change().dropna()
            volumes = recent['volume'].dropna()
            
            if len(price_changes) > 0 and len(volumes) > 0:
                # 价格上涨时的成交量为流入，下跌时为流出
                inflow = 0.0
                outflow = 0.0
                
                for i in range(min(len(price_changes), len(volumes))):
                    if i < len(price_changes) and i < len(volumes):
                        change = price_changes.iloc[i]
                        vol = volumes.iloc[i]
                        
                        if pd.notna(change) and pd.notna(vol):
                            if change > 0:
                                inflow += float(vol)
                            elif change < 0:
                                outflow += float(vol)
                
                net_flow = inflow - outflow
                
                result['periods'][f'{period}'] = {
                    'inflow': float(inflow),
                    'outflow': float(outflow),
                    'net_flow': float(net_flow),
                    'inflow_ratio': float(inflow / (inflow + outflow)) if (inflow + outflow) > 0 else 0.5
                }
        
        # 总体趋势
        latest_flow = result['periods'].get('5', {})
        if latest_flow:
            if latest_flow.get('net_flow', 0) > 0:
                result['overall'] = 'inflow'
            elif latest_flow.get('net_flow', 0) < 0:
                result['overall'] = 'outflow'
            else:
                result['overall'] = 'neutral'
        
        return result
    
    @staticmethod
    def detect_phase(df: pd.DataFrame) -> Dict[str, Any]:
        """检测当前市场阶段（吸-洗-拉-出）- 基础版"""
        if len(df) < 20:
            return {'phase': 'unknown', 'confidence': 0.0}
        
        recent = df.tail(20)
        latest = df.iloc[-1]
        
        # 计算基础指标
        price_change_20 = (latest['close'] - df['close'].iloc[-20]) / df['close'].iloc[-20] if len(df) > 20 else 0
        volume_avg_5 = recent['volume'].tail(5).mean()
        volume_avg_20 = recent['volume'].mean()
        volume_ratio = volume_avg_5 / volume_avg_20 if volume_avg_20 > 0 else 1
        
        volatility = recent['close'].pct_change().std()
        
        # 简单规则判断阶段
        phase = 'unknown'
        confidence = 0.3
        signals = []
        
        # 拉升阶段：价格快速上涨 + 成交量放大
        if price_change_20 > 0.05 and volume_ratio > 1.2:
            phase = 'pump'
            confidence = 0.7
            signals.append('快速上涨')
            signals.append('成交量放大')
        
        # 出货阶段：高位震荡 + 放量滞涨
        elif price_change_20 > 0 and price_change_20 < 0.05 and volume_ratio > 1.5:
            phase = 'distribution'
            confidence = 0.6
            signals.append('高位震荡')
            signals.append('放量滞涨')
        
        # 吸筹阶段：低位横盘 + 温和放量
        elif price_change_20 < 0.02 and price_change_20 > -0.02 and volume_ratio > 1.1:
            phase = 'accumulation'
            confidence = 0.5
            signals.append('低位横盘')
            signals.append('温和放量')
        
        # 洗盘阶段：快速下跌 + 高波动
        elif volatility > 0.03 and price_change_20 < -0.03:
            phase = 'washout'
            confidence = 0.55
            signals.append('快速下跌')
            signals.append('高波动率')
        
        return {
            'phase': phase,
            'confidence': confidence,
            'signals': signals,
            'indicators': {
                'price_change_20': float(price_change_20),
                'volume_ratio': float(volume_ratio),
                'volatility': float(volatility)
            }
        }
    
    @staticmethod
    def analyze(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """综合庄家分析"""
        df = df.copy()
        
        # 确保有时间索引
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
        
        large_orders = WhaleAnalysisService.detect_large_orders(df)
        money_flow = WhaleAnalysisService.analyze_money_flow(df)
        phase = WhaleAnalysisService.detect_phase(df)
        
        return {
            'symbol': symbol,
            'large_orders': large_orders[-10:],  # 最近10个大单
            'large_orders_count': len(large_orders),
            'money_flow': money_flow,
            'phase': phase,
            'timestamp': int(pd.Timestamp.now().timestamp() * 1000)
        }
