"""
综合舆情分析 API - FinBERT 风格增强版
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

from app.services.comprehensive_sentiment_service import (
    get_comprehensive_sentiment_service
)
from app.services.sentiment_scheduler_service import (
    get_sentiment_scheduler_service,
)
from app.services.binance_service import BinanceService


router = APIRouter(prefix="/api/comprehensive-sentiment", tags=["综合舆情分析"])
binance_service = BinanceService()


class TextAnalysisRequest(BaseModel):
    text: str


@router.post("/analyze-financial")
async def analyze_financial_text(
    request: TextAnalysisRequest
):
    """
    FinBERT 风格金融文本情感分析
    """
    try:
        service = get_comprehensive_sentiment_service()
        result = service.analyze_financial_sentiment(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords/tfidf")
async def extract_keywords_tfidf(
    texts: List[str]
):
    """
    TF-IDF 关键词提取
    """
    try:
        service = get_comprehensive_sentiment_service()
        keywords = service.extract_keywords_tfidf(texts, top_n=15)
        return {
            "keywords": [{"word": word, "score": float(score)} for word, score in keywords],
            "total_texts": len(texts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords/textrank")
async def extract_keywords_textrank(
    text: str
):
    """
    TextRank 关键词提取
    """
    try:
        service = get_comprehensive_sentiment_service()
        keywords = service.extract_keywords_textrank(text, top_n=15)
        return {
            "keywords": [{"word": word, "score": float(score)} for word, score in keywords],
            "text_length": len(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news-impact/{symbol}")
async def analyze_news_price_impact(
    symbol: str = "BTCUSDT",
    news_count: int = Query(20, ge=5, le=100, description="分析的新闻数量")
):
    """
    新闻-价格关联分析
    
    分析新闻发布前后的价格变化，量化新闻影响
    """
    try:
        comp_service = get_comprehensive_sentiment_service()

        # 获取真实新闻（不可用时自动降级）
        news_list = comp_service.fetch_market_news(symbol, limit=news_count, hours=96)

        # 逐条分析情绪
        for news in news_list:
            enhanced_analysis = comp_service.analyze_financial_sentiment(
                f"{news.get('title', '')} {news.get('content', '')}"
            )
            news["sentiment_analysis"] = enhanced_analysis
        
        # 获取价格数据（Binance 失败会自动降级到模拟）
        klines = await binance_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=500
        )
        
        df = pd.DataFrame(klines)
        if "timestamp" not in df.columns:
            raise ValueError("价格数据缺少 timestamp 字段")
        
        # 分析新闻价格影响
        result = comp_service.analyze_news_price_impact(
            symbol=symbol,
            news_list=news_list,
            price_data=df
        )
        
        return {
            "symbol": symbol,
            **result,
            "news_preview": news_list[:5],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full-analysis/{symbol}")
async def get_full_sentiment_analysis(
    symbol: str = "BTCUSDT",
    news_count: int = Query(30, ge=10, le=120, description="新闻数量"),
    forecast_hours: int = Query(24, ge=1, le=72, description="舆情趋势预测小时数")
):
    """
    获取完整的综合舆情分析
    
    包含:
    - 基础舆情指数
    - 恐惧贪婪指数
    - FinBERT 风格新闻分析
    - 关键词提取
    - 新闻-价格影响分析
    """
    try:
        comp_service = get_comprehensive_sentiment_service()
        scheduler_service = get_sentiment_scheduler_service()

        # 1. 获取新闻（真实 + 自动降级）
        news_list = comp_service.fetch_market_news(symbol, limit=news_count, hours=120)

        # 2. 分析新闻情绪
        for news in news_list:
            enhanced_analysis = comp_service.analyze_financial_sentiment(
                f"{news.get('title', '')} {news.get('content', '')}"
            )
            news["enhanced_sentiment"] = enhanced_analysis
            news["sentiment_analysis"] = enhanced_analysis

        # 3. 构建综合舆情指数
        sentiment_index = comp_service.build_sentiment_index(symbol, news_list)
        trend_forecast = comp_service.forecast_sentiment_trend(
            symbol=symbol,
            sentiment_index=sentiment_index,
            news_list=news_list,
            hours_ahead=forecast_hours,
        )

        # 4. 关键词
        all_news_texts = [news["title"] for news in news_list]
        tfidf_keywords = comp_service.extract_keywords_tfidf(all_news_texts, top_n=15)

        # 5. TextRank（取最新一条）
        textrank_keywords = []
        if news_list:
            textrank_keywords = comp_service.extract_keywords_textrank(
                news_list[0]["title"], 
                top_n=10
            )

        # 6. 新闻价格影响
        klines = await binance_service.get_klines(symbol=symbol, interval="1h", limit=500)
        df = pd.DataFrame(klines)
        if "timestamp" not in df.columns:
            raise ValueError("价格数据缺少 timestamp 字段")
        impact_report = comp_service.analyze_news_price_impact(
            symbol=symbol,
            news_list=news_list,
            price_data=df
        )
        multi_platform_snapshot = await scheduler_service.get_or_collect_latest(
            symbol=symbol,
            freshness_seconds=20 * 60,
        )
        time_analysis = scheduler_service.analyze_timeline(symbol)
        
        return {
            "symbol": symbol,
            "sentiment_index": sentiment_index,
            "trend_forecast": trend_forecast,
            "news_count": len(news_list),
            "news": news_list[:10],
            "keywords": {
                "tfidf": [{"word": word, "score": float(score)} for word, score in tfidf_keywords],
                "textrank": [{"word": word, "score": float(score)} for word, score in textrank_keywords]
            },
            "news_price_impact": impact_report,
            "multi_platform": multi_platform_snapshot,
            "time_analysis": time_analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/{symbol}")
async def collect_multi_platform_sentiment(
    symbol: str = "BTCUSDT",
):
    """
    手动触发一次多平台舆情采集
    """
    try:
        scheduler_service = get_sentiment_scheduler_service()
        snapshot = await scheduler_service.collect_once(symbol=symbol, force_refresh=True)
        timeline_analysis = scheduler_service.analyze_timeline(symbol)
        return {
            "symbol": symbol.upper(),
            "snapshot": snapshot,
            "time_analysis": timeline_analysis,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-platform/{symbol}")
async def get_multi_platform_snapshot(
    symbol: str = "BTCUSDT",
    freshness_seconds: int = Query(1200, ge=60, le=7200, description="最大可接受数据新鲜度(秒)"),
):
    """
    获取多平台舆情快照（新闻+Reddit+公告）
    """
    try:
        scheduler_service = get_sentiment_scheduler_service()
        snapshot = await scheduler_service.get_or_collect_latest(
            symbol=symbol,
            freshness_seconds=freshness_seconds,
        )
        return {
            "symbol": symbol.upper(),
            "multi_platform": snapshot,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{symbol}")
async def get_multi_platform_timeline(
    symbol: str = "BTCUSDT",
    hours: int = Query(24, ge=1, le=240, description="时间窗口(小时)"),
    limit: int = Query(240, ge=10, le=2000, description="最多返回点数"),
):
    """
    获取多平台舆情时间线与趋势分析
    """
    try:
        scheduler_service = get_sentiment_scheduler_service()
        if not scheduler_service.get_timeline(symbol, hours=hours, limit=1):
            await scheduler_service.collect_once(symbol=symbol, force_refresh=True)

        timeline = scheduler_service.get_timeline(symbol=symbol, hours=hours, limit=limit)
        analysis = scheduler_service.analyze_timeline(symbol=symbol)
        return {
            "symbol": symbol.upper(),
            "hours": hours,
            "points": len(timeline),
            "timeline": timeline,
            "time_analysis": analysis,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
async def get_scheduler_status():
    """
    获取舆情调度器运行状态
    """
    try:
        scheduler_service = get_sentiment_scheduler_service()
        return {
            "status": scheduler_service.get_scheduler_status(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend-forecast/{symbol}")
async def get_sentiment_trend_forecast(
    symbol: str = "BTCUSDT",
    news_count: int = Query(30, ge=10, le=120, description="新闻数量"),
    forecast_hours: int = Query(24, ge=1, le=72, description="舆情趋势预测小时数"),
):
    """
    获取舆情趋势预测（未来 1-72 小时）
    """
    try:
        comp_service = get_comprehensive_sentiment_service()
        news_list = comp_service.fetch_market_news(symbol, limit=news_count, hours=120)
        for news in news_list:
            enhanced_analysis = comp_service.analyze_financial_sentiment(
                f"{news.get('title', '')} {news.get('content', '')}"
            )
            news["enhanced_sentiment"] = enhanced_analysis
            news["sentiment_analysis"] = enhanced_analysis

        sentiment_index = comp_service.build_sentiment_index(symbol, news_list)
        trend_forecast = comp_service.forecast_sentiment_trend(
            symbol=symbol,
            sentiment_index=sentiment_index,
            news_list=news_list,
            hours_ahead=forecast_hours,
        )

        return {
            "symbol": symbol,
            "sentiment_index": sentiment_index,
            "trend_forecast": trend_forecast,
            "news_count": len(news_list),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

