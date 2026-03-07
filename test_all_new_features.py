#!/usr/bin/env python3
"""
演示所有新添加的功能！
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.enhanced_sentiment_service import EnhancedSentimentService
from app.services.backtest_service import BacktestService
from app.services.simulation_service import get_simulation_service
from app.services.multi_timeframe_service import MultiTimeframeService
from app.services.enhanced_prediction_service import EnhancedPredictionService


def demo_enhanced_sentiment():
    """演示增强版舆情分析"""
    print("=" * 80)
    print("📰 演示 1: 增强版舆情分析")
    print("=" * 80)
    print()
    
    service = EnhancedSentimentService()
    result = service.analyze_full_sentiment("BTC")
    
    print(f"📊 分析对象: {result['keyword']}")
    print()
    print(f"🏆 综合评分: {result['overall_score']['score']:.1f} / 100")
    print(f"   等级: {result['overall_score']['grade']} - {result['overall_score']['label']}")
    print(f"   建议: {result['overall_score']['suggestion']}")
    print()
    print("📰 新闻情感:")
    print(f"   情感分数: {result['news_sentiment']['sentiment_score']:.2f}")
    print(f"   新闻数量: {result['news_sentiment']['news_count']}")
    print(f"   分布: 正面{result['news_sentiment']['distribution']['positive']} / 负面{result['news_sentiment']['distribution']['negative']} / 中性{result['news_sentiment']['distribution']['neutral']}")
    print()
    print("🐦 社交媒体:")
    print(f"   整体情感: {result['social_sentiment']['overall_sentiment']:.2f}")
    print(f"   热门话题: {', '.join(result['social_sentiment']['hot_topics'][:3])}")
    print()
    print("📈 舆情趋势:")
    print(f"   趋势方向: {result['trend_analysis']['trend_label']}")
    print()
    print("🔥 舆情热度:")
    print(f"   热度指数: {result['heat_analysis']['heat_index']:.1f}")
    print(f"   热度等级: {result['heat_analysis']['heat_label']}")
    print()
    print("⚠️  预警分析:")
    print(f"   预警数量: {result['alert_analysis']['alert_count']}")
    print(f"   风险等级: {result['alert_analysis']['risk_level']}")
    for alert in result['alert_analysis']['alerts'][:2]:
        print(f"   - {alert['message']}")
    print()


def demo_backtest():
    """演示策略回测"""
    print("=" * 80)
    print("📈 演示 2: 策略回测")
    print("=" * 80)
    print()
    
    service = BacktestService()
    result = service.run_backtest("BTCUSDT", initial_balance=10000.0)
    
    print(f"📊 回测对象: {result['symbol']}")
    print()
    print("💰 账户表现:")
    print(f"   初始资金: ${result['results']['initial_balance']:.2f}")
    print(f"   最终资金: ${result['results']['final_balance']:.2f}")
    print(f"   总收益率: {result['results']['total_return'] * 100:.2f}%")
    print(f"   年化收益率: {result['results']['annual_return'] * 100:.2f}%")
    print(f"   等级: {result['results']['grade']} - {result['results']['label']}")
    print()
    print("📊 风险指标:")
    print(f"   最大回撤: {result['results']['max_drawdown'] * 100:.2f}%")
    print(f"   夏普比率: {result['results']['sharpe_ratio']:.2f}")
    print(f"   盈亏比: {result['results']['profit_factor']:.2f}")
    print()
    print("📈 交易统计:")
    print(f"   总交易次数: {result['results']['total_trades']}")
    print(f"   买入次数: {result['results']['buy_trades']}")
    print(f"   卖出次数: {result['results']['sell_trades']}")
    print(f"   胜率: {result['results']['win_rate'] * 100:.1f}%")
    print()
    print("💰 盈亏统计:")
    print(f"   总盈利: ${result['results']['total_profit']:.2f}")
    print(f"   总亏损: ${result['results']['total_loss']:.2f}")
    print()


def demo_simulation():
    """演示模拟交易"""
    print("=" * 80)
    print("🎮 演示 3: 模拟交易 (Dry-run)")
    print("=" * 80)
    print()
    
    service = get_simulation_service()
    
    # 创建账户
    print("1️⃣  创建模拟账户...")
    account_id = service.create_account(initial_balance=10000.0, name="测试账户")
    print(f"   账户ID: {account_id}")
    print()
    
    # 下单
    print("2️⃣  下单买入 BTCUSDT...")
    order_result = service.place_order(
        account_id=account_id,
        symbol="BTCUSDT",
        side="buy",
        order_type="market",
        quantity=0.1
    )
    if order_result.get("success"):
        print(f"   订单状态: {order_result['data']['status']}")
        print(f"   成交价格: ${order_result['data']['price']:.2f}")
        print(f"   成交数量: {order_result['data']['quantity']}")
    print()
    
    # 查询账户
    print("3️⃣  查询账户信息...")
    account = service.get_account(account_id)
    print(f"   账户名称: {account['name']}")
    print(f"   当前余额: ${account['current_balance']:.2f}")
    print(f"   可用余额: ${account['available_balance']:.2f}")
    print(f"   未实现盈亏: ${account['unrealized_pnl']:.2f}")
    print(f"   已实现盈亏: ${account['realized_pnl']:.2f}")
    print()
    
    # 查询交易历史
    print("4️⃣  查询交易历史...")
    trades = service.get_trades(account_id, limit=5)
    print(f"   交易记录数: {len(trades)}")
    for trade in trades[:2]:
        print(f"   - {trade['side'].upper()} {trade['symbol']}: {trade['quantity']} @ ${trade['price']:.2f}")
    print()
    
    # 查询账户表现
    print("5️⃣  查询账户表现...")
    performance = service.get_performance(account_id)
    print(f"   总收益率: {performance['total_return'] * 100:.2f}%")
    print(f"   已实现盈亏: ${performance['realized_pnl']:.2f}")
    print(f"   未实现盈亏: ${performance['unrealized_pnl']:.2f}")
    print(f"   最大回撤: {performance['max_drawdown'] * 100:.2f}%")
    print()


def demo_multi_timeframe():
    """演示多时间周期分析"""
    print("=" * 80)
    print("⏰ 演示 4: 多时间周期分析")
    print("=" * 80)
    print()
    
    service = MultiTimeframeService()
    result = service.analyze_multi_timeframe("BTCUSDT", ["1m", "15m", "1h", "4h", "1d"])
    
    print(f"📊 分析对象: {result['symbol']}")
    print()
    print("🌐 综合判断:")
    print(f"   综合方向: {result['overall']['label']}")
    print(f"   各周期一致性: {'✅ 一致' if result['overall']['consistency'] else '❌ 不一致'}")
    print()
    print("📊 各时间周期分析:")
    for tf in result['timeframes']:
        data = result['results'][tf]
        print(f"   {tf:4s}: {data['trend']['label']} | 当前: ${data['current_price']:.2f} | RSI: {data['indicators']['rsi']:.1f}")
    print()
    print("📊 时间周期总结:")
    for tf, label in result['overall']['timeframe_summary'].items():
        print(f"   {tf:4s}: {label}")
    print()


def demo_enhanced_prediction():
    """演示增强版趋势预测"""
    print("=" * 80)
    print("🔮 演示 5: 增强版趋势预测")
    print("=" * 80)
    print()
    
    service = EnhancedPredictionService()
    result = service.predict_enhanced_trend("BTCUSDT")
    
    print(f"📊 预测对象: {result['symbol']}")
    print(f"⏰ 时间周期: {result['timeframe']}")
    print()
    print("🚀 综合预测:")
    print(f"   预测方向: {result['overall']['label']}")
    print(f"   预测置信度: {result['overall']['confidence'] * 100:.1f}%")
    print(f"   模型一致性: {'✅ 一致' if result['overall']['consistency'] else '❌ 不一致'}")
    print()
    print("🤖 各模型预测:")
    for model, label in result['overall']['model_votes'].items():
        conf = result['predictions'][model]['confidence'] * 100
        print(f"   {model:20s}: {label} (置信度: {conf:.1f}%)")
    print()
    print("📈 预测结果:")
    print(f"   当前价格: ${result['price_prediction']['current_price']:.2f}")
    print(f"   目标价格: ${result['price_prediction']['target_price']:.2f}")
    print(f"   止损价格: ${result['price_prediction']['stop_loss']:.2f}")
    print(f"   支撑位: ${result['price_prediction']['support']:.2f}")
    print(f"   阻力位: ${result['price_prediction']['resistance']:.2f}")
    print(f"   盈亏比: {result['price_prediction']['risk_reward_ratio']:.2f}")
    print()
    print("⚠️  风险评估:")
    print(f"   风险评分: {result['risk_assessment']['risk_score'] * 100:.1f} / 100")
    print(f"   风险等级: {result['risk_assessment']['risk_label']}")
    print(f"   波动率: {result['risk_assessment']['volatility'] * 100:.2f}%")
    print(f"   RSI: {result['risk_assessment']['rsi']:.1f}")
    print(f"   建议: {result['risk_assessment']['suggestion']}")
    print()


def main():
    print()
    print("🚀" * 20)
    print("🚀" + " " * 36 + "🚀")
    print("🚀  虚拟货币分析预测系统 - 新功能演示  🚀")
    print("🚀" + " " * 36 + "🚀")
    print("🚀" * 20)
    print()
    
    # 演示所有功能
    demo_enhanced_sentiment()
    demo_backtest()
    demo_simulation()
    demo_multi_timeframe()
    demo_enhanced_prediction()
    
    print("=" * 80)
    print("🎉 所有新功能演示完成！")
    print("=" * 80)
    print()
    print("📋 新增功能清单:")
    print("  1. ✅ 增强版舆情分析 - 全方面分析")
    print("  2. ✅ 策略回测功能 - 历史数据回测")
    print("  3. ✅ 模拟交易 (Dry-run) - 模拟交易不亏钱")
    print("  4. ✅ 多时间周期分析 - 同时看多个时间周期")
    print("  5. ✅ 增强版趋势预测 - 多模型综合预测")
    print()
    print("💡 所有功能都已集成到系统中！")
    print()


if __name__ == "__main__":
    main()
