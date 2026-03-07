#!/usr/bin/env python3
"""
测试通过代理连接 Binance
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import aiohttp

# 设置代理
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'


async def test_binance():
    print("🔮 测试通过代理连接 Binance...")
    print()
    
    # 测试获取 BTCUSDT 实时价格
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
    
    print(f"📡 请求 URL: {url}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy="http://127.0.0.1:7890") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Binance API 连接成功！")
                    print()
                    print("📊 BTCUSDT 24小时行情:")
                    print(f"   当前价格: ${float(data['lastPrice']):.2f}")
                    print(f"   24h 涨跌: {float(data['priceChangePercent']):.2f}%")
                    print(f"   24h 最高: ${float(data['highPrice']):.2f}")
                    print(f"   24h 最低: ${float(data['lowPrice']):.2f}")
                    print(f"   24h 成交量: {float(data['volume']):.2f}")
                    print()
                    
                    # 测试获取 K线
                    print("📡 测试获取 K线数据...")
                    kline_url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=10"
                    async with session.get(kline_url, proxy="http://127.0.0.1:7890") as kline_response:
                        if kline_response.status == 200:
                            klines = await kline_response.json()
                            print(f"✅ K线数据获取成功！获取到 {len(klines)} 条 K线")
                            print()
                            print("📈 最近5条 K线:")
                            for k in klines[-5:]:
                                print(f"   时间: {pd.to_datetime(k[0], unit='ms')} | 开盘: ${float(k[1]):.2f} | 收盘: ${float(k[4]):.2f}")
                            print()
                            print("🎉 所有测试成功！代理配置完成！")
                else:
                    print(f"❌ 请求失败: {response.status}")
                    
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 添加 pandas 用于时间格式化
    import pandas as pd
    asyncio.run(test_binance())
