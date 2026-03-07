#!/usr/bin/env python3
"""
测试 RIVER 预测 - 简化版（不依赖外部 API）
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.prediction_service import PredictionService
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_mock_klines(symbol: str, count: int = 200):
    """生成模拟 K线数据"""
    np.random.seed(42)  # 固定随机种子
    
    # 基础价格
    base_price = 0.5 if symbol.upper().startswith("RIVER") else 50000
    
    # 生成价格序列
    prices = [base_price]
    for i in range(1, count):
        # 随机波动
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # 生成 K线数据
    klines = []
    now = datetime.now()
    
    for i in range(count):
        timestamp = int((now - timedelta(hours=count-i)).timestamp() * 1000)
        
        # OHLC 数据
        open_p = prices[i]
        close_p = prices[i]
        high_p = prices[i] * (1 + abs(np.random.normal(0, 0.01)))
        low_p = prices[i] * (1 - abs(np.random.normal(0, 0.01)))
        volume = np.random.uniform(10000, 100000)
        
        klines.append({
            "timestamp": timestamp,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
            "closeTime": timestamp,
            "quoteVolume": volume * close_p,
            "trades": int(np.random.randint(100, 1000)),
            "takerBuyBase": volume * 0.5,
            "takerBuyQuote": volume * close_p * 0.5
        })
    
    return klines


def main():
    print("🔮 开始测试 RIVER 预测 (使用模拟数据)...")
    print()
    
    symbol = "RIVERUSDT"
    
    # 生成模拟 K线数据
    print(f"📊 生成 {symbol} 模拟 K线数据...")
    klines = generate_mock_klines(symbol, 200)
    print(f"✅ 生成 {len(klines)} 条 K线数据")
    print()
    
    # 转换为 DataFrame
    df = pd.DataFrame(klines)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # 进行趋势预测
    print("🤖 进行趋势预测...")
    prediction_service = PredictionService()
    prediction = prediction_service.predict_basic_trend(df)
    print()
    
    print("=" * 60)
    print(f"📈 {symbol} 趋势预测结果 (模拟数据)")
    print("=" * 60)
    print()
    
    # 预测方向
    trend_text = {
        'up': '📈 看涨',
        'down': '📉 看跌',
        'sideways': '➡️ 震荡'
    }
    print(f"预测方向: {trend_text.get(prediction['prediction'], prediction['prediction'])}")
    print(f"预测置信度: {prediction['confidence'] * 100:.1f}%")
    print()
    
    # 信号统计
    print("📊 信号统计:")
    print(f"  - 看涨信号: {prediction['signals']['bullish_count']} 个")
    print(f"  - 看跌信号: {prediction['signals']['bearish_count']} 个")
    print(f"  - 总信号数: {prediction['signals']['total_signals']} 个")
    print()
    
    # 支撑阻力位
    print("💰 关键价位:")
    print(f"  - 当前价格: ${prediction['current_price']:.6f}")
    if prediction['levels']['support']:
        print(f"  - 支撑位: ${prediction['levels']['support']:.6f}")
    if prediction['levels']['resistance']:
        print(f"  - 阻力位: ${prediction['levels']['resistance']:.6f}")
    print()
    
    # 价格区间预测
    print("📊 价格区间预测 (24小时, 95%置信度):")
    range_pred = prediction_service.predict_price_range(df, 24)
    print(f"  - 当前价格: ${range_pred['current_price']:.6f}")
    print(f"  - 预测下限: ${range_pred['lower_bound']:.6f}")
    print(f"  - 预测上限: ${range_pred['upper_bound']:.6f}")
    print(f"  - 历史波动率: {range_pred['volatility'] * 100:.2f}%")
    print()
    
    print("=" * 60)
    print("⚠️  说明: 使用模拟数据演示，非实时数据")
    print("⚠️  免责声明: 本预测仅供参考，不构成投资建议！")
    print("=" * 60)


if __name__ == "__main__":
    main()
