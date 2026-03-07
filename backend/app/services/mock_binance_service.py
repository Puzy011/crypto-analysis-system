import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta


class MockBinanceService:
    """模拟币安 API 服务（备用方案）"""
    
    @staticmethod
    def get_ticker(symbol: str) -> Dict[str, Any]:
        """获取单个交易对的实时行情（模拟数据）"""
        
        base_price = MockBinanceService._get_base_price(symbol)
        
        # 随机波动
        price_change = np.random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + price_change)
        
        return {
            "symbol": symbol,
            "price": float(current_price),
            "priceChange": float(current_price - base_price),
            "priceChangePercent": float(price_change * 100),
            "high": float(current_price * 1.02),
            "low": float(current_price * 0.98),
            "volume": float(np.random.uniform(10000, 100000)),
            "quoteVolume": float(np.random.uniform(100000, 1000000)),
            "openPrice": float(base_price),
            "count": int(np.random.randint(1000, 10000)),
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    @staticmethod
    def get_tickers(symbols: List[str]) -> List[Dict[str, Any]]:
        """获取多个交易对的实时行情（模拟数据）"""
        return [MockBinanceService.get_ticker(symbol) for symbol in symbols]
    
    @staticmethod
    def get_klines(
        symbol: str,
        interval: str = "1h",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取K线数据（模拟数据）"""
        
        base_price = MockBinanceService._get_base_price(symbol)
        
        # 生成带趋势的价格序列
        np.random.seed(42)
        
        prices = [base_price]
        for i in range(1, limit):
            trend = 0.0001 if i < limit * 0.6 else -0.0002
            noise = np.random.normal(0, 0.01)
            change = trend + noise
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # 生成K线数据
        klines = []
        now = datetime.now()
        
        # 根据间隔确定时间增量
        if interval == "1m":
            delta = timedelta(minutes=1)
        elif interval == "5m":
            delta = timedelta(minutes=5)
        elif interval == "15m":
            delta = timedelta(minutes=15)
        elif interval == "1h":
            delta = timedelta(hours=1)
        elif interval == "4h":
            delta = timedelta(hours=4)
        elif interval == "1d":
            delta = timedelta(days=1)
        else:
            delta = timedelta(hours=1)
        
        for i in range(limit):
            timestamp = int((now - delta * (limit - i)).timestamp() * 1000)
            
            open_p = prices[i]
            close_p = prices[i]
            high_p = prices[i] * (1 + abs(np.random.normal(0, 0.008)))
            low_p = prices[i] * (1 - abs(np.random.normal(0, 0.008)))
            volume = np.random.uniform(1000, 10000)
            
            klines.append({
                "timestamp": timestamp,
                "open": float(open_p),
                "high": float(high_p),
                "low": float(low_p),
                "close": float(close_p),
                "volume": float(volume),
                "closeTime": timestamp + 3600000,  # 1小时
                "quoteVolume": float(volume * close_p),
                "trades": int(np.random.randint(100, 1000)),
                "takerBuyBase": float(volume * 0.5),
                "takerBuyQuote": float(volume * close_p * 0.5)
            })
        
        return klines
    
    @staticmethod
    def _get_base_price(symbol: str) -> float:
        """获取基础价格"""
        symbol = symbol.upper()
        
        price_map = {
            "BTCUSDT": 73000.0,
            "ETHUSDT": 3500.0,
            "BNBUSDT": 600.0,
            "SOLUSDT": 150.0,
            "XRPUSDT": 0.5,
            "RIVERUSDT": 0.42,
            "DOGEUSDT": 0.15,
            "ADAUSDT": 0.45,
            "AVAXUSDT": 35.0,
            "DOTUSDT": 7.0
        }
        
        return price_map.get(symbol, 100.0)


# 全局实例
_mock_binance_service = None


def get_mock_binance_service() -> MockBinanceService:
    """获取模拟币安服务单例"""
    global _mock_binance_service
    if _mock_binance_service is None:
        _mock_binance_service = MockBinanceService()
    return _mock_binance_service
