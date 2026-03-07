"""
综合舆情分析 API - FinBERT 风格增强版
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

from app.services.comprehensive_sentiment_service import (
    get_comprehensive_sentiment_service
)
from app.services.mock_binance_service import get_mock_binance_service
from app.services.enhanced_sentiment_service import get_enhanced_sentiment_service


router = APIRouter(prefix="/api/comprehensive-sentiment", tags=["综合舆情分析"])


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
        sent_service = get_enhanced_sentiment_service()
        mock_service = get_mock_binance_service()
        
        # 生成新闻
        news_list = sent_service.generate_mock_news(symbol, count=news_count)
        
        # 用综合舆情分析重新分析每条新闻
        for news in news_list:
            enhanced_analysis = comp_service.analyze_financial_sentiment(news["title"])
            news["sentiment_analysis"] = enhanced_analysis
        
        # 获取价格数据
        klines = mock_service.get_klines(
            symbol=symbol,
            interval="1h",
            limit=500
        )
        
        df = pd.DataFrame(klines)
        df["timestamp"] = df["time"]
        
        # 分析新闻价格影响
        result = comp_service.analyze_news_price_impact(
            symbol=symbol,
            news_list=news_list,
            price_data=df
        )
        
        return {
            "symbol": symbol,
            **result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full-analysis/{symbol}")
async def get_full_sentiment_analysis(
    symbol: str = "BTCUSDT"
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
        sent_service = get_enhanced_sentiment_service()
        mock_service = get_mock_binance_service()
        
        # 1. 获取基础舆情指数
        sentiment_index = sent_service.calculate_sentiment_index(symbol)
        
        # 2. 获取新闻
        news_list = sent_service.generate_mock_news(symbol, count=20)
        
        # 3. 用综合舆情分析新闻
        all_news_texts = [news["title"] for news in news_list]
        
        # 4. 提取关键词 (TF-IDF)
        tfidf_keywords = comp_service.extract_keywords_tfidf(all_news_texts, top_n=15)
        
        # 5. 提取关键词 (TextRank) - 从第一条新闻
        textrank_keywords = []
        if news_list:
            textrank_keywords = comp_service.extract_keywords_textrank(
                news_list[0]["title"], 
                top_n=10
            )
        
        # 6. 增强分析每条新闻
        for news in news_list:
            enhanced_analysis = comp_service.analyze_financial_sentiment(news["title"])
            news["enhanced_sentiment"] = enhanced_analysis
        
        return {
            "symbol": symbol,
            "sentiment_index": sentiment_index,
            "news_count": len(news_list),
            "news": news_list[:10],  # 返回前10条
            "keywords": {
                "tfidf": [{"word": word, "score": float(score)} for word, score in tfidf_keywords],
                "textrank": [{"word": word, "score": float(score)} for word, score in textrank_keywords]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

