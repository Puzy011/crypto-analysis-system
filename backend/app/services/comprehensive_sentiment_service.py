"""
综合舆情分析服务 - FinBERT 风格增强版
参考: FinBERT, Stock News Sentiment Analysis, Cryptocurrency Sentiment Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import math
from dataclasses import dataclass


@dataclass
class NewsImpact:
    """新闻影响记录"""
    news_id: str
    published_at: int
    sentiment_score: float
    price_before: float
    price_after_1h: float
    price_after_4h: float
    price_after_24h: float
    impact_score: float
    impact_label: str


class ComprehensiveSentimentService:
    """综合舆情分析服务 - FinBERT 风格增强版"""
    
    def __init__(self):
        # 金融情感词典 (FinBERT 风格)
        self.financial_sentiment_dict = {
            # 极度正面
            "bullish": 2.0,
            "rally": 2.0,
            "surge": 2.0,
            "pump": 2.0,
            "moon": 2.0,
            "breakout": 2.0,
            "soar": 2.0,
            "skyrocket": 2.0,
            "boom": 2.0,
            "ath": 2.0,
            "all-time high": 2.0,
            "看涨": 2.0,
            "上涨": 2.0,
            "突破": 2.0,
            "暴涨": 2.0,
            "新高": 2.0,
            
            # 正面
            "support": 1.0,
            "accumulation": 1.0,
            "adoption": 1.0,
            "partnership": 1.0,
            "listing": 1.0,
            "institutional": 1.0,
            "bull market": 1.0,
            "gain": 1.0,
            "rise": 1.0,
            "grow": 1.0,
            "positive": 1.0,
            "利好": 1.0,
            "牛市": 1.0,
            "增长": 1.0,
            "合作": 1.0,
            "上市": 1.0,
            
            # 轻微正面
            "rebound": 0.5,
            "recover": 0.5,
            "stable": 0.5,
            "steady": 0.5,
            "consolidation": 0.5,
            "回弹": 0.5,
            "稳定": 0.5,
            "震荡": 0.5,
            
            # 中性
            "neutral": 0.0,
            "sideways": 0.0,
            "flat": 0.0,
            "range-bound": 0.0,
            "中性": 0.0,
            "横盘": 0.0,
            
            # 轻微负面
            "pullback": -0.5,
            "retrace": -0.5,
            "correction": -0.5,
            "回调": -0.5,
            "回撤": -0.5,
            "调整": -0.5,
            
            # 负面
            "resistance": -1.0,
            "distribution": -1.0,
            "sell": -1.0,
            "panic": -1.0,
            "fud": -1.0,
            "regulation": -1.0,
            "ban": -1.0,
            "hack": -1.0,
            "scam": -1.0,
            "bear market": -1.0,
            "drop": -1.0,
            "fall": -1.0,
            "decline": -1.0,
            "negative": -1.0,
            "看跌": -1.0,
            "下跌": -1.0,
            "利空": -1.0,
            "熊市": -1.0,
            "暴跌": -1.0,
            "监管": -1.0,
            "黑客": -1.0,
            "骗局": -1.0,
            
            # 极度负面
            "bearish": -2.0,
            "crash": -2.0,
            "dump": -2.0,
            "plunge": -2.0,
            "collapse": -2.0,
            "破产": -2.0,
            "崩盘": -2.0,
            "崩溃": -2.0
        }
        
        # 金融停用词
        self.financial_stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "up", "down",
            "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall",
            "比特币", "以太坊", "币安", "价格", "市场", "交易", "btc", "eth",
            "crypto", "bitcoin", "ethereum", "price", "market", "trade"
        }
        
        # 加密货币相关实体类型
        self.entity_types = {
            "exchange": ["binance", "coinbase", "okx", "bybit", "kucoin", "币安", "火币", "欧易"],
            "coin": ["bitcoin", "ethereum", "solana", "cardano", "ripple", "比特币", "以太坊", "sol"],
            "person": ["satoshi", "vitalik", "cz", "中本聪", "V神", "赵长鹏"],
            "event": ["halving", "merge", "upgrade", "fork", "减半", "合并", "升级", "分叉"],
            "regulation": ["sec", "cftc", "fed", "证监会", "央行", "监管"]
        }
        
        # 新闻影响历史
        self.news_impact_history: Dict[str, List[NewsImpact]] = defaultdict(list)
        
        # 舆情历史
        self.sentiment_history = defaultdict(lambda: defaultdict(list))
    
    def extract_keywords_tfidf(
        self,
        texts: List[str],
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """
        TF-IDF 关键词提取
        
        参考: 自然语言处理中的关键词提取
        """
        if not texts:
            return []
        
        # 1. 预处理文本
        processed_texts = []
        for text in texts:
            words = self._preprocess_text(text)
            processed_texts.append(words)
        
        # 2. 计算词频 (TF)
        all_words = [word for words in processed_texts for word in words]
        word_freq = Counter(all_words)
        
        # 3. 计算文档频率 (DF)
        doc_freq = defaultdict(int)
        for words in processed_texts:
            unique_words = set(words)
            for word in unique_words:
                doc_freq[word] += 1
        
        # 4. 计算 TF-IDF
        num_docs = len(processed_texts)
        tfidf_scores = {}
        
        for word, freq in word_freq.items():
            if word in self.financial_stopwords or len(word) < 2:
                continue
            
            tf = freq / len(all_words)
            idf = math.log(num_docs / (1 + doc_freq.get(word, 0)))
            tfidf_scores[word] = tf * idf
        
        # 5. 排序返回
        sorted_keywords = sorted(
            tfidf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return sorted_keywords
    
    def extract_keywords_textrank(
        self,
        text: str,
        top_n: int = 10,
        window_size: int = 4
    ) -> List[Tuple[str, float]]:
        """
        TextRank 关键词提取
        
        参考: PageRank 算法在文本中的应用
        """
        words = self._preprocess_text(text)
        
        if len(words) < 2:
            return []
        
        # 1. 构建词共现图
        word_nodes = list(set(words))
        word_to_idx = {word: i for i, word in enumerate(word_nodes)}
        num_nodes = len(word_nodes)
        
        # 初始化邻接矩阵
        adjacency = np.zeros((num_nodes, num_nodes))
        
        # 滑动窗口构建共现
        for i in range(len(words)):
            word1 = words[i]
            idx1 = word_to_idx.get(word1)
            if idx1 is None:
                continue
            
            for j in range(max(0, i - window_size), min(len(words), i + window_size + 1)):
                if i == j:
                    continue
                word2 = words[j]
                idx2 = word_to_idx.get(word2)
                if idx2 is not None:
                    adjacency[idx1][idx2] += 1
        
        # 2. TextRank 迭代
        damping = 0.85
        max_iter = 100
        tolerance = 1e-6
        
        scores = np.ones(num_nodes) / num_nodes
        
        for _ in range(max_iter):
            prev_scores = scores.copy()
            
            for i in range(num_nodes):
                # 计算入度分数
                incoming_score = 0.0
                for j in range(num_nodes):
                    if adjacency[j][i] > 0:
                        sum_j = adjacency[j].sum()
                        if sum_j > 0:
                            incoming_score += adjacency[j][i] / sum_j * scores[j]
                
                scores[i] = (1 - damping) + damping * incoming_score
            
            # 检查收敛
            if np.abs(scores - prev_scores).sum() < tolerance:
                break
        
        # 3. 返回结果
        keyword_scores = [
            (word_nodes[i], float(scores[i]))
            for i in range(num_nodes)
            if word_nodes[i] not in self.financial_stopwords
            and len(word_nodes[i]) >= 2
        ]
        
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        return keyword_scores[:top_n]
    
    def analyze_financial_sentiment(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        FinBERT 风格金融情感分析
        
        参考: ProsusAI/finbert
        """
        words = self._preprocess_text(text)
        text_lower = text.lower()
        
        # 1. 基于金融情感词典的评分
        sentiment_scores = []
        matched_words = []
        
        for word in words:
            if word in self.financial_sentiment_dict:
                score = self.financial_sentiment_dict[word]
                sentiment_scores.append(score)
                matched_words.append((word, score))
        
        # 2. n-gram 匹配
        for n in [3, 2]:
            for i in range(len(words) - n + 1):
                ngram = " ".join(words[i:i+n])
                if ngram in self.financial_sentiment_dict:
                    score = self.financial_sentiment_dict[ngram]
                    sentiment_scores.append(score)
                    matched_words.append((ngram, score))
        
        # 3. 计算综合情感分
        if not sentiment_scores:
            sentiment_score = 0.0
            sentiment_label = "neutral"
            confidence = 0.5
        else:
            # 加权平均（考虑词频和强度）
            sentiment_score = float(np.mean(sentiment_scores))
            
            # 归一化到 [-1, 1]
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            # 确定情感标签
            if sentiment_score > 0.5:
                sentiment_label = "very_positive"
                confidence = 0.5 + sentiment_score * 0.5
            elif sentiment_score > 0.1:
                sentiment_label = "positive"
                confidence = 0.5 + sentiment_score * 0.5
            elif sentiment_score < -0.5:
                sentiment_label = "very_negative"
                confidence = 0.5 - sentiment_score * 0.5
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
                confidence = 0.5 - sentiment_score * 0.5
            else:
                sentiment_label = "neutral"
                confidence = 0.5 + (1 - abs(sentiment_score)) * 0.5
        
        # 4. 提取实体
        entities = self._extract_entities(text)
        
        # 5. 提取关键词
        keywords_textrank = self.extract_keywords_textrank(text, top_n=8)
        
        return {
            "text": text[:150] + "..." if len(text) > 150 else text,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "confidence": float(confidence),
            "matched_words": matched_words,
            "entities": entities,
            "keywords": [word for word, score in keywords_textrank],
            "keyword_scores": keywords_textrank,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def analyze_news_price_impact(
        self,
        symbol: str,
        news_list: List[Dict[str, Any]],
        price_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        新闻-价格关联分析
        
        参考: Stock News Sentiment Analysis
        """
        if not news_list or price_data.empty:
            return {"message": "数据不足"}
        
        impacts = []
        price_dict = {
            row["timestamp"]: row["close"]
            for _, row in price_data.iterrows()
        }
        timestamps = sorted(price_dict.keys())
        
        for news in news_list:
            news_time = news.get("timestamp", 0)
            sentiment_analysis = news.get("sentiment_analysis", {})
            sentiment_score = sentiment_analysis.get("sentiment_score", 0)
            
            # 找到新闻发布前后的价格
            price_before = self._find_closest_price(news_time, timestamps, price_dict, direction="before")
            price_after_1h = self._find_price_after(news_time, timestamps, price_dict, hours=1)
            price_after_4h = self._find_price_after(news_time, timestamps, price_dict, hours=4)
            price_after_24h = self._find_price_after(news_time, timestamps, price_dict, hours=24)
            
            if price_before is not None and price_after_24h is not None:
                # 计算影响分数
                price_change_24h = (price_after_24h - price_before) / price_before
                
                # 情感与价格变化的一致性
                sentiment_sign = 1 if sentiment_score > 0 else -1
                price_sign = 1 if price_change_24h > 0 else -1
                agreement = sentiment_sign == price_sign
                
                # 综合影响分数
                impact_score = abs(price_change_24h) * (1 if agreement else -1)
                
                # 影响标签
                if impact_score > 0.05:
                    impact_label = "strong_positive"
                elif impact_score > 0.02:
                    impact_label = "positive"
                elif impact_score < -0.05:
                    impact_label = "strong_negative"
                elif impact_score < -0.02:
                    impact_label = "negative"
                else:
                    impact_label = "neutral"
                
                impact = NewsImpact(
                    news_id=news.get("id", ""),
                    published_at=news_time,
                    sentiment_score=sentiment_score,
                    price_before=price_before,
                    price_after_1h=price_after_1h or price_before,
                    price_after_4h=price_after_4h or price_before,
                    price_after_24h=price_after_24h,
                    impact_score=impact_score,
                    impact_label=impact_label
                )
                impacts.append(impact)
        
        # 统计分析
        if impacts:
            avg_impact = np.mean([i.impact_score for i in impacts])
            pos_impacts = sum(1 for i in impacts if i.impact_score > 0)
            neg_impacts = sum(1 for i in impacts if i.impact_score < 0)
            agreement_rate = sum(1 for i in impacts if i.impact_label in ["positive", "strong_positive"]) / len(impacts)
            
            # 按影响排序
            top_impact_news = sorted(impacts, key=lambda x: abs(x.impact_score), reverse=True)[:10]
        else:
            avg_impact = 0.0
            pos_impacts = 0
            neg_impacts = 0
            agreement_rate = 0.0
            top_impact_news = []
        
        return {
            "symbol": symbol,
            "total_news_analyzed": len(news_list),
            "total_impacts_calculated": len(impacts),
            "average_impact_score": float(avg_impact),
            "positive_impacts": pos_impacts,
            "negative_impacts": neg_impacts,
            "agreement_rate": float(agreement_rate),
            "top_impact_news": [
                {
                    "news_id": i.news_id,
                    "impact_score": float(i.impact_score),
                    "impact_label": i.impact_label,
                    "sentiment_score": float(i.sentiment_score),
                    "price_change_24h": float((i.price_after_24h - i.price_before) / i.price_before)
                }
                for i in top_impact_news
            ]
        }
    
    def _preprocess_text(self, text: str) -> List[str]:
        """预处理文本"""
        # 转小写
        text = text.lower()
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词和短词
        words = [
            word for word in words
            if word not in self.financial_stopwords
            and len(word) >= 2
        ]
        
        return words
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取金融实体"""
        text_lower = text.lower()
        entities = defaultdict(list)
        
        for entity_type, keywords in self.entity_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    entities[entity_type].append(keyword)
        
        return dict(entities)
    
    def _find_closest_price(
        self,
        target_time: int,
        timestamps: List[int],
        price_dict: Dict[int, float],
        direction: str = "both"
    ) -> Optional[float]:
        """找到最近的价格"""
        if not timestamps:
            return None
        
        # 二分查找
        left, right = 0, len(timestamps)
        while left < right:
            mid = (left + right) // 2
            if timestamps[mid] < target_time:
                left = mid + 1
            else:
                right = mid
        
        candidates = []
        if left > 0 and (direction in ["both", "before"]):
            candidates.append(timestamps[left - 1])
        if left < len(timestamps) and (direction in ["both", "after"]):
            candidates.append(timestamps[left])
        
        if not candidates:
            return None
        
        # 返回最接近的
        closest = min(candidates, key=lambda x: abs(x - target_time))
        return price_dict.get(closest)
    
    def _find_price_after(
        self,
        news_time: int,
        timestamps: List[int],
        price_dict: Dict[int, float],
        hours: float
    ) -> Optional[float]:
        """找到指定小时后的价格"""
        target_time = news_time + int(hours * 3600 * 1000)
        return self._find_closest_price(target_time, timestamps, price_dict, direction="after")


# 全局实例
_comprehensive_sentiment_service = None


def get_comprehensive_sentiment_service() -> ComprehensiveSentimentService:
    """获取综合舆情服务单例"""
    global _comprehensive_sentiment_service
    if _comprehensive_sentiment_service is None:
        _comprehensive_sentiment_service = ComprehensiveSentimentService()
    return _comprehensive_sentiment_service

