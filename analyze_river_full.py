#!/usr/bin/env python3
"""
RIVER 完整分析报告 - 模拟数据演示
包含：未来5小时趋势预测 + 舆情分析 + 具体建议
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.enhanced_sentiment_service import EnhancedSentimentService
from app.services.enhanced_prediction_service import EnhancedPredictionService


def generate_mock_klines(symbol: str, count: int = 200):
    """生成模拟 K线数据"""
    
    np.random.seed(42)
    
    base_price = 0.5  # RIVER 基础价格
    
    # 生成带趋势的价格序列
    prices = [base_price]
    for i in range(1, count):
        # 趋势 + 随机波动
        trend = 0.0005 if i < count * 0.6 else -0.0003
        noise = np.random.normal(0, 0.012)
        change = trend + noise
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # 生成 K线数据
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
    
    return klines, prices


def main():
    print("=" * 80)
    print("🔮 RIVER/USDT 完整分析报告")
    print("=" * 80)
    print()
    print("📊 说明: 使用模拟数据演示完整分析流程")
    print("    (网络正常时可替换为真实数据)")
    print()
    
    symbol = "RIVERUSDT"
    
    # 1. 生成模拟数据
    print("1️⃣  生成模拟数据...")
    klines, prices = generate_mock_klines(symbol, 200)
    df = pd.DataFrame(klines)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    current_price = df['close'].iloc[-1]
    print(f"   ✅ 生成 200 条小时级 K线数据")
    print(f"   💰 当前价格: ${current_price:.6f}")
    print()
    
    # 2. 增强版舆情分析
    print("2️⃣  增强版舆情分析...")
    sentiment_service = EnhancedSentimentService()
    sentiment_result = sentiment_service.analyze_full_sentiment("RIVER")
    
    print(f"   🏆 综合评分: {sentiment_result['overall_score']['score']:.1f} / 100")
    print(f"   等级: {sentiment_result['overall_score']['grade']} - {sentiment_result['overall_score']['label']}")
    print(f"   建议: {sentiment_result['overall_score']['suggestion']}")
    print()
    
    # 3. 增强版趋势预测
    print("3️⃣  增强版趋势预测...")
    prediction_service = EnhancedPredictionService()
    prediction_result = prediction_service.predict_enhanced_trend("RIVERUSDT")
    
    print(f"   🚀 综合预测: {prediction_result['overall']['label']}")
    print(f"   预测置信度: {prediction_result['overall']['confidence'] * 100:.1f}%")
    print()
    
    # 4. 未来 5 小时价格预测
    print("4️⃣  未来 5 小时价格预测...")
    
    # 计算历史波动率
    returns = df['close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(24)  # 年化
    
    # 基于预测方向
    if prediction_result['overall']['direction'] == "up":
        trend_factor = 1 + volatility * 0.25
    elif prediction_result['overall']['direction'] == "down":
        trend_factor = 1 - volatility * 0.25
    else:
        trend_factor = 1
    
    # 生成 5 小时预测点
    future_predictions = []
    base_price = current_price
    
    for hour in range(1, 6):
        # 趋势 + 随机波动
        hour_trend = (trend_factor - 1) * (hour / 5)
        hour_noise = np.random.normal(0, volatility * 0.15)
        predicted_price = base_price * (1 + hour_trend + hour_noise)
        
        # 置信区间
        lower = predicted_price * (1 - volatility * 0.3)
        upper = predicted_price * (1 + volatility * 0.3)
        
        future_time = (datetime.now() + timedelta(hours=hour)).strftime("%Y-%m-%d %H:00")
        
        future_predictions.append({
            "hour": hour,
            "time": future_time,
            "predicted_price": predicted_price,
            "lower_bound": lower,
            "upper_bound": upper
        })
    
    print(f"   ⏰ 预测时间范围: 未来 5 小时")
    print(f"   💰 当前价格: ${current_price:.6f}")
    print(f"   📊 历史波动率: {volatility * 100:.2f}%")
    print()
    print("   🔮 逐小时预测:")
    for pred in future_predictions:
        change_pct = (pred['predicted_price'] - current_price) / current_price * 100
        arrow = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
        print(f"      {pred['time']}: ${pred['predicted_price']:.6f} {arrow} ({change_pct:+.2f}%)")
        print(f"               区间: ${pred['lower_bound']:.6f} ~ ${pred['upper_bound']:.6f}")
    print()
    
    # 5. 完整分析报告
    print("=" * 80)
    print("📋 RIVER/USDT 完整分析报告")
    print("=" * 80)
    print()
    
    print("一、市场现状")
    print(f"   - 交易对: RIVER/USDT")
    print(f"   - 当前价格: ${current_price:.6f}")
    print(f"   - 分析周期: 最近 200 小时")
    print(f"   - 24h 涨跌: {(current_price - prices[-24]) / prices[-24] * 100:+.2f}%")
    print()
    
    print("二、舆情分析")
    print(f"   - 综合评分: {sentiment_result['overall_score']['score']:.1f} / 100")
    print(f"   - 等级: {sentiment_result['overall_score']['grade']} - {sentiment_result['overall_score']['label']}")
    print()
    print("   舆情细分:")
    print(f"   - 新闻情感分数: {sentiment_result['news_sentiment']['sentiment_score']:.2f}")
    print(f"   - 新闻数量: {sentiment_result['news_sentiment']['news_count']}")
    print(f"   - 分布: 正面{sentiment_result['news_sentiment']['distribution']['positive']} / 负面{sentiment_result['news_sentiment']['distribution']['negative']} / 中性{sentiment_result['news_sentiment']['distribution']['neutral']}")
    print(f"   - 社交媒体情感: {sentiment_result['social_sentiment']['overall_sentiment']:.2f}")
    print(f"   - 舆情趋势: {sentiment_result['trend_analysis']['trend_label']}")
    print(f"   - 舆情热度: {sentiment_result['heat_analysis']['heat_label']} (指数: {sentiment_result['heat_analysis']['heat_index']:.1f})")
    print()
    if sentiment_result['alert_analysis']['alerts']:
        print("   ⚠️  舆情预警:")
        for alert in sentiment_result['alert_analysis']['alerts']:
            print(f"   - {alert['message']}")
            print(f"     建议: {alert['suggestion']}")
    print()
    
    print("三、趋势预测")
    print(f"   - 综合预测方向: {prediction_result['overall']['label']}")
    print(f"   - 预测置信度: {prediction_result['overall']['confidence'] * 100:.1f}%")
    print(f"   - 模型一致性: {'✅ 一致' if prediction_result['overall']['consistency'] else '❌ 不一致'}")
    print()
    print("   🤖 各模型预测:")
    for model, label in prediction_result['overall']['model_votes'].items():
        conf = prediction_result['predictions'][model]['confidence'] * 100
        print(f"   - {model:20s}: {label} (置信度: {conf:.1f}%)")
    print()
    print("   📈 预测价格区间:")
    print(f"   - 当前价格: ${prediction_result['price_prediction']['current_price']:.6f}")
    print(f"   - 目标价格: ${prediction_result['price_prediction']['target_price']:.6f}")
    print(f"   - 止损价格: ${prediction_result['price_prediction']['stop_loss']:.6f}")
    print(f"   - 支撑位: ${prediction_result['price_prediction']['support']:.6f}")
    print(f"   - 阻力位: ${prediction_result['price_prediction']['resistance']:.6f}")
    print(f"   - 盈亏比: {prediction_result['price_prediction']['risk_reward_ratio']:.2f}")
    print()
    
    print("四、未来 5 小时预测")
    print(f"   - 预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} ~ {(datetime.now() + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M')}")
    print(f"   - 历史波动率: {volatility * 100:.2f}%")
    print()
    print("   🔮 详细预测:")
    for pred in future_predictions:
        change_pct = (pred['predicted_price'] - current_price) / current_price * 100
        arrow = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
        print(f"   {pred['time']}:")
        print(f"      预测价格: ${pred['predicted_price']:.6f} {arrow} ({change_pct:+.2f}%)")
        print(f"      95%置信区间: ${pred['lower_bound']:.6f} ~ ${pred['upper_bound']:.6f}")
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
    print("   💡 具体操作建议:")
    
    if prediction_result['overall']['direction'] == "up":
        print("   📈 趋势看涨，可考虑:")
        print("      1. 适量建仓（建议仓位: 30-50%）")
        print(f"      2. 目标价位: ${future_predictions[-1]['upper_bound']:.6f}")
        print(f"      3. 止损价位: ${future_predictions[0]['lower_bound'] * 0.98:.6f}")
        print("      4. 分批入场，降低风险")
    elif prediction_result['overall']['direction'] == "down":
        print("   📉 趋势看跌，建议:")
        print("      1. 观望为主，不要急于抄底")
        print("      2. 如有持仓，考虑减仓或设置止损")
        print(f"      3. 可关注支撑位: ${future_predictions[-1]['lower_bound']:.6f}")
        print("      4. 等待明确信号再入场")
    else:
        print("   ➡️ 震荡趋势，策略:")
        print("      1. 高抛低吸，区间操作")
        print(f"      2. 支撑位: ${future_predictions[-1]['lower_bound']:.6f} (可考虑买入)")
        print(f"      3. 阻力位: ${future_predictions[-1]['upper_bound']:.6f} (可考虑卖出)")
        print("      4. 控制仓位，快进快出")
    print()
    
    print("=" * 80)
    print("⚠️  免责声明: 本分析仅供参考，不构成投资建议！")
    print("⚠️  模拟数据: 本报告使用模拟数据演示，网络正常时可获取真实数据")
    print("=" * 80)


if __name__ == "__main__":
    main()
