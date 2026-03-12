"""
增强舆情分析服务 - 参考 FinBERT、Stock News Sentiment Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import random
import re


class EnhancedSentimentService:
    """增强舆情分析服务"""
    
    def __init__(self):
        # 舆情历史数据（滑动窗口）
        self.sentiment_history = defaultdict(lambda: deque(maxlen=1000))
        
        # 舆情预警阈值
        self.alert_thresholds = {
            "extreme_positive": 0.7,
            "positive": 0.3,
            "negative": -0.3,
            "extreme_negative": -0.7
        }
        
        # 关键词库（加密货币相关）
        self.crypto_keywords = {
            "positive": [
                "bullish", "rally", "surge", "pump", "moon", "breakout",
                "support", "accumulation", "adoption", "partnership",
                "listing", "institutional", "bull market", "ath",
                "看涨", "上涨", "突破", "买入", "利好", "牛市", "新高"
            ],
            "negative": [
                "bearish", "crash", "dump", "plunge", "collapse", "drop",
                "resistance", "distribution", "sell", "panic", "fud",
                "regulation", "ban", "hack", "scam", "bear market",
                "看跌", "下跌", "暴跌", "卖出", "利空", "熊市", "恐慌"
            ]
        }
        
        # 模拟新闻源
        self.mock_news_sources = [
            "CoinDesk", "Cointelegraph", "Decrypt", "The Block",
            "CryptoSlate", "Bitcoin Magazine", "福布斯加密", "金色财经"
        ]
        
        # 舆情指数
        self.sentiment_index = {
            "fear_greed": 50.0,  # 0-100
            "bull_bear_ratio": 0.5,  # 0-1
            "social_volume": 1000,
            "news_count": 50
        }
    
    def analyze_text_sentiment(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        分析文本情感
        
        参考: FinBERT 的金融情感分析
        """
        text = text.lower()
        
        # 1. 关键词匹配
        positive_matches = []
        negative_matches = []
        
        for word in self.crypto_keywords["positive"]:
            if word.lower() in text:
                positive_matches.append(word)
        
        for word in self.crypto_keywords["negative"]:
            if word.lower() in text:
                negative_matches.append(word)
        
        # 2. 计算情感分数
        pos_count = len(positive_matches)
        neg_count = len(negative_matches)
        total = pos_count + neg_count
        
        if total == 0:
            sentiment_score = 0.0
            sentiment_label = "neutral"
            confidence = 0.5
        else:
            sentiment_score = (pos_count - neg_count) / total
            
            if sentiment_score > 0.3:
                sentiment_label = "positive"
                confidence = min(0.5 + sentiment_score * 0.5, 1.0)
            elif sentiment_score < -0.3:
                sentiment_label = "negative"
                confidence = min(0.5 - sentiment_score * 0.5, 1.0)
            else:
                sentiment_label = "neutral"
                confidence = 0.5 + (1 - abs(sentiment_score)) * 0.5
        
        # 3. 提取主题
        topics = self._extract_topics(text)
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiment_score": float(sentiment_score),
            "sentiment_label": sentiment_label,
            "confidence": float(confidence),
            "positive_keywords": positive_matches,
            "negative_keywords": negative_matches,
            "topics": topics,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _extract_topics(self, text: str) -> List[str]:
        """提取文本主题"""
        topics = []
        
        # 加密货币相关主题
        topic_keywords = {
            "Bitcoin": ["bitcoin", "btc", "比特币"],
            "Ethereum": ["ethereum", "eth", "以太坊"],
            "Regulation": ["regulation", "regulator", "sec", "监管"],
            "Adoption": ["adoption", "institutional", "payment", "采用"],
            "Technology": ["technology", "blockchain", "protocol", "技术"],
            "Market": ["market", "price", "trading", "市场"]
        }
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text.lower():
                    topics.append(topic)
                    break
        
        return list(set(topics)) if topics else ["General"]
    
    def generate_mock_news(
        self,
        symbol: str = "BTCUSDT",
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        生成模拟新闻
        
        实际项目中应该集成真实的新闻 API
        """
        news_templates = [
            "{source}：{symbol} 价格突破 ${price:.0f}，市场情绪{sentiment}",
            "分析师表示：{symbol} 可能迎来{direction}行情",
            "最新消息：{institution} 宣布{action} {symbol}",
            "技术分析：{symbol} 在{level}位置发现{signal}",
            "{source} 独家：{symbol} 相关{event}即将发生",
            "链上数据显示：{symbol} {indicator}指标{change}",
            "社交媒体热议：{symbol} 话题热度{trend}"
        ]
        
        sentiment_options = ["乐观", "谨慎", "高涨", "低迷", "稳定"]
        direction_options = ["上涨", "下跌", "震荡", "突破"]
        institutions = ["灰度", "贝莱德", "摩根大通", "高盛", "富达"]
        actions = ["增持", "减持", "看好", "关注", "投资"]
        levels = ["关键支撑", "重要阻力", "历史高位", "年度新低"]
        signals = ["买入信号", "卖出信号", "背离信号", "突破信号"]
        events = ["利好", "重大更新", "技术升级", "合作"]
        indicators = ["活跃地址", "交易量", "持币分布", "网络哈希"]
        changes = ["显著上升", "大幅下降", "保持稳定", "出现异动"]
        trends = ["飙升", "下降", "持续升温", "逐渐冷却"]
        
        news_list = []
        base_price = 65000 if "BTC" in symbol else 3500 if "ETH" in symbol else 1
        
        for i in range(count):
            source = random.choice(self.mock_news_sources)
            template = random.choice(news_templates)
            
            # 随机价格波动 ±5%
            price = base_price * (1 + random.uniform(-0.05, 0.05))
            
            news_text = template.format(
                source=source,
                symbol=symbol,
                price=price,
                sentiment=random.choice(sentiment_options),
                direction=random.choice(direction_options),
                institution=random.choice(institutions),
                action=random.choice(actions),
                level=random.choice(levels),
                signal=random.choice(signals),
                event=random.choice(events),
                indicator=random.choice(indicators),
                change=random.choice(changes),
                trend=random.choice(trends)
            )
            
            # 分析新闻情感
            sentiment_analysis = self.analyze_text_sentiment(news_text)
            
            # 随机时间（过去24小时内）
            news_time = datetime.now() - timedelta(hours=random.uniform(0, 24))
            
            news_list.append({
                "id": f"news_{int(news_time.timestamp())}_{i}",
                "title": news_text,
                "source": source,
                "symbol": symbol,
                "sentiment_analysis": sentiment_analysis,
                "published_at": news_time.isoformat(),
                "timestamp": int(news_time.timestamp() * 1000),
                "url": f"https://example.com/news/{i}"
            })
        
        # 按时间倒序排序
        news_list.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return news_list
    
    def calculate_sentiment_index(
        self,
        symbol: str,
        news_list: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        计算综合舆情指数
        
        参考: Fear & Greed Index
        """
        if news_list is None:
            news_list = self.generate_mock_news(symbol, count=20)
        
        # 1. 新闻情感分析
        sentiment_scores = []
        sentiment_counts = defaultdict(int)
        
        for news in news_list:
            if "sentiment_analysis" in news:
                score = news["sentiment_analysis"]["sentiment_score"]
                label = news["sentiment_analysis"]["sentiment_label"]
                sentiment_scores.append(score)
                sentiment_counts[label] += 1
        
        if not sentiment_scores:
            avg_sentiment = 0.0
        else:
            avg_sentiment = float(np.mean(sentiment_scores))
        
        # 2. 计算恐惧贪婪指数（0-100）
        # 0 = 极度恐惧，100 = 极度贪婪
        fear_greed = 50 + avg_sentiment * 50
        fear_greed = max(0, min(100, fear_greed))
        
        # 3. 多空比例
        total = sum(sentiment_counts.values())
        bull_count = sentiment_counts.get("positive", 0)
        bear_count = sentiment_counts.get("negative", 0)
        
        if total > 0:
            bull_bear_ratio = bull_count / (bull_count + bear_count + 1)
        else:
            bull_bear_ratio = 0.5
        
        # 4. 确定市场状态
        if fear_greed > 75:
            market_state = "极度贪婪"
            state_emoji = "🟢"
        elif fear_greed > 60:
            market_state = "贪婪"
            state_emoji = "🟡"
        elif fear_greed > 40:
            market_state = "中性"
            state_emoji = "⚪"
        elif fear_greed > 25:
            market_state = "恐惧"
            state_emoji = "🟠"
        else:
            market_state = "极度恐惧"
            state_emoji = "🔴"
        
        # 5. 更新全局指数
        self.sentiment_index["fear_greed"] = fear_greed
        self.sentiment_index["bull_bear_ratio"] = bull_bear_ratio
        self.sentiment_index["news_count"] = len(news_list)
        self.sentiment_index["social_volume"] = 1000 + random.randint(-200, 200)
        
        # 6. 记录历史
        history_record = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "datetime": datetime.now().isoformat(),
            "symbol": symbol,
            "fear_greed": float(fear_greed),
            "market_state": market_state,
            "avg_sentiment": float(avg_sentiment),
            "bull_bear_ratio": float(bull_bear_ratio),
            "sentiment_counts": dict(sentiment_counts),
            "news_count": len(news_list)
        }
        self.sentiment_history[symbol].append(history_record)
        
        return {
            "symbol": symbol,
            "fear_greed_index": float(fear_greed),
            "market_state": market_state,
            "market_state_emoji": state_emoji,
            "avg_sentiment_score": float(avg_sentiment),
            "bull_bear_ratio": float(bull_bear_ratio),
            "sentiment_distribution": dict(sentiment_counts),
            "news_analyzed": len(news_list),
            "social_volume": self.sentiment_index["social_volume"],
            "recent_news": news_list[:5],  # 最新5条新闻
            "history_record": history_record
        }
    
    def check_sentiment_alerts(
        self,
        symbol: str,
        sentiment_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查舆情预警
        
        参考: 舆情异常检测
        """
        alerts = []
        fear_greed = sentiment_data.get("fear_greed_index", 50)
        avg_sentiment = sentiment_data.get("avg_sentiment_score", 0)
        
        # 1. 极度贪婪预警
        if fear_greed > 80:
            alerts.append({
                "type": "extreme_greed",
                "level": "warning",
                "title": "⚠️ 极度贪婪警告",
                "message": f"恐惧贪婪指数高达 {fear_greed:.1f}，市场可能过热",
                "suggestion": "考虑分批止盈，警惕回调风险"
            })
        
        # 2. 极度恐惧预警（可能是买入机会）
        elif fear_greed < 20:
            alerts.append({
                "type": "extreme_fear",
                "level": "info",
                "title": "😨 极度恐惧",
                "message": f"恐惧贪婪指数低至 {fear_greed:.1f}，市场可能过度恐慌",
                "suggestion": "可关注超卖机会，但需严格控制风险"
            })
        
        # 3. 强烈负面舆情预警
        if avg_sentiment < -0.5:
            alerts.append({
                "type": "strong_negative_sentiment",
                "level": "warning",
                "title": "📉 强烈负面舆情",
                "message": f"平均情感分 {avg_sentiment:.2f}，需关注利空消息",
                "suggestion": "谨慎操作，等待局势明朗"
            })
        
        # 4. 强烈正面舆情
        elif avg_sentiment > 0.5:
            alerts.append({
                "type": "strong_positive_sentiment",
                "level": "info",
                "title": "📈 强烈正面舆情",
                "message": f"平均情感分 {avg_sentiment:.2f}，市场情绪乐观",
                "suggestion": "可顺势操作，但勿追高"
            })
        
        # 5. 舆情突变检测（与历史对比）
        history = list(self.sentiment_history[symbol])
        if len(history) >= 5:
            recent_avg = np.mean([h["fear_greed"] for h in history[-5:-1]])
            current = fear_greed
            change = current - recent_avg
            
            if abs(change) > 20:
                direction = "上升" if change > 0 else "下降"
                alerts.append({
                    "type": "sentiment_sudden_change",
                    "level": "info",
                    "title": "🔄 舆情突变",
                    "message": f"恐惧贪婪指数突然{direction} {abs(change):.1f} 点",
                    "suggestion": "关注消息面变化"
                })
        
        return alerts
    
    def get_sentiment_history(
        self,
        symbol: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取舆情历史数据"""
        history = list(self.sentiment_history[symbol])
        return history[-limit:]

    def analyze_full_sentiment(
        self,
        keyword: str,
        news_count: int = 20
    ) -> Dict[str, Any]:
        """
        全方面舆情分析（用于演示与 API）
        返回结构与 test_all_new_features.py 对齐。
        """
        symbol = str(keyword or "BTC").upper()
        news_list = self.generate_mock_news(symbol, count=news_count)
        sentiment_index = self.calculate_sentiment_index(symbol, news_list)

        # 新闻情感汇总
        distribution = sentiment_index.get("sentiment_distribution", {}) or {}
        sentiment_score = float(sentiment_index.get("avg_sentiment_score", 0.0) or 0.0)
        news_sentiment = {
            "sentiment_score": sentiment_score,
            "news_count": len(news_list),
            "distribution": {
                "positive": int(distribution.get("positive", 0) or 0),
                "negative": int(distribution.get("negative", 0) or 0),
                "neutral": int(distribution.get("neutral", 0) or 0),
            },
        }

        # 社交情感（模拟）
        overall_sentiment = float(max(-1.0, min(1.0, sentiment_score + random.uniform(-0.15, 0.15))))
        hot_topics = self._extract_topics(" ".join([n["title"] for n in news_list[:5]]))
        social_sentiment = {
            "overall_sentiment": overall_sentiment,
            "hot_topics": hot_topics[:5],
        }

        # 趋势分析（基于历史恐惧贪婪指数变化）
        history = self.get_sentiment_history(symbol, limit=6)
        if len(history) >= 2:
            delta = history[-1]["fear_greed"] - history[0]["fear_greed"]
        else:
            delta = sentiment_index.get("fear_greed_index", 50) - 50
        if delta > 8:
            trend_label = "升温"
        elif delta < -8:
            trend_label = "降温"
        else:
            trend_label = "平稳"
        trend_analysis = {
            "trend_label": trend_label,
            "delta": float(delta),
        }

        # 热度分析（基于新闻数量 + 社交量）
        social_volume = int(sentiment_index.get("social_volume", 0) or 0)
        heat_index = min(100.0, max(0.0, len(news_list) * 2 + social_volume / 30))
        if heat_index > 70:
            heat_label = "高热"
        elif heat_index > 40:
            heat_label = "中性"
        else:
            heat_label = "低热"
        heat_analysis = {
            "heat_index": float(heat_index),
            "heat_label": heat_label,
        }

        # 综合评分
        score = float(max(0.0, min(100.0, 50 + sentiment_score * 50 + (heat_index - 50) * 0.3)))
        if score >= 75:
            grade = "A"
            label = "情绪乐观"
            suggestion = "可关注强势趋势，但避免追高。"
        elif score >= 55:
            grade = "B"
            label = "情绪偏多"
            suggestion = "以趋势跟随为主，注意回撤。"
        elif score >= 40:
            grade = "C"
            label = "情绪中性"
            suggestion = "等待更清晰的信号。"
        else:
            grade = "D"
            label = "情绪偏空"
            suggestion = "谨慎操作，严格风控。"
        overall_score = {
            "score": score,
            "grade": grade,
            "label": label,
            "suggestion": suggestion,
        }

        alerts = self.check_sentiment_alerts(symbol, sentiment_index)
        risk_level = "low"
        if any(a.get("level") == "warning" for a in alerts):
            risk_level = "high"
        elif alerts:
            risk_level = "medium"
        alert_analysis = {
            "alert_count": len(alerts),
            "risk_level": risk_level,
            "alerts": alerts,
        }

        return {
            "keyword": symbol,
            "overall_score": overall_score,
            "news_sentiment": news_sentiment,
            "social_sentiment": social_sentiment,
            "trend_analysis": trend_analysis,
            "heat_analysis": heat_analysis,
            "alert_analysis": alert_analysis,
            "news": news_list[:10],
            "generated_at": datetime.now().isoformat(),
        }


# 全局实例
_enhanced_sentiment_service = None


def get_enhanced_sentiment_service() -> EnhancedSentimentService:
    """获取增强舆情服务单例"""
    global _enhanced_sentiment_service
    if _enhanced_sentiment_service is None:
        _enhanced_sentiment_service = EnhancedSentimentService()
    return _enhanced_sentiment_service

