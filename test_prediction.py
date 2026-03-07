#!/usr/bin/env python3
"""
测试任意币种预测 - 使用 OKX
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from app.services.okx_service import OKXService
from app.services.prediction_service import PredictionService
import pandas as pd


async def main():
    # RIVER/USDT 在 OKX 上的交易对
    symbol = "RIVER-USDT-SWAP"  # OKX 合约格式
    
    print(f"🔮 开始测试 {symbol} 预测 (OKX)...")
    print()
    
    okx_service = OKXService()
    prediction_service = PredictionService()
    
    try:
        # 获取 K线数据
        print(f"📊 获取 {symbol} K线数据 (OKX)...")
        klines = await okx_service.get_klines(symbol, "1H", 200)
        print(f"✅ 获取到 {len(klines)} 条 K线数据")
        print()
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 进行趋势预测
        print("🤖 进行趋势预测...")
        prediction = prediction_service.predict_basic_trend(df)
        print()
        
        print("=" * 60)
        print(f"📈 {symbol} 趋势预测结果 (OKX)")
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
        print("⚠️  免责声明: 本预测仅供参考，不构成投资建议！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        print("💡 提示:")
        print("  - 如果 RIVER-USDT-SWAP 不对")
        print("  - 请告诉我 RIVER 在 OKX 上的正确交易对代码")
        print("  - 或者换成其他币种测试")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
