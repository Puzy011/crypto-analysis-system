import aiohttp
import asyncio
from typing import List, Dict, Any
from app.services.mock_binance_service import MockBinanceService


class BinanceService:
    """币安 API 服务（带备用模拟数据）"""
    
    BASE_URL = "https://api.binance.com"
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取单个交易对的实时行情"""
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/24hr"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    data = await response.json()
                    return self._format_ticker(data)
        except Exception as e:
            print(f"Binance API 访问失败，使用模拟数据: {e}")
            return MockBinanceService.get_ticker(symbol)
    
    async def get_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """获取多个交易对的实时行情"""
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/24hr"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    all_tickers = await response.json()
                    
                    # 过滤出需要的交易对
                    symbol_set = set(symbols)
                    filtered = [
                        self._format_ticker(t) 
                        for t in all_tickers 
                        if t["symbol"] in symbol_set
                    ]
                    return filtered
        except Exception as e:
            print(f"Binance API 访问失败，使用模拟数据: {e}")
            return MockBinanceService.get_tickers(symbols)
    
    async def get_klines(
        self, 
        symbol: str, 
        interval: str = "1h", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            url = f"{self.BASE_URL}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    klines = await response.json()
                    return [self._format_kline(k) for k in klines]
        except Exception as e:
            print(f"Binance API 访问失败，使用模拟数据: {e}")
            return MockBinanceService.get_klines(symbol, interval, limit)
    
    def _format_ticker(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化行情数据"""
        return {
            "symbol": data["symbol"],
            "price": float(data["lastPrice"]),
            "priceChange": float(data["priceChange"]),
            "priceChangePercent": float(data["priceChangePercent"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
            "volume": float(data["volume"]),
            "quoteVolume": float(data["quoteVolume"]),
            "openPrice": float(data["openPrice"]),
            "count": int(data["count"]),
            "timestamp": int(data["closeTime"])
        }
    
    def _format_kline(self, kline: List[Any]) -> Dict[str, Any]:
        """格式化K线数据"""
        return {
            "timestamp": int(kline[0]),
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
            "closeTime": int(kline[6]),
            "quoteVolume": float(kline[7]),
            "trades": int(kline[8]),
            "takerBuyBase": float(kline[9]),
            "takerBuyQuote": float(kline[10])
        }
