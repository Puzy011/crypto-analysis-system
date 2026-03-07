from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import (
    market, prediction, whale, sentiment, advanced,
    realtime_sentiment, prediction_backtest, realtime_prediction,
    advanced_prediction, enhanced_sentiment, whale_analysis,
    complete_ta, enhanced_backtest, comprehensive_sentiment,
    topic_modeling
)
from app.core.config import settings
from app.services.sentiment_scheduler_service import get_sentiment_scheduler_service

app = FastAPI(
    title="Crypto Analysis System API",
    description="虚拟货币行情分析系统 - API (增强版)",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(market.router, prefix="/api/market", tags=["市场行情"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["AI预测"])
app.include_router(whale.router, prefix="/api/whale", tags=["庄家分析"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["舆情分析"])
app.include_router(advanced.router, prefix="/api/advanced", tags=["高级功能"])
app.include_router(realtime_sentiment.router, prefix="/api/realtime-sentiment", tags=["实时舆情监控"])
app.include_router(prediction_backtest.router, prefix="/api/prediction-backtest", tags=["预测回测验证"])
app.include_router(realtime_prediction.router, prefix="/api/realtime-prediction", tags=["实时预测更新"])

# 新增强功能路由
app.include_router(advanced_prediction.router)
app.include_router(enhanced_sentiment.router)
app.include_router(whale_analysis.router)
app.include_router(complete_ta.router)
app.include_router(enhanced_backtest.router)
app.include_router(comprehensive_sentiment.router)
app.include_router(topic_modeling.router)


@app.on_event("startup")
async def startup_event():
    scheduler = get_sentiment_scheduler_service()
    await scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    scheduler = get_sentiment_scheduler_service()
    await scheduler.stop()

@app.get("/")
async def root():
    return {
        "message": "Crypto Analysis System API (Enhanced)",
        "version": "2.0.0",
        "description": "基于 GitHub 优秀项目增强的加密货币分析系统",
        "features": [
            "高级预测模型 (XGBoost, LightGBM, Prophet, Random Forest)",
            "增强舆情分析 (FinBERT 风格)",
            "巨鲸/庄家分析 (OrderFlow 风格)",
            "实时舆情监控",
            "预测回测验证",
            "实时预测更新"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
