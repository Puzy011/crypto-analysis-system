import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from app.services.binance_service import BinanceService
from app.services.technical_service import TechnicalIndicatorsService

router = APIRouter()
binance_service = BinanceService()
tech_service = TechnicalIndicatorsService()

DEFAULT_MARKET_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "LTCUSDT", "BCHUSDT", "TRXUSDT", "ATOMUSDT", "MATICUSDT",
    "UNIUSDT", "ETCUSDT", "NEARUSDT", "AAVEUSDT", "FILUSDT",
    "RIVERUSDT",
]


def _normalize_symbol_list(raw: Optional[str], default_quote: str = "USDT") -> List[str]:
    """
    将 symbols 字符串规范化为交易对列表:
    - 支持逗号/空格/分号分隔
    - 支持直接传 BTC/ETH（自动补 USDT）
    - 自动去重
    """
    if not raw:
        return []

    normalized_quote = (default_quote or "USDT").upper()
    parts = [p.strip().upper() for p in re.split(r"[,\s;]+", raw) if p.strip()]
    result: List[str] = []
    seen = set()
    quote_suffixes = ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "BTC", "ETH")

    for item in parts:
        symbol = item
        if not item.endswith(quote_suffixes):
            symbol = f"{item}{normalized_quote}"
        if symbol not in seen:
            seen.add(symbol)
            result.append(symbol)
    return result

@router.get("/ticker/{symbol}")
async def get_ticker(
    symbol: str = "BTCUSDT",
    market_type: str = Query("spot", description="spot 或 futures"),
):
    """获取指定交易对的实时行情"""
    try:
        ticker = await binance_service.get_ticker(symbol.upper(), market_type=market_type)
        return {
            "success": True,
            "data": ticker
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickers")
async def get_tickers(
    symbols: Optional[str] = Query(
        None,
        description="交易对列表，支持逗号分隔；可传 BTC,ETH 自动补成 BTCUSDT,ETHUSDT",
    ),
    limit: int = Query(20, ge=1, le=200, description="未指定 symbols 时返回数量"),
    quote_asset: str = Query("USDT", description="未指定 symbols 时按该计价币筛选"),
    market_type: str = Query("spot", description="spot 或 futures"),
):
    """
    获取多个交易对的实时行情

    - 传 symbols: 按传入交易对查询
    - 不传 symbols: 自动返回主流交易对（按成交额）
    """
    try:
        symbol_list = _normalize_symbol_list(symbols, default_quote=quote_asset)
        if not symbol_list:
            ranked_symbols = await binance_service.get_trading_symbols(
                quote_asset=quote_asset,
                limit=max(limit, len(DEFAULT_MARKET_SYMBOLS)),
                include_leveraged=False,
                market_type=market_type,
            )
            if ranked_symbols:
                symbol_list = [item["symbol"] for item in ranked_symbols[:limit]]
            else:
                symbol_list = DEFAULT_MARKET_SYMBOLS[:limit]

        # 防止一次请求过大
        symbol_list = symbol_list[:200]
        tickers = await binance_service.get_tickers(symbol_list, market_type=market_type)
        return {
            "success": True,
            "data": tickers,
            "count": len(tickers),
            "symbols": symbol_list,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_symbols(
    quote_asset: str = Query("USDT", description="计价币，如 USDT"),
    limit: int = Query(200, ge=1, le=500, description="返回数量上限"),
    search: Optional[str] = Query(None, description="按 symbol/baseAsset 模糊过滤"),
    include_leveraged: bool = Query(False, description="是否包含杠杆代币"),
    market_type: str = Query("spot", description="spot 或 futures"),
):
    """获取可查询交易对列表（按 24h 成交额排序）"""
    try:
        symbols = await binance_service.get_trading_symbols(
            quote_asset=quote_asset,
            limit=500,
            include_leveraged=include_leveraged,
            market_type=market_type,
        )
        if search:
            kw = search.strip().upper()
            symbols = [
                s
                for s in symbols
                if kw in str(s.get("symbol", "")).upper()
                or kw in str(s.get("baseAsset", "")).upper()
            ]
        symbols = symbols[:limit]
        return {
            "success": True,
            "data": symbols,
            "count": len(symbols),
            "quote_asset": quote_asset.upper(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100,
    market_type: str = Query("spot", description="spot 或 futures"),
):
    """获取K线数据"""
    try:
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit,
            market_type=market_type,
        )
        return {
            "success": True,
            "data": klines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{symbol}/indicators")
async def get_klines_with_indicators(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 200,
    market_type: str = Query("spot", description="spot 或 futures"),
):
    """获取K线数据及技术指标"""
    try:
        klines = await binance_service.get_klines(
            symbol.upper(),
            interval,
            limit,
            market_type=market_type,
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 计算技术指标
        indicators = tech_service.calculate_all_indicators(df)
        
        return {
            "success": True,
            "data": {
                "klines": klines,
                "indicators": indicators
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "market"
    }
