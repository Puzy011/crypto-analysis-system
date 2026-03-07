"""
增强舆情分析 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.enhanced_sentiment_service import (
    get_enhanced_sentiment_service
)


router = APIRouter(prefix="/api/enhanced-sentiment", tags=["增强舆情"])


class TextAnalysisRequest(BaseModel):
    text: str


@router.post("/analyze-text")
async def analyze_text_sentiment(
    request: TextAnalysisRequest
):
    """
    分析单条文本的情感
    """
    try:
        sentiment_service = get_enhanced_sentiment_service()
        result = sentiment_service.analyze_text_sentiment(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/{symbol}")
async def get_sentiment_index(
    symbol: str = "BTCUSDT",
    news_count: int = Query(20, ge=5, le=100, description="分析的新闻数量")
):
    """
    获取综合舆情指数
    """
    try:
        sentiment_service = get_enhanced_sentiment_service()
        
        # 生成模拟新闻
        news_list = sentiment_service.generate_mock_news(symbol, count=news_count)
        
        # 计算舆情指数
        index = sentiment_service.calculate_sentiment_index(symbol, news_list)
        
        return index
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/{symbol}")
async def get_sentiment_news(
    symbol: str = "BTCUSDT",
    count: int = Query(20, ge=5, le=100, description="新闻数量")
):
    """
    获取带情感分析的新闻列表
    """
    try:
        sentiment_service = get_enhanced_sentiment_service()
        news_list = sentiment_service.generate_mock_news(symbol, count=count)
        return {
            "symbol": symbol,
            "news_count": len(news_list),
            "news": news_list,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{symbol}")
async def get_sentiment_alerts(
    symbol: str = "BTCUSDT"
):
    """
    获取舆情预警
    """
    try:
        sentiment_service = get_enhanced_sentiment_service()
        
        # 先计算舆情指数
        news_list = sentiment_service.generate_mock_news(symbol, count=20)
        index = sentiment_service.calculate_sentiment_index(symbol, news_list)
        
        # 检查预警
        alerts = sentiment_service.check_sentiment_alerts(symbol, index)
        
        return {
            "symbol": symbol,
            "sentiment_index": index,
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}")
async def get_sentiment_history(
    symbol: str = "BTCUSDT",
    limit: int = Query(100, ge=1, le=1000, description="历史记录数量")
):
    """
    获取舆情历史数据
    """
    try:
        sentiment_service = get_enhanced_sentiment_service()
        history = sentiment_service.get_sentiment_history(symbol, limit=limit)
        return {
            "symbol": symbol,
            "history_count": len(history),
            "history": history,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fear-greed")
async def get_fear_greed_index(
    symbol: str = Query("BTCUSDT", description="交易对")
):
    """
    获取恐惧贪婪指数（便捷接口）
    """
    try:
        sentiment_service = get_enhanced_sentiment_service()
        news_list = sentiment_service.generate_mock_news(symbol, count=20)
        index = sentiment_service.calculate_sentiment_index(symbol, news_list)
        
        return {
            "symbol": symbol,
            "fear_greed_index": index["fear_greed_index"],
            "market_state": index["market_state"],
            "market_state_emoji": index["market_state_emoji"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

