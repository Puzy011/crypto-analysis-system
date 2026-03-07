import aiohttp
import pandas as pd
from typing import Dict, Any, List


class OKXService:
    """OKX API 服务"""
    
    BASE_URL = "https://www.okx.com"
    
    @staticmethod
    async def get_klines(
        symbol: str,
        interval: str = "1H",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取K线数据"""
        url = f"{OKXService.BASE_URL}/api/v5/market/candles"
        
        # OKX 时间周期映射
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1H",
            "4h": "4H",
            "1d": "1D",
            "1w": "1W",
            "1M": "1M"
        }
        okx_interval = interval_map.get(interval, "1H")
        
        params = {
            "instId": symbol,
            "bar": okx_interval,
            "limit": str(limit)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"OKX API error: {response.status}")
                data = await response.json()
                if data.get("code") != "0":
                    raise Exception(f"OKX API error: {data.get('msg')}")
                
                # OKX 返回的K线数据格式：
                # [时间, 开盘, 最高, 最低, 收盘, 成交量, ...]
                klines = []
                for k in data["data"]:
                    klines.append(OKXService._format_kline(k))
                
                # 反转顺序（OKX返回最新的在前）
                klines.reverse()
                return klines
    
    @staticmethod
    def _format_kline(kline: List[Any]) -> Dict[str, Any]:
        """格式化K线数据"""
        # OKX K线格式: [时间, 开盘, 最高, 最低, 收盘, 成交量, ...]
        return {
            "timestamp": int(kline[0]),
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
            "closeTime": int(kline[0]),
            "quoteVolume": float(kline[6]) if len(kline) > 6 else 0,
            "trades": 0,
            "takerBuyBase": 0,
            "takerBuyQuote": 0
        }
