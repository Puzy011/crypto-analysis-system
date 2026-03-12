import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np


class MockBinanceService:
    """模拟币安 API 服务（备用方案）"""

    POPULAR_USDT_SYMBOLS = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "TRXUSDT",
        "AVAXUSDT", "LINKUSDT", "DOTUSDT", "TONUSDT", "SHIBUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT",
        "ATOMUSDT", "XLMUSDT", "ETCUSDT", "HBARUSDT", "FILUSDT", "ICPUSDT", "APTUSDT", "ARBUSDT",
        "OPUSDT", "INJUSDT", "SUIUSDT", "NEARUSDT", "AAVEUSDT", "GRTUSDT", "VETUSDT", "ALGOUSDT",
        "MATICUSDT", "MANAUSDT", "SANDUSDT", "AXSUSDT", "EOSUSDT", "XMRUSDT", "RUNEUSDT", "EGLDUSDT",
        "KASUSDT", "STXUSDT", "IMXUSDT", "SEIUSDT", "TIAUSDT", "JUPUSDT", "WIFUSDT", "PEPEUSDT",
        "FLOKIUSDT", "BONKUSDT", "MEMEUSDT", "PYTHUSDT", "LDOUSDT", "RPLUSDT", "MKRUSDT", "CRVUSDT",
        "CVXUSDT", "DYDXUSDT", "GMXUSDT", "RDNTUSDT", "PENDLEUSDT", "KAVAUSDT", "ZECUSDT", "DASHUSDT",
        "COMPUSDT", "SNXUSDT", "1INCHUSDT", "CHZUSDT", "ENJUSDT", "BATUSDT", "ZILUSDT", "IOTAUSDT",
        "KSMUSDT", "QTUMUSDT", "NEOUSDT", "ONTUSDT", "ICXUSDT", "ZRXUSDT", "HOTUSDT", "OMGUSDT",
        "RVNUSDT", "CFXUSDT", "MINAUSDT", "ROSEUSDT", "COTIUSDT", "CELOUSDT", "ONEUSDT", "ANKRUSDT",
        "AUDIOUSDT", "KNCUSDT", "YFIUSDT", "FTMUSDT", "GALAUSDT", "LRCUSDT", "MASKUSDT", "BLURUSDT",
        "ACHUSDT", "ARPAUSDT", "PEOPLEUSDT", "IDUSDT", "MAGICUSDT", "PROMUSDT", "API3USDT", "ENSUSDT",
        "SSVUSDT", "SXPUSDT", "SKLUSDT", "STORJUSDT", "ILVUSDT", "FETUSDT", "OCEANUSDT", "RNDRUSDT",
        "WLDUSDT", "STRKUSDT", "AEVOUSDT", "ALTUSDT", "PORTALUSDT", "ENAUSDT", "ETHFIUSDT", "ZROUSDT",
        "IOUSDT", "OMUSDT", "NOTUSDT", "BOMEUSDT", "TURBOUSDT", "XAIUSDT", "ORDIUSDT", "SATSUSDT",
        "1000SATSUSDT", "JTOUSDT", "JOEUSDT", "TRBUSDT", "LPTUSDT", "BANDUSDT", "NTRNUSDT", "CYBERUSDT",
        "HOOKUSDT", "HIFIUSDT", "ARKMUSDT", "DYMUSDT", "MANTAUSDT", "NFPUSDT", "PIXELUSDT", "ACEUSDT",
        "AIUSDT", "XVGUSDT", "RSRUSDT", "MTLUSDT", "BALUSDT", "BNTUSDT", "C98USDT", "CELRUSDT",
        "CTSIUSDT", "DUSKUSDT", "FIDAUSDT", "FLMUSDT", "HFTUSDT", "JSTUSDT", "KEYUSDT", "LEVERUSDT",
        "LITUSDT", "MDTUSDT", "NKNUSDT", "OGNUSDT", "PERPUSDT", "REQUSDT", "RIFUSDT", "TLMUSDT",
        "ZENUSDT", "WOOUSDT", "PHBUSDT", "LINAUSDT", "GALUSDT", "TRUUSDT", "HIGHUSDT", "CTKUSDT",
        "GLMRUSDT", "ASTRUSDT", "DARUSDT", "RAREUSDT", "ALICEUSDT", "SFPUSDT", "STGUSDT", "SUSHIUSDT",
        "XECUSDT", "BICOUSDT", "SPELLUSDT", "PLAUSDT", "POLSUSDT", "RAYUSDT", "USTCUSDT", "USTUSDT",
    ]

    @staticmethod
    def _stable_int(token: str) -> int:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return int(digest[:12], 16)

    @staticmethod
    def _rng_for_symbol(symbol: str, bucket_seconds: int = 60) -> np.random.Generator:
        bucket = int(datetime.now().timestamp() // max(1, bucket_seconds))
        seed = (MockBinanceService._stable_int(symbol.upper()) + bucket) % (2**32 - 1)
        return np.random.default_rng(seed)

    @staticmethod
    def get_ticker(symbol: str) -> Dict[str, Any]:
        """获取单个交易对的实时行情（模拟数据）"""
        normalized = symbol.upper()
        base_price = MockBinanceService._get_base_price(normalized)
        rng = MockBinanceService._rng_for_symbol(f"ticker:{normalized}", bucket_seconds=20)

        drift = float(rng.normal(0.0, 0.008))
        current_price = max(0.0000001, base_price * (1.0 + drift))
        spread = float(abs(rng.normal(0.006, 0.0025)))
        high = current_price * (1.0 + spread)
        low = current_price * max(0.0000001, 1.0 - spread)
        volume = float(rng.uniform(15_000, 3_000_000))

        return {
            "symbol": normalized,
            "price": float(current_price),
            "priceChange": float(current_price - base_price),
            "priceChangePercent": float(drift * 100),
            "high": float(high),
            "low": float(low),
            "volume": volume,
            "quoteVolume": float(volume * current_price),
            "openPrice": float(base_price),
            "count": int(rng.integers(1500, 300000)),
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    @staticmethod
    def get_tickers(symbols: List[str]) -> List[Dict[str, Any]]:
        """获取多个交易对的实时行情（模拟数据）"""
        return [MockBinanceService.get_ticker(symbol) for symbol in symbols]

    @staticmethod
    def get_trading_symbols(
        quote_asset: str = "USDT",
        limit: int = 200,
        include_leveraged: bool = False,
    ) -> List[Dict[str, Any]]:
        """获取可交易交易对（模拟数据）"""
        normalized_quote = (quote_asset or "USDT").upper()
        if normalized_quote != "USDT":
            return []

        symbols = MockBinanceService.POPULAR_USDT_SYMBOLS[: max(1, min(int(limit), len(MockBinanceService.POPULAR_USDT_SYMBOLS)))]
        result: List[Dict[str, Any]] = []
        for idx, symbol in enumerate(symbols):
            base_asset = symbol.replace("USDT", "")
            # 模拟成交额：按序递减，保留排序稳定性
            quote_volume = float((len(symbols) - idx) * 1_400_000)
            result.append(
                {
                    "symbol": symbol,
                    "baseAsset": base_asset,
                    "quoteAsset": "USDT",
                    "status": "TRADING",
                    "quoteVolume": quote_volume,
                }
            )
        return result

    @staticmethod
    def get_klines(
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取K线数据（模拟数据）"""
        normalized = symbol.upper()
        base_price = MockBinanceService._get_base_price(normalized)
        rng = MockBinanceService._rng_for_symbol(f"kline:{normalized}:{interval}:{limit}", bucket_seconds=120)

        now = datetime.now()
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

        # 按币种设置温和趋势，避免每次完全随机
        trend_seed = MockBinanceService._stable_int(normalized) % 1000
        drift_per_bar = ((trend_seed / 1000.0) - 0.5) * 0.0018
        vol_scale = 0.004 + (trend_seed % 13) / 5000.0

        prices = [base_price]
        for _ in range(1, limit):
            noise = float(rng.normal(0.0, vol_scale))
            ret = drift_per_bar + noise
            prices.append(max(0.0000001, prices[-1] * (1.0 + ret)))

        klines = []
        for i in range(limit):
            timestamp = int((now - delta * (limit - i)).timestamp() * 1000)
            open_p = prices[i - 1] if i > 0 else prices[i]
            close_p = prices[i]
            wick = abs(float(rng.normal(0.0, vol_scale * 1.3)))
            high_p = max(open_p, close_p) * (1.0 + wick)
            low_p = min(open_p, close_p) * max(0.0000001, 1.0 - wick)
            volume = float(rng.uniform(2_500, 260_000))
            taker_ratio = float(np.clip(rng.normal(0.5, 0.1), 0.2, 0.8))

            klines.append(
                {
                    "timestamp": timestamp,
                    "open": float(open_p),
                    "high": float(high_p),
                    "low": float(low_p),
                    "close": float(close_p),
                    "volume": volume,
                    "closeTime": timestamp + int(delta.total_seconds() * 1000),
                    "quoteVolume": float(volume * close_p),
                    "trades": int(rng.integers(120, 4200)),
                    "takerBuyBase": float(volume * taker_ratio),
                    "takerBuyQuote": float(volume * close_p * taker_ratio),
                }
            )
        return klines

    @staticmethod
    def _get_base_price(symbol: str) -> float:
        """获取基础价格"""
        symbol = symbol.upper()
        price_map = {
            "BTCUSDT": 69000.0,
            "ETHUSDT": 3500.0,
            "BNBUSDT": 590.0,
            "SOLUSDT": 160.0,
            "XRPUSDT": 0.58,
            "DOGEUSDT": 0.18,
            "ADAUSDT": 0.52,
            "TRXUSDT": 0.12,
            "AVAXUSDT": 38.0,
            "LINKUSDT": 18.5,
            "DOTUSDT": 8.2,
            "TONUSDT": 6.3,
            "SHIBUSDT": 0.000023,
            "LTCUSDT": 95.0,
            "BCHUSDT": 430.0,
            "UNIUSDT": 11.2,
            "ATOMUSDT": 11.3,
            "XLMUSDT": 0.12,
            "ETCUSDT": 30.0,
            "HBARUSDT": 0.11,
            "FILUSDT": 8.2,
            "ICPUSDT": 12.0,
            "APTUSDT": 10.5,
            "ARBUSDT": 1.5,
            "OPUSDT": 3.0,
            "INJUSDT": 40.0,
            "SUIUSDT": 1.9,
            "NEARUSDT": 5.6,
            "AAVEUSDT": 120.0,
            "PEPEUSDT": 0.000012,
            "FLOKIUSDT": 0.00017,
            "BONKUSDT": 0.000027,
            "WIFUSDT": 2.1,
            "JUPUSDT": 1.2,
            "SEIUSDT": 0.8,
            "TIAUSDT": 14.0,
            "FETUSDT": 1.5,
            "RNDRUSDT": 7.5,
            "WLDUSDT": 7.0,
            "STRKUSDT": 2.0,
            "TRBUSDT": 90.0,
            "1000SATSUSDT": 0.00032,
            "SATSUSDT": 0.0000008,
            "TURBOUSDT": 0.005,
            "BOMEUSDT": 0.01,
            "NOTUSDT": 0.016,
            "GALAUSDT": 0.05,
            "FTMUSDT": 0.9,
            "MATICUSDT": 1.0,
        }
        if symbol in price_map:
            return price_map[symbol]

        seed = MockBinanceService._stable_int(symbol)
        buckets = [
            (0.000004, 0.005),
            (0.006, 0.09),
            (0.1, 0.9),
            (1.0, 9.0),
            (10.0, 90.0),
            (100.0, 900.0),
        ]
        low, high = buckets[seed % len(buckets)]
        ratio = ((seed // 97) % 1_000_000) / 1_000_000.0
        return float(low + (high - low) * ratio)


# 全局实例
_mock_binance_service = None


def get_mock_binance_service() -> MockBinanceService:
    """获取模拟币安服务单例"""
    global _mock_binance_service
    if _mock_binance_service is None:
        _mock_binance_service = MockBinanceService()
    return _mock_binance_service

