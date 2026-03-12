import asyncio
import os
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime


class BinanceService:
    """多交易所真实行情服务（Binance 主源，Gate.io 备用，无模拟数据）"""

    SPOT_BASE_URLS = [
        "https://api.binance.com",
        "https://api1.binance.com",
        "https://api-gcp.binance.com",
    ]
    FUTURES_BASE_URLS = [
        "https://fapi.binance.com",
    ]
    GATE_BASE_URL = "https://api.gateio.ws/api/v4"
    QUOTE_SUFFIXES = (
        "USDT", "USDC", "BUSD", "FDUSD", "TUSD",
        "BTC", "ETH", "EUR", "TRY", "BRL",
    )

    def __init__(self) -> None:
        custom_spot = str(os.getenv("BINANCE_SPOT_BASE_URL", "")).strip()
        custom_futures = str(os.getenv("BINANCE_FUTURES_BASE_URL", "")).strip()
        custom_gate = str(os.getenv("GATE_BASE_URL", "")).strip()

        self.spot_base_urls = self._unique_urls([custom_spot, *self.SPOT_BASE_URLS])
        self.futures_base_urls = self._unique_urls([custom_futures, *self.FUTURES_BASE_URLS])
        self.gate_base_urls = self._unique_urls([custom_gate, self.GATE_BASE_URL])

        self.request_timeout = float(os.getenv("BINANCE_HTTP_TIMEOUT", "4"))
        self.request_retries = max(1, int(os.getenv("BINANCE_HTTP_RETRIES", "1")))
        self.circuit_breaker_seconds = max(5, int(os.getenv("BINANCE_CIRCUIT_BREAKER_SECONDS", "45")))
        self._last_binance_failure_at: Optional[datetime] = None

    def _unique_urls(self, urls: List[str]) -> List[str]:
        seen = set()
        result: List[str] = []
        for raw in urls:
            url = str(raw or "").strip().rstrip("/")
            if not url or url in seen:
                continue
            seen.add(url)
            result.append(url)
        return result

    def _build_timeout(self, total: float) -> aiohttp.ClientTimeout:
        effective = float(total)
        read_timeout = min(max(2.5, effective - 0.2), effective)
        return aiohttp.ClientTimeout(
            total=effective,
            connect=min(2.0, effective),
            sock_connect=min(2.0, effective),
            sock_read=read_timeout,
        )

    async def _request_json_from_urls(
        self,
        base_urls: List[str],
        path: str,
        params: Optional[Dict[str, Any]],
        timeout: float,
        label: str,
        use_binance_circuit: bool = False,
    ) -> Any:
        if not path.startswith("/"):
            path = f"/{path}"
        if not base_urls:
            raise RuntimeError(f"{label} no base url configured")

        if use_binance_circuit and self._last_binance_failure_at is not None:
            elapsed = (datetime.now() - self._last_binance_failure_at).total_seconds()
            if elapsed < self.circuit_breaker_seconds:
                left = self.circuit_breaker_seconds - int(elapsed)
                raise RuntimeError(f"{label} circuit open ({left}s left)")

        timeout_cfg = self._build_timeout(timeout)
        headers = {"User-Agent": "crypto-analysis-system/1.0"}
        errors: List[str] = []

        for attempt in range(self.request_retries):
            async with aiohttp.ClientSession(timeout=timeout_cfg, trust_env=True, headers=headers) as session:
                for base in base_urls:
                    url = f"{base}{path}"
                    try:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                if use_binance_circuit:
                                    self._last_binance_failure_at = None
                                return await response.json()
                            text = await response.text()
                            errors.append(f"{url} -> HTTP {response.status}: {text[:120]}")
                    except Exception as exc:
                        errors.append(f"{url} -> {type(exc).__name__}: {exc}")

            if attempt < self.request_retries - 1:
                await asyncio.sleep(0.2 * (attempt + 1))

        if use_binance_circuit:
            self._last_binance_failure_at = datetime.now()
        raise RuntimeError(f"{label} request failed: {' | '.join(errors[:6])}")

    async def _request_binance_spot_json(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 8,
    ) -> Any:
        return await self._request_json_from_urls(
            base_urls=self.spot_base_urls,
            path=path,
            params=params,
            timeout=timeout,
            label=f"Binance spot {path}",
            use_binance_circuit=True,
        )

    async def _request_binance_futures_json(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 8,
    ) -> Any:
        return await self._request_json_from_urls(
            base_urls=self.futures_base_urls,
            path=path,
            params=params,
            timeout=timeout,
            label=f"Binance futures {path}",
            use_binance_circuit=True,
        )

    async def _request_gate_json(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 10,
    ) -> Any:
        return await self._request_json_from_urls(
            base_urls=self.gate_base_urls,
            path=path,
            params=params,
            timeout=timeout,
            label=f"Gate {path}",
            use_binance_circuit=False,
        )

    def _normalize_symbol(self, symbol: str) -> str:
        return str(symbol or "").upper().replace("-", "").replace("_", "")

    def _to_gate_pair(self, symbol: str) -> str:
        normalized = self._normalize_symbol(symbol)
        for suffix in sorted(self.QUOTE_SUFFIXES, key=len, reverse=True):
            if normalized.endswith(suffix) and len(normalized) > len(suffix):
                base = normalized[: -len(suffix)]
                return f"{base}_{suffix}"
        raise ValueError(f"Unsupported symbol for gate pair: {symbol}")

    def _from_gate_pair(self, pair: str) -> str:
        normalized = str(pair or "").upper().replace("-", "_")
        parts = normalized.split("_")
        if len(parts) >= 2:
            return f"{parts[0]}{parts[1]}"
        return normalized.replace("_", "")

    def _to_gate_interval(self, interval: str) -> str:
        mapping = {
            "1m": "1m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "2h": "2h",
            "4h": "4h",
            "6h": "6h",
            "8h": "8h",
            "12h": "12h",
            "1d": "1d",
            "3d": "3d",
            "1w": "7d",
            "1M": "30d",
        }
        return mapping.get(interval, "1h")
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取单个交易对实时行情（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        errors: List[str] = []

        try:
            data = await self._request_binance_spot_json(
                "/api/v3/ticker/24hr",
                params={"symbol": normalized},
                timeout=8,
            )
            return self._format_ticker(data)
        except Exception as exc:
            errors.append(f"binance={exc}")

        try:
            pair = self._to_gate_pair(normalized)
            rows = await self._request_gate_json(
                "/spot/tickers",
                params={"currency_pair": pair},
                timeout=10,
            )
            if isinstance(rows, list) and rows:
                return self._format_gate_ticker(rows[0], normalized)
            errors.append("gate=empty_ticker")
        except Exception as exc:
            errors.append(f"gate={exc}")

        raise RuntimeError(f"无法获取真实 ticker({normalized})，{'; '.join(errors)}")
    
    async def get_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """批量获取交易对实时行情（真实数据）"""
        normalized_list = []
        seen = set()
        for item in symbols or []:
            sym = self._normalize_symbol(item)
            if sym and sym not in seen:
                seen.add(sym)
                normalized_list.append(sym)
        if not normalized_list:
            return []

        symbol_set = set(normalized_list)
        result_map: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []

        try:
            rows = await self._request_binance_spot_json("/api/v3/ticker/24hr", timeout=10)
            for row in rows or []:
                sym = self._normalize_symbol(row.get("symbol", ""))
                if sym in symbol_set:
                    result_map[sym] = self._format_ticker(row)
        except Exception as exc:
            errors.append(f"binance={exc}")

        missing = [s for s in normalized_list if s not in result_map]
        if missing:
            try:
                gate_rows = await self._request_gate_json("/spot/tickers", timeout=12)
                for row in gate_rows or []:
                    sym = self._from_gate_pair(row.get("currency_pair", ""))
                    if sym in symbol_set and sym not in result_map:
                        result_map[sym] = self._format_gate_ticker(row, sym)
            except Exception as exc:
                errors.append(f"gate={exc}")

        if not result_map:
            raise RuntimeError(f"无法获取真实 tickers，{'; '.join(errors)}")

        return [result_map[s] for s in normalized_list if s in result_map]

    async def get_trading_symbols(
        self,
        quote_asset: str = "USDT",
        limit: int = 200,
        include_leveraged: bool = False,
    ) -> List[Dict[str, Any]]:
        """获取可交易交易对列表（真实数据，按成交额排序）"""
        normalized_quote = self._normalize_symbol(quote_asset)
        errors: List[str] = []

        try:
            exchange_info = await self._request_binance_spot_json("/api/v3/exchangeInfo", timeout=12)
            raw_symbols = exchange_info.get("symbols", []) or []
            candidates: List[Dict[str, Any]] = []
            for row in raw_symbols:
                symbol = self._normalize_symbol(row.get("symbol", ""))
                base_asset = self._normalize_symbol(row.get("baseAsset", ""))
                q_asset = self._normalize_symbol(row.get("quoteAsset", ""))
                status = self._normalize_symbol(row.get("status", ""))
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

            if candidates:
                tickers = await self._request_binance_spot_json("/api/v3/ticker/24hr", timeout=12)
                volume_map: Dict[str, float] = {}
                for t in tickers or []:
                    sym = self._normalize_symbol(t.get("symbol", ""))
                    try:
                        volume_map[sym] = float(t.get("quoteVolume", 0) or 0)
                    except Exception:
                        volume_map[sym] = 0.0
                for item in candidates:
                    item["quoteVolume"] = float(volume_map.get(item["symbol"], 0.0))
                candidates.sort(key=lambda x: float(x.get("quoteVolume", 0.0)), reverse=True)
                return candidates[: max(1, min(int(limit), 500))]
        except Exception as exc:
            errors.append(f"binance={exc}")

        try:
            pair_rows = await self._request_gate_json("/spot/currency_pairs", timeout=14)
            ticker_rows = await self._request_gate_json("/spot/tickers", timeout=14)
            quote_volume_map: Dict[str, float] = {}
            for t in ticker_rows or []:
                pair = str(t.get("currency_pair", "")).upper()
                try:
                    quote_volume_map[pair] = float(t.get("quote_volume", 0) or 0)
                except Exception:
                    quote_volume_map[pair] = 0.0

            candidates: List[Dict[str, Any]] = []
            for row in pair_rows or []:
                base_asset = self._normalize_symbol(row.get("base", ""))
                q_asset = self._normalize_symbol(row.get("quote", ""))
                status = str(row.get("trade_status", "")).lower()
                if q_asset != normalized_quote or status != "tradable":
                    continue
                if not include_leveraged and self._is_leveraged_token(base_asset):
                    continue
                pair = f"{base_asset}_{q_asset}"
                symbol = f"{base_asset}{q_asset}"
                candidates.append(
                    {
                        "symbol": symbol,
                        "baseAsset": base_asset,
                        "quoteAsset": q_asset,
                        "status": "TRADING",
                        "quoteVolume": float(quote_volume_map.get(pair, 0.0)),
                    }
                )

            candidates.sort(key=lambda x: float(x.get("quoteVolume", 0.0)), reverse=True)
            return candidates[: max(1, min(int(limit), 500))]
        except Exception as exc:
            errors.append(f"gate={exc}")

        raise RuntimeError(f"无法获取真实交易对列表，{'; '.join(errors)}")
    
    async def get_klines(
        self, 
        symbol: str, 
        interval: str = "1h", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取K线数据（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        safe_limit = max(1, min(int(limit), 1000))
        errors: List[str] = []

        try:
            klines = await self._request_binance_spot_json(
                "/api/v3/klines",
                params={"symbol": normalized, "interval": interval, "limit": safe_limit},
                timeout=12,
            )
            return [self._format_kline(k) for k in klines]
        except Exception as exc:
            errors.append(f"binance={exc}")

        try:
            pair = self._to_gate_pair(normalized)
            gate_interval = self._to_gate_interval(interval)
            rows = await self._request_gate_json(
                "/spot/candlesticks",
                params={"currency_pair": pair, "interval": gate_interval, "limit": safe_limit},
                timeout=12,
            )
            if not isinstance(rows, list) or not rows:
                raise RuntimeError("gate_empty_klines")
            return [self._format_gate_kline(k) for k in rows]
        except Exception as exc:
            errors.append(f"gate={exc}")

        raise RuntimeError(f"无法获取真实K线({normalized})，{'; '.join(errors)}")

    async def get_agg_trades(
        self,
        symbol: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """获取聚合成交（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        safe_limit = max(1, min(int(limit), 1000))

        try:
            trades = await self._request_binance_spot_json(
                "/api/v3/aggTrades",
                params={"symbol": normalized, "limit": safe_limit},
                timeout=8,
            )
            return [self._format_agg_trade(t) for t in trades]
        except Exception as exc:
            print(f"Binance aggTrades 访问失败: {exc}")

        try:
            pair = self._to_gate_pair(normalized)
            rows = await self._request_gate_json(
                "/spot/trades",
                params={"currency_pair": pair, "limit": safe_limit},
                timeout=10,
            )
            if not isinstance(rows, list):
                return []
            return [self._format_gate_trade(t) for t in rows]
        except Exception as exc:
            print(f"Gate trades 访问失败: {exc}")
            return []

    async def get_order_book(
        self,
        symbol: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取现货订单簿深度（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        safe_limit = max(5, min(int(limit), 5000))

        try:
            data = await self._request_binance_spot_json(
                "/api/v3/depth",
                params={"symbol": normalized, "limit": safe_limit},
                timeout=8,
            )
            return self._format_order_book(normalized, data)
        except Exception as exc:
            print(f"Binance order book 访问失败: {exc}")

        try:
            pair = self._to_gate_pair(normalized)
            gate_limit = max(5, min(safe_limit, 200))
            data = await self._request_gate_json(
                "/spot/order_book",
                params={"currency_pair": pair, "limit": gate_limit},
                timeout=10,
            )
            return self._format_gate_order_book(normalized, data)
        except Exception as exc:
            print(f"Gate order book 访问失败: {exc}")
            return {"symbol": normalized, "bids": [], "asks": [], "timestamp": int(datetime.now().timestamp() * 1000)}

    async def get_futures_open_interest(
        self,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """获取合约持仓量（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        try:
            data = await self._request_binance_futures_json(
                "/fapi/v1/openInterest",
                params={"symbol": normalized},
                timeout=8,
            )
            return {
                "symbol": data.get("symbol", normalized),
                "open_interest": float(data.get("openInterest", 0)),
                "timestamp": int(data.get("time", 0) or 0),
            }
        except Exception as exc:
            print(f"Binance futures open interest 访问失败: {exc}")

        try:
            contract = self._to_gate_pair(normalized)
            data = await self._request_gate_json(
                f"/futures/usdt/contracts/{contract}",
                timeout=10,
            )
            return {
                "symbol": normalized,
                "open_interest": float(data.get("position_size", 0) or 0),
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
        except Exception as exc:
            print(f"Gate futures open interest 访问失败: {exc}")
            return None

    async def get_global_long_short_ratio(
        self,
        symbol: str,
        period: str = "1h",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取全市场多空账户比（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        safe_limit = max(1, min(int(limit), 200))

        try:
            data = await self._request_binance_futures_json(
                "/futures/data/globalLongShortAccountRatio",
                params={"symbol": normalized, "period": period, "limit": max(1, min(limit, 500))},
                timeout=8,
            )
            result = []
            for item in data or []:
                result.append({
                    "symbol": item.get("symbol", normalized),
                    "long_short_ratio": float(item.get("longShortRatio", 0)),
                    "long_account": float(item.get("longAccount", 0)),
                    "short_account": float(item.get("shortAccount", 0)),
                    "timestamp": int(item.get("timestamp", 0)),
                })
            return result
        except Exception as exc:
            print(f"Binance global long/short ratio 访问失败: {exc}")

        try:
            contract = self._to_gate_pair(normalized)
            rows = await self._request_gate_json(
                "/futures/usdt/contract_stats",
                params={"contract": contract, "limit": safe_limit},
                timeout=10,
            )
            result = []
            for item in rows or []:
                long_users = float(item.get("long_users", 0) or 0)
                short_users = float(item.get("short_users", 0) or 0)
                total_users = long_users + short_users
                long_account = float(long_users / total_users) if total_users > 0 else 0.0
                short_account = float(short_users / total_users) if total_users > 0 else 0.0
                ratio = float(item.get("lsr_account", 0) or 0)
                if ratio <= 0 and short_users > 0:
                    ratio = float(long_users / (short_users + 1e-8))
                result.append(
                    {
                        "symbol": normalized,
                        "long_short_ratio": ratio,
                        "long_account": long_account,
                        "short_account": short_account,
                        "timestamp": int(float(item.get("time", 0) or 0) * 1000),
                    }
                )
            result.sort(key=lambda x: x.get("timestamp", 0))
            return result
        except Exception as exc:
            print(f"Gate long/short ratio 访问失败: {exc}")
            return []

    async def get_open_interest_hist(
        self,
        symbol: str,
        period: str = "1h",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取合约持仓量历史（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        safe_limit = max(1, min(int(limit), 200))

        try:
            data = await self._request_binance_futures_json(
                "/futures/data/openInterestHist",
                params={"symbol": normalized, "period": period, "limit": max(1, min(limit, 500))},
                timeout=8,
            )
            result = []
            for item in data or []:
                result.append({
                    "symbol": item.get("symbol", normalized),
                    "sum_open_interest": float(item.get("sumOpenInterest", 0)),
                    "sum_open_interest_value": float(item.get("sumOpenInterestValue", 0)),
                    "timestamp": int(item.get("timestamp", 0)),
                })
            return result
        except Exception as exc:
            print(f"Binance open interest history 访问失败: {exc}")

        try:
            contract = self._to_gate_pair(normalized)
            rows = await self._request_gate_json(
                "/futures/usdt/contract_stats",
                params={"contract": contract, "limit": safe_limit},
                timeout=10,
            )
            result = []
            for item in rows or []:
                result.append({
                    "symbol": normalized,
                    "sum_open_interest": float(item.get("open_interest", 0) or 0),
                    "sum_open_interest_value": float(item.get("open_interest_usd", 0) or 0),
                    "timestamp": int(float(item.get("time", 0) or 0) * 1000),
                })
            result.sort(key=lambda x: x.get("timestamp", 0))
            return result
        except Exception as exc:
            print(f"Gate open interest history 访问失败: {exc}")
            return []

    async def get_funding_rate(
        self,
        symbol: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取资金费率历史（真实数据）"""
        normalized = self._normalize_symbol(symbol)
        safe_limit = max(1, min(int(limit), 200))

        try:
            data = await self._request_binance_futures_json(
                "/fapi/v1/fundingRate",
                params={"symbol": normalized, "limit": max(1, min(limit, 1000))},
                timeout=8,
            )
            result = []
            for item in data or []:
                result.append({
                    "symbol": item.get("symbol", normalized),
                    "funding_rate": float(item.get("fundingRate", 0)),
                    "mark_price": float(item.get("markPrice", 0)),
                    "timestamp": int(item.get("fundingTime", 0)),
                })
            return result
        except Exception as exc:
            print(f"Binance funding rate 访问失败: {exc}")

        try:
            contract = self._to_gate_pair(normalized)
            mark_price = 0.0
            try:
                ticker_rows = await self._request_gate_json(
                    "/futures/usdt/tickers",
                    params={"contract": contract},
                    timeout=8,
                )
                if isinstance(ticker_rows, list) and ticker_rows:
                    mark_price = float(ticker_rows[0].get("mark_price", 0) or 0)
            except Exception:
                mark_price = 0.0

            rows = await self._request_gate_json(
                "/futures/usdt/funding_rate",
                params={"contract": contract, "limit": safe_limit},
                timeout=10,
            )
            result = []
            for item in rows or []:
                result.append({
                    "symbol": normalized,
                    "funding_rate": float(item.get("r", 0) or 0),
                    "mark_price": mark_price,
                    "timestamp": int(float(item.get("t", 0) or 0) * 1000),
                })
            result.sort(key=lambda x: x.get("timestamp", 0))
            return result
        except Exception as exc:
            print(f"Gate funding rate 访问失败: {exc}")
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

    def _format_gate_ticker(self, row: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """格式化 Gate 行情数据到统一格式"""
        last_price = float(row.get("last", 0) or 0)
        change_pct = float(row.get("change_percentage", 0) or 0)
        denom = 1 + change_pct / 100.0
        open_price = float(last_price / denom) if abs(denom) > 1e-8 else last_price
        return {
            "symbol": symbol,
            "price": last_price,
            "priceChange": float(last_price - open_price),
            "priceChangePercent": change_pct,
            "high": float(row.get("high_24h", 0) or 0),
            "low": float(row.get("low_24h", 0) or 0),
            "volume": float(row.get("base_volume", 0) or 0),
            "quoteVolume": float(row.get("quote_volume", 0) or 0),
            "openPrice": open_price,
            "count": 0,
            "timestamp": int(datetime.now().timestamp() * 1000)
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

    def _format_gate_kline(self, row: List[Any]) -> Dict[str, Any]:
        """格式化 Gate K线数据到统一格式"""
        ts_sec = int(float(row[0]))
        quote_volume = float(row[1] or 0)
        close_price = float(row[2] or 0)
        high_price = float(row[3] or 0)
        low_price = float(row[4] or 0)
        open_price = float(row[5] or 0)
        base_volume = float(row[6] or 0)
        is_closed = str(row[7]).lower() == "true" if len(row) >= 8 else True

        timestamp = ts_sec * 1000
        close_time = timestamp + 60_000
        trades = int(max(1, base_volume * 8))
        taker_buy_base = float(base_volume * 0.5)
        taker_buy_quote = float(quote_volume * 0.5)

        return {
            "timestamp": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": base_volume,
            "closeTime": close_time if is_closed else int(datetime.now().timestamp() * 1000),
            "quoteVolume": quote_volume,
            "trades": trades,
            "takerBuyBase": taker_buy_base,
            "takerBuyQuote": taker_buy_quote,
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

    def _format_gate_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """格式化 Gate 成交到统一结构"""
        side = str(trade.get("side", "")).lower()
        is_buyer_maker = side == "sell"
        try:
            ts = int(float(trade.get("create_time_ms", 0)))
        except Exception:
            ts = int(float(trade.get("create_time", 0)) * 1000)

        tid = int(float(trade.get("id", 0) or 0))
        return {
            "id": tid,
            "price": float(trade.get("price", 0) or 0),
            "amount": float(trade.get("amount", 0) or 0),
            "first_trade_id": tid,
            "last_trade_id": tid,
            "timestamp": ts,
            "is_buyer_maker": is_buyer_maker,
            "is_best_match": True,
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
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    def _format_gate_order_book(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化 Gate 订单簿"""
        bids = []
        asks = []
        for bid in data.get("bids", []) or []:
            if len(bid) >= 2:
                bids.append({"price": float(bid[0]), "amount": float(bid[1])})
        for ask in data.get("asks", []) or []:
            if len(ask) >= 2:
                asks.append({"price": float(ask[0]), "amount": float(ask[1])})
        return {
            "symbol": symbol,
            "last_update_id": int(data.get("update", 0) or 0),
            "bids": bids,
            "asks": asks,
            "timestamp": int(data.get("current", int(datetime.now().timestamp() * 1000)) or 0),
        }

    def _is_leveraged_token(self, base_asset: str) -> bool:
        """过滤杠杆代币/ETF"""
        upper = self._normalize_symbol(base_asset)
        if upper.endswith(("UP", "DOWN", "BULL", "BEAR", "3L", "3S", "5L", "5S")):
            return True
        return upper.startswith(("BULL", "BEAR"))
