import pandas as pd
import numpy as np
from typing import Dict, Any, List
import random
from datetime import datetime, timedelta


class SentimentAnalysisService:
    """舆情分析服务 - 基础版"""
    
    @staticmethod
    def analyze_news_sentiment(keyword: str = "crypto") -> Dict[str, Any]:
        """分析新闻舆情"""
        # 模拟新闻数据（实际项目中应调用真实新闻 API）
        mock_news = [
            {"title": f"{keyword} 价格突破新高，市场情绪乐观", "sentiment": "positive", "impact": 0.8},
            {"title": f"{keyword} 持续上涨，投资者信心增强", "sentiment": "positive", "impact": 0.7},
            {"title": f"{keyword} 技术面分析：看涨信号明显", "sentiment": "positive", "impact": 0.6},
            {"title": f"{keyword} 价格波动加剧，市场谨慎观望", "sentiment": "neutral", "impact": 0.5},
            {"title": f"{keyword} 短期回调风险增加", "sentiment": "negative", "impact": 0.4},
            {"title": f"{keyword} 监管风险引起关注", "sentiment": "negative", "impact": 0.3},
        ]
        
        # 计算舆情分数
        positive_count = sum(1 for n in mock_news if n["sentiment"] == "positive")
        negative_count = sum(1 for n in mock_news if n["sentiment"] == "negative")
        neutral_count = sum(1 for n in mock_news if n["sentiment"] == "neutral")
        
        # 计算加权舆情分数 (-1 到 1)
        sentiment_score = 0.0
        total_impact = 0.0
        
        for news in mock_news:
            weight = news["impact"]
            total_impact += weight
            
            if news["sentiment"] == "positive":
                sentiment_score += weight
            elif news["sentiment"] == "negative":
                sentiment_score -= weight
        
        if total_impact > 0:
            sentiment_score = sentiment_score / total_impact
        
        # 确定舆情状态
        if sentiment_score > 0.3:
            overall_sentiment = "bullish"
            sentiment_label = "📈 看多"
        elif sentiment_score < -0.3:
            overall_sentiment = "bearish"
            sentiment_label = "📉 看空"
        else:
            overall_sentiment = "neutral"
            sentiment_label = "➡️ 中性"
        
        return {
            "keyword": keyword,
            "overall_sentiment": overall_sentiment,
            "sentiment_label": sentiment_label,
            "sentiment_score": float(sentiment_score),
            "news_count": len(mock_news),
            "breakdown": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            },
            "recent_news": mock_news[:5],  # 最近5条新闻
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    @staticmethod
    def analyze_social_sentiment(keyword: str = "crypto") -> Dict[str, Any]:
        """分析社交媒体舆情"""
        # 模拟社交媒体数据
        # 实际项目中应调用 Twitter/Reddit 等 API
        
        # 生成过去7天的舆情趋势
        dates = []
        sentiment_trend = []
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
            dates.append(date)
            # 模拟舆情分数 (-0.8 到 0.8)
            sentiment_trend.append(float(random.uniform(-0.8, 0.8)))
        
        # 当前热门话题
        hot_topics = [
            f"{keyword} price surge",
            f"{keyword} adoption growth",
            f"{keyword} market update",
            f"{keyword} technical analysis",
            f"{keyword} community news"
        ]
        
        # 情绪热力图
        heatmap = {
            "fear_greed": float(random.uniform(0, 100)),
            "twitter_sentiment": float(random.uniform(-0.5, 0.5)),
            "reddit_sentiment": float(random.uniform(-0.5, 0.5)),
            "telegram_sentiment": float(random.uniform(-0.5, 0.5))
        }
        
        return {
            "keyword": keyword,
            "dates": dates,
            "sentiment_trend": sentiment_trend,
            "hot_topics": hot_topics,
            "heatmap": heatmap,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    @staticmethod
    def get_fear_greed_index() -> Dict[str, Any]:
        """获取恐慌贪婪指数"""
        # 模拟恐慌贪婪指数（0-100）
        # 实际项目中应调用 Alternative.me API
        
        score = float(random.uniform(20, 80))
        
        if score < 25:
            category = "Extreme Fear"
            label = "😨 极度恐慌"
            color = "danger"
        elif score < 45:
            category = "Fear"
            label = "😟 恐慌"
            color = "warning"
        elif score < 55:
            category = "Neutral"
            label = "😐 中性"
            color = "info"
        elif score < 75:
            category = "Greed"
            label = "😊 贪婪"
            color = "warning"
        else:
            category = "Extreme Greed"
            label = "🤩 极度贪婪"
            color = "success"
        
        return {
            "score": score,
            "category": category,
            "label": label,
            "color": color,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
