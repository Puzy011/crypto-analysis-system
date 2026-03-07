from fastapi import APIRouter, HTTPException
from app.services.sentiment_service import SentimentAnalysisService

router = APIRouter()
sentiment_service = SentimentAnalysisService()


@router.get("/news/{keyword}")
async def get_news_sentiment(keyword: str = "crypto"):
    """获取新闻舆情分析"""
    try:
        analysis = sentiment_service.analyze_news_sentiment(keyword)
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/{keyword}")
async def get_social_sentiment(keyword: str = "crypto"):
    """获取社交媒体舆情分析"""
    try:
        analysis = sentiment_service.analyze_social_sentiment(keyword)
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fear-greed")
async def get_fear_greed_index():
    """获取恐慌贪婪指数"""
    try:
        index = sentiment_service.get_fear_greed_index()
        return {
            "success": True,
            "data": index
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "sentiment"
    }
