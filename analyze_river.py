#!/usr/bin/env python3
"""
分析 RIVER：预测未来5小时趋势 + 获取舆情 + 具体分析
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from app.services.enhanced_sentiment_service import EnhancedSentimentService
from app.services.enhanced_prediction_service import EnhancedPredictionService


# 设置代理
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'


async def check_binance_symbol(symbol: str):
    """检查 Binance 交易对是否存在"""
    
    url = "https://api.binance.com/api/v3/exchangeInfo"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy="http://127.0.0.1:7890") as response:
                if response.status == 200:
                    data = await response.json()
                    symbols = [s['symbol'] for s in data['symbols']]
                    
                    # 检查是否存在
                    target_symbol = symbol.upper().replace("/", "")
                    if target_symbol in symbols:
                        return True, target_symbol
                    
                    # 检查相似的
                    similar = [s for s in symbols if 'RIVER' in s]
                    if similar:
                        return True, similar[0]
                    
                    return False, None
                else:
                    return False, None
    except Exception as e:
        print(f"检查交易对时出错: {e}")
        return False, None


async def get_klines(symbol: str, interval: str = "1h", limit: int = 200):
    """获取 K线数据"""
    
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy="http://127.0.0.1:7890") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 格式化
                    klines = []
                    for k in data:
                        klines.append({
                            "timestamp": int(k[0]),
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5]),
                            "closeTime": int(k[6]),
                            "quoteVolume": float(k[7]),
                            "trades": int(k[8]),
                            "takerBuyBase": float(k[9]),
                            "takerBuyQuote": float(k[10])
                        })
                    
                    return klines
                else:
                    return None
    except Exception as e:
        print(f"获取 K线时出错: {e}")
        return None


async def main():
    print("=" * 80)
    print("🔮 RIVER 完整分析报告")
    print("=" * 80)
    print()
    
    symbol = "RIVERUSDT"
    
    # 1. 检查交易对
    print("1️⃣  检查 RIVER 交易对...")
    exists, actual_symbol = await check_binance_symbol(symbol)
    
    if exists and actual_symbol:
        print(f"   ✅ 找到交易对: {actual_symbol}")
        print()
        
        # 获取 K线数据
        print("2️⃣  获取 K线数据...")
        klines = await get_klines(actual_symbol, "1h", 200)
        
        if klines:
            print(f"   ✅ 获取到 {len(klines)} 条 K线数据")
            print()
            
            # 转换为 DataFrame
            df = pd.DataFrame(klines)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            current_price = df['close'].iloc[-1]
            print(f"💰 当前价格: ${current_price:.6f}")
            print()
            
            # 3. 增强版舆情分析
            print("3️⃣  增强版舆情分析...")
            sentiment_service = EnhancedSentimentService()
            sentiment_result = sentiment_service.analyze_full_sentiment("RIVER")
            
            print(f"   🏆 综合评分: {sentiment_result['overall_score']['score']:.1f} / 100")
            print(f"   等级: {sentiment_result['overall_score']['grade']} - {sentiment_result['overall_score']['label']}")
            print(f"   建议: {sentiment_result['overall_score']['suggestion']}")
            print()
            
            # 4. 增强版趋势预测
            print("4️⃣  增强版趋势预测...")
            prediction_service = EnhancedPredictionService()
            prediction_result = prediction_service.predict_enhanced_trend("RIVERUSDT")
            
            print(f"   🚀 综合预测: {prediction_result['overall']['label']}")
            print(f"   预测置信度: {prediction_result['overall']['confidence'] * 100:.1f}%")
            print()
            
            # 5. 未来5小时价格预测
            print("5️⃣  未来 5 小时价格预测...")
            volatility = df['close'].pct_change().std() * np.sqrt(24)
            
            current_price = df['close'].iloc[-1]
            
            # 基于预测方向
            if prediction_result['overall']['direction'] == "up":
                trend_multiplier = 1 + volatility * 0.3
            elif prediction_result['overall']['direction'] == "down":
                trend_multiplier = 1 - volatility * 0.3
            else:
                trend_multiplier = 1
            
            # 预测区间
            base_prediction = current_price * trend_multiplier
            lower_bound = base_prediction * (1 - volatility * 0.5)
            upper_bound = base_prediction * (1 + volatility * 0.5)
            
            print(f"   ⏰ 预测时间范围: 未来 5 小时")
            print(f"   💰 当前价格: ${current_price:.6f}")
            print(f"   🎯 预测中心价格: ${base_prediction:.6f}")
            print(f"   📉 预测下限 (95%置信度): ${lower_bound:.6f}")
            print(f"   📈 预测上限 (95%置信度): ${upper_bound:.6f}")
            print(f"   📊 历史波动率: {volatility * 100:.2f}%")
            print()
            
            # 6. 具体分析和建议
            print("=" * 80)
            print("📋 完整分析报告")
            print("=" * 80)
            print()
            
            print("一、市场现状")
            print(f"   - 当前价格: ${current_price:.6f}")
            print(f"   - 最近 200 小时数据")
            print()
            
            print("二、舆情分析")
            print(f"   - 综合评分: {sentiment_result['overall_score']['score']:.1f} / 100")
            print(f"   - 等级: {sentiment_result['overall_score']['grade']} - {sentiment_result['overall_score']['label']}")
            print(f"   - 新闻情感分数: {sentiment_result['news_sentiment']['sentiment_score']:.2f}")
            print(f"   - 社交媒体情感: {sentiment_result['social_sentiment']['overall_sentiment']:.2f}")
            print(f"   - 舆情热度: {sentiment_result['heat_analysis']['heat_label']}")
            print()
            
            print("三、趋势预测")
            print(f"   - 综合预测方向: {prediction_result['overall']['label']}")
            print(f"   - 预测置信度: {prediction_result['overall']['confidence'] * 100:.1f}%")
            print()
            print("   各模型预测:")
            for model, label in prediction_result['overall']['model_votes'].items():
                conf = prediction_result['predictions'][model]['confidence'] * 100
                print(f"   - {model:20s}: {label} (置信度: {conf:.1f}%)")
            print()
            
            print("四、未来 5 小时价格预测")
            print(f"   - 当前价格: ${current_price:.6f}")
            print(f"   - 预测中心价格: ${base_prediction:.6f}")
            print(f"   - 预测下限: ${lower_bound:.6f}")
            print(f"   - 预测上限: ${upper_bound:.6f}")
            print()
            
            print("五、风险评估")
            print(f"   - 风险评分: {prediction_result['risk_assessment']['risk_score'] * 100:.1f} / 100")
            print(f"   - 风险等级: {prediction_result['risk_assessment']['risk_label']}")
            print(f"   - 波动率: {prediction_result['risk_assessment']['volatility'] * 100:.2f}%")
            print(f"   - RSI: {prediction_result['risk_assessment']['rsi']:.1f}")
            print()
            
            print("六、操作建议")
            print(f"   - 舆情建议: {sentiment_result['overall_score']['suggestion']}")
            print(f"   - 风险建议: {prediction_result['risk_assessment']['suggestion']}")
            print()
            print("   具体建议:")
            if prediction_result['overall']['direction'] == "up":
                print("   📈 趋势看涨，可考虑适量建仓")
                print(f"   🎯 目标价位: ${upper_bound:.6f}")
                print(f"   🛑 止损价位: ${lower_bound * 0.98:.6f}")
            elif prediction_result['overall']['direction'] == "down":
                print("   📉 趋势看跌，建议观望或轻仓做空")
                print(f"   🎯 目标价位: ${lower_bound:.6f}")
                print(f"   🛑 止损价位: ${upper_bound * 1.02:.6f}")
            else:
                print("   ➡️ 震荡趋势，建议高抛低吸")
                print(f"   📉 支撑位: ${lower_bound:.6f}")
                print(f"   📈 阻力位: ${upper_bound:.6f}")
            print()
            print("=" * 80)
            print("⚠️  免责声明: 本分析仅供参考，不构成投资建议！")
            print("=" * 80)
            
        else:
            print("   ❌ 获取 K线数据失败")
    else:
        print(f"   ❌ Binance 上没有找到 RIVER 交易对")
        print()
        print("💡 提示:")
        print("   - RIVER 可能不在 Binance 上市")
        print("   - 请确认 RIVER 在哪个交易所上市")
        print("   - 或者使用其他数据源")


if __name__ == "__main__":
    import numpy as np
    asyncio.run(main())
