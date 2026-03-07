"""
主题建模 API - LDA 风格
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.services.topic_modeling_service import get_topic_modeling_service
from app.services.enhanced_sentiment_service import get_enhanced_sentiment_service


router = APIRouter(prefix="/api/topic-modeling", tags=["主题建模"])


class TopicModelingRequest(BaseModel):
    texts: List[str]
    num_topics: int = 5
    num_words: int = 10


@router.post("/lda")
async def run_lda_topic_modeling(
    request: TopicModelingRequest
):
    """
    运行 LDA 主题建模
    """
    try:
        service = get_topic_modeling_service()
        result = service.simple_lda_topic_modeling(
            texts=request.texts,
            num_topics=request.num_topics,
            num_words=request.num_words
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-themes")
async def extract_themes(
    texts: List[str],
    top_n: int = Query(5, ge=1, le=10, description="返回主题数量")
):
    """
    从文本中提取主题
    """
    try:
        service = get_topic_modeling_service()
        themes = service.extract_themes(texts, top_n=top_n)
        return {
            "themes": themes,
            "total_texts": len(texts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-events")
async def analyze_event_types(
    text: str
):
    """
    分析文本中的事件类型
    """
    try:
        service = get_topic_modeling_service()
        result = service.analyze_event_types(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/from-news/{symbol}")
async def analyze_news_topics(
    symbol: str = "BTCUSDT",
    news_count: int = Query(20, ge=5, le=100, description="分析的新闻数量")
):
    """
    从新闻中分析主题
    """
    try:
        topic_service = get_topic_modeling_service()
        sent_service = get_enhanced_sentiment_service()
        
        # 生成新闻
        news_list = sent_service.generate_mock_news(symbol, count=news_count)
        
        # 提取新闻文本
        news_texts = [news["title"] for news in news_list]
        
        # 主题建模
        lda_result = topic_service.simple_lda_topic_modeling(
            texts=news_texts,
            num_topics=5,
            num_words=10
        )
        
        # 提取主题
        themes = topic_service.extract_themes(news_texts, top_n=5)
        
        # 分析每条新闻的事件类型
        news_with_events = []
        for news in news_list:
            event_analysis = topic_service.analyze_event_types(news["title"])
            news_with_events.append({
                **news,
                "event_analysis": event_analysis
            })
        
        return {
            "symbol": symbol,
            "news_count": len(news_list),
            "lda_topic_modeling": lda_result,
            "key_themes": themes,
            "news_with_events": news_with_events[:10],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

