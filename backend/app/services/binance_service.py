import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
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

    async def get_trading_symbols(
        self,
        quote_asset: str = "USDT",
        limit: int = 200,
        include_leveraged: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        获取可交易交易对列表（默认 USDT 计价），并按 24h quoteVolume 排序
        """
        normalized_quote = (quote_asset or "USDT").upper()
        try:
            async with aiohttp.ClientSession() as session:
                # 1) 交易对元信息
                exchange_url = f"{self.BASE_URL}/api/v3/exchangeInfo"
                async with session.get(exchange_url, timeout=8) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    exchange_info = await response.json()

                raw_symbols = exchange_info.get("symbols", []) or []
                candidates: List[Dict[str, Any]] = []
                for row in raw_symbols:
                    symbol = str(row.get("symbol", "")).upper()
                    base_asset = str(row.get("baseAsset", "")).upper()
                    q_asset = str(row.get("quoteAsset", "")).upper()
                    status = str(row.get("status", "")).upper()
                    is_spot = bool(row.get("isSpotTradingAllowed", False))
                    if not symbol or q_asset != normalized_quote:
                        continue
                    if status != "TRADING" or not is_spot:
                        continue
                    if not include_leveraged and self._is_leveraged_token(base_asset):
                        continue
                    candidates.append(
                        {
                            "symbol": symbol,
                            "baseAsset": base_asset,
                            "quoteAsset": q_asset,
                            "status": status,
                        }
                    )

                if not candidates:
                    return []

                # 2) 成交额排序
                ticker_url = f"{self.BASE_URL}/api/v3/ticker/24hr"
                async with session.get(ticker_url, timeout=8) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    all_tickers = await response.json()

                volume_map: Dict[str, float] = {}
                for t in all_tickers:
                    sym = str(t.get("symbol", "")).upper()
                    try:
                        volume_map[sym] = float(t.get("quoteVolume", 0) or 0)
                    except Exception:
                        volume_map[sym] = 0.0

                for item in candidates:
                    item["quoteVolume"] = float(volume_map.get(item["symbol"], 0.0))

                candidates.sort(key=lambda x: float(x.get("quoteVolume", 0.0)), reverse=True)
                return candidates[: max(1, min(int(limit), 500))]
        except Exception as e:
            print(f"Binance symbols 访问失败，使用模拟数据: {e}")
            return MockBinanceService.get_trading_symbols(
                quote_asset=normalized_quote,
                limit=limit,
                include_leveraged=include_leveraged,
            )
    
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

    async def get_agg_trades(
        self,
        symbol: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """获取聚合成交（逐笔近似）"""
        try:
            url = f"{self.BASE_URL}/api/v3/aggTrades"
            params = {"symbol": symbol, "limit": max(1, min(limit, 1000))}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    trades = await response.json()
                    return [self._format_agg_trade(t) for t in trades]
        except Exception as e:
            print(f"Binance aggTrades 访问失败: {e}")
            return []

    async def get_order_book(
        self,
        symbol: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取现货订单簿深度"""
        try:
            url = f"{self.BASE_URL}/api/v3/depth"
            params = {"symbol": symbol, "limit": max(5, min(limit, 5000))}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance API error: {response.status}")
                    data = await response.json()
                    return self._format_order_book(symbol, data)
        except Exception as e:
            print(f"Binance order book 访问失败: {e}")
            return {"symbol": symbol, "bids": [], "asks": [], "timestamp": int(datetime.now().timestamp() * 1000)}

    async def get_futures_open_interest(
        self,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """获取合约持仓量（Open Interest）"""
        try:
            url = "https://fapi.binance.com/fapi/v1/openInterest"
            params = {"symbol": symbol}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance Futures API error: {response.status}")
                    data = await response.json()
                    return {
                        "symbol": data.get("symbol", symbol),
                        "open_interest": float(data.get("openInterest", 0)),
                        "timestamp": int(data.get("time", 0) or 0),
                    }
        except Exception as e:
            print(f"Binance futures open interest 访问失败: {e}")
            return None

    async def get_global_long_short_ratio(
        self,
        symbol: str,
        period: str = "1h",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取全市场多空账户比（合约）"""
        try:
            url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
            params = {
                "symbol": symbol,
                "period": period,
                "limit": max(1, min(limit, 500)),
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance Futures API error: {response.status}")
                    data = await response.json()
                    result = []
                    for item in data:
                        result.append({
                            "symbol": item.get("symbol", symbol),
                            "long_short_ratio": float(item.get("longShortRatio", 0)),
                            "long_account": float(item.get("longAccount", 0)),
                            "short_account": float(item.get("shortAccount", 0)),
                            "timestamp": int(item.get("timestamp", 0)),
                        })
                    return result
        except Exception as e:
            print(f"Binance global long/short ratio 访问失败: {e}")
            return []

    async def get_open_interest_hist(
        self,
        symbol: str,
        period: str = "1h",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取合约持仓量历史"""
        try:
            url = "https://fapi.binance.com/futures/data/openInterestHist"
            params = {
                "symbol": symbol,
                "period": period,
                "limit": max(1, min(limit, 500)),
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance Futures API error: {response.status}")
                    data = await response.json()
                    result = []
                    for item in data:
                        result.append({
                            "symbol": item.get("symbol", symbol),
                            "sum_open_interest": float(item.get("sumOpenInterest", 0)),
                            "sum_open_interest_value": float(item.get("sumOpenInterestValue", 0)),
                            "timestamp": int(item.get("timestamp", 0)),
                        })
                    return result
        except Exception as e:
            print(f"Binance open interest history 访问失败: {e}")
            return []

    async def get_funding_rate(
        self,
        symbol: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取资金费率历史"""
        try:
            url = "https://fapi.binance.com/fapi/v1/fundingRate"
            params = {
                "symbol": symbol,
                "limit": max(1, min(limit, 1000)),
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Binance Futures API error: {response.status}")
                    data = await response.json()
                    result = []
                    for item in data:
                        result.append({
                            "symbol": item.get("symbol", symbol),
                            "funding_rate": float(item.get("fundingRate", 0)),
                            "mark_price": float(item.get("markPrice", 0)),
                            "timestamp": int(item.get("fundingTime", 0)),
                        })
                    return result
        except Exception as e:
            print(f"Binance funding rate 访问失败: {e}")
            return []
    
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

    def _format_agg_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """格式化聚合成交数据"""
        return {
            "id": int(trade.get("a", 0)),
            "price": float(trade.get("p", 0)),
            "amount": float(trade.get("q", 0)),
            "first_trade_id": int(trade.get("f", 0)),
            "last_trade_id": int(trade.get("l", 0)),
            "timestamp": int(trade.get("T", 0)),
            "is_buyer_maker": bool(trade.get("m", False)),
            "is_best_match": bool(trade.get("M", False)),
        }

    def _format_order_book(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化订单簿"""
        bids = []
        asks = []
        for bid in data.get("bids", []):
            if len(bid) >= 2:
                bids.append({"price": float(bid[0]), "amount": float(bid[1])})
        for ask in data.get("asks", []):
            if len(ask) >= 2:
                asks.append({"price": float(ask[0]), "amount": float(ask[1])})
        return {
            "symbol": symbol,
            "last_update_id": int(data.get("lastUpdateId", 0)),
            "bids": bids,
            "asks": asks,
        }

    def _is_leveraged_token(self, base_asset: str) -> bool:
        """过滤杠杆代币（UP/DOWN/BULL/BEAR）"""
        upper = (base_asset or "").upper()
        return upper.endswith("UP") or upper.endswith("DOWN") or upper.endswith("BULL") or upper.endswith("BEAR")
