from fastapi import APIRouter, HTTPException
from app.services.realtime_sentiment_service import get_realtime_sentiment_service
from app.services.enhanced_sentiment_service import EnhancedSentimentService
from datetime import datetime

router = APIRouter()

# 服务实例
realtime_service = get_realtime_sentiment_service()
enhanced_service = EnhancedSentimentService()


@router.post("/monitor/{keyword}")
async def monitor_sentiment(keyword: str = "crypto"):
    """监控并更新舆情数据"""
    try:
        # 获取增强版舆情分析
        sentiment_data = enhanced_service.analyze_full_sentiment(keyword)
        
        # 更新实时舆情服务
        result = realtime_service.update_sentiment(keyword, sentiment_data)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{keyword}")
async def get_sentiment_status(keyword: str = "crypto"):
    """获取实时舆情状态"""
    try:
        status = realtime_service.get_realtime_status(keyword)
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{keyword}")
async def get_sentiment_history(keyword: str = "crypto", limit: int = 100):
    """获取历史舆情数据"""
    try:
        history = realtime_service.get_history(keyword, limit)
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{keyword}")
async def get_sentiment_alerts(
    keyword: str = None,
    level: str = None,
    limit: int = 50
):
    """获取舆情预警历史"""
    try:
        alerts = realtime_service.get_alerts(keyword, level, limit)
        return {
            "success": True,
            "data": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{keyword}")
async def get_sentiment_summary(keyword: str = "crypto"):
    """获取舆情摘要"""
    try:
        summary = realtime_service.get_summary(keyword)
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization/{keyword}")
async def get_sentiment_visualization(keyword: str = "crypto", limit: int = 100):
    """获取舆情历史数据可视化数据（用于图表展示）"""
    try:
        history = realtime_service.get_history(keyword, limit)
        
        if not history:
            return {
                "success": True,
                "data": {
                    "keyword": keyword,
                    "timestamps": [],
                    "overall_scores": [],
                    "news_scores": [],
                    "social_scores": [],
                    "alerts": []
                }
            }
        
        # 提取可视化数据
        timestamps = []
        overall_scores = []
        news_scores = []
        social_scores = []
        
        for record in history:
            timestamps.append(record.get("datetime"))
            data = record.get("data", {})
            overall_scores.append(data.get("overall_score", {}).get("score", 50))
            news_scores.append(data.get("news_sentiment", {}).get("sentiment_score", 0))
            social_scores.append(data.get("social_sentiment", {}).get("overall_sentiment", 0))
        
        # 获取同期预警
        alerts = realtime_service.get_alerts(keyword=keyword, limit=20)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "timestamps": timestamps,
                "overall_scores": overall_scores,
                "news_scores": news_scores,
                "social_scores": social_scores,
                "alerts": alerts,
                "data_points": len(history)
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
        "service": "realtime_sentiment",
        "timestamp": int(datetime.now().timestamp() * 1000)
    }
