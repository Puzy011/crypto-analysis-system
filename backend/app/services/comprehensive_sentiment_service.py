"""
综合舆情分析服务 - FinBERT 风格增强版
参考: FinBERT, Stock News Sentiment Analysis, Cryptocurrency Sentiment Analysis
"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import xml.etree.ElementTree as ET

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


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
    event_tags: List[str]


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

        # 强度副词和否定词（用于更接近 FinBERT 的规则增强）
        self.intensifiers = {
            "very": 1.25, "extremely": 1.5, "significantly": 1.3, "massively": 1.4,
            "非常": 1.25, "强烈": 1.4, "明显": 1.2, "大幅": 1.4
        }
        self.negations = {"not", "never", "no", "without", "无", "不", "并非", "未"}

        # 事件标签词典
        self.event_keywords = {
            "regulation": ["sec", "regulation", "ban", "lawsuit", "监管", "禁令", "诉讼"],
            "security": ["hack", "exploit", "breach", "attack", "黑客", "漏洞", "被盗"],
            "adoption": ["adoption", "integration", "partnership", "上线", "合作", "接入"],
            "macro": ["fed", "rate", "inflation", "宏观", "利率", "通胀"],
            "etf": ["etf", "approval", "申报", "通过"],
            "whale": ["whale", "large transfer", "巨鲸", "大额转账", "主力"]
        }

        # 新闻源权重（可信度）
        self.source_weights = {
            "coindesk": 1.0,
            "cointelegraph": 0.95,
            "decrypt": 0.90,
            "the block": 1.0,
            "binance": 0.90,
            "okx": 0.85,
            "unknown": 0.75
        }

        # 币种别名
        self.asset_alias = {
            "BTC": ["btc", "bitcoin", "比特币"],
            "ETH": ["eth", "ethereum", "以太坊"],
            "SOL": ["sol", "solana"],
            "BNB": ["bnb", "binance coin"],
            "XRP": ["xrp", "ripple"],
            "ADA": ["ada", "cardano"],
            "DOGE": ["doge", "dogecoin"]
        }

        # 公开 RSS 新闻源（无需 API Key）
        self.news_feeds = [
            {"source": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
            {"source": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
            {"source": "Decrypt", "url": "https://decrypt.co/feed"},
            {"source": "The Block", "url": "https://www.theblock.co/rss.xml"}
        ]

        # 简单内存缓存，减少频繁请求
        self.news_cache: Dict[str, Dict[str, Any]] = {}
        self.news_cache_ttl = timedelta(minutes=5)

    def fetch_market_news(
        self,
        symbol: str,
        limit: int = 30,
        hours: int = 72,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取实时新闻（RSS），失败时降级到模板新闻。
        """
        cache_key = f"{symbol}_{limit}_{hours}"
        now = datetime.now(timezone.utc)
        if not force_refresh:
            cached = self.news_cache.get(cache_key)
            if cached and now - cached["updated_at"] < self.news_cache_ttl:
                return cached["items"][:limit]

        asset = self._extract_base_asset(symbol)
        aliases = self.asset_alias.get(asset, [asset.lower()])
        cutoff_ts = int((now - timedelta(hours=hours)).timestamp() * 1000)
        seen_titles = set()
        all_news: List[Dict[str, Any]] = []

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }

        for feed in self.news_feeds:
            try:
                resp = requests.get(feed["url"], headers=headers, timeout=8)
                if resp.status_code != 200 or not resp.text:
                    continue

                entries = self._parse_feed_entries(resp.text)
                for idx, entry in enumerate(entries):
                    title = entry.get("title", "")
                    if not title:
                        continue

                    desc = entry.get("description", "")
                    composed = f"{title} {desc}".lower()
                    if not self._is_relevant_news(composed, aliases, asset):
                        continue

                    norm_title = self._normalize_title(title)
                    if norm_title in seen_titles:
                        continue
                    seen_titles.add(norm_title)

                    link = entry.get("link", "")
                    published_str = entry.get("published", "")
                    ts = self._parse_timestamp(published_str)
                    if ts < cutoff_ts:
                        continue

                    all_news.append(
                        {
                            "id": f"{feed['source'].lower()}_{ts}_{idx}",
                            "title": title.strip(),
                            "content": desc.strip(),
                            "source": feed["source"],
                            "url": link.strip(),
                            "timestamp": ts,
                            "published_at": datetime.fromtimestamp(
                                ts / 1000, tz=timezone.utc
                            ).isoformat(),
                            "symbol": symbol,
                        }
                    )
            except Exception:
                continue

        all_news.sort(key=lambda x: x["timestamp"], reverse=True)
        if not all_news:
            all_news = self._generate_fallback_news(symbol, max(10, min(limit, 20)))

        self.news_cache[cache_key] = {"updated_at": now, "items": all_news[:limit]}
        return all_news[:limit]

    def build_sentiment_index(
        self,
        symbol: str,
        news_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        构建综合舆情指数（时间衰减 + 来源权重）。
        """
        if not news_list:
            return {
                "symbol": symbol,
                "fear_greed_index": 50.0,
                "market_state": "中性",
                "market_state_emoji": "⚪",
                "avg_sentiment_score": 0.0,
                "weighted_sentiment_score": 0.0,
                "sentiment_distribution": {"neutral": 0},
                "event_distribution": {},
                "source_distribution": {},
                "source_diversity_score": 0.0,
                "momentum_24h": 0.0,
                "news_analyzed": 0,
                "hot_topics": [],
            }

        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        weighted_scores: List[float] = []
        raw_scores: List[float] = []
        source_dist: Counter = Counter()
        label_dist: Counter = Counter()
        event_dist: Counter = Counter()

        for news in news_list:
            analysis = news.get("enhanced_sentiment") or news.get("sentiment_analysis")
            if not analysis:
                analysis = self.analyze_financial_sentiment(
                    f"{news.get('title', '')} {news.get('content', '')}"
                )

            score = float(analysis.get("sentiment_score", 0.0))
            label = analysis.get("sentiment_label", "neutral")
            raw_scores.append(score)
            label_dist[label] += 1

            source = str(news.get("source", "unknown")).lower()
            source_dist[source] += 1
            source_w = self._source_weight(source)

            age_h = max(0.0, (now_ts - int(news.get("timestamp", now_ts))) / 3600000)
            time_w = math.exp(-age_h / 24)
            weighted_scores.append(score * source_w * time_w)

            for evt in analysis.get("event_tags", []):
                event_dist[evt] += 1

        avg_score = float(np.mean(raw_scores)) if raw_scores else 0.0
        weighted_score = (
            float(np.sum(weighted_scores) / (np.sum(np.abs(weighted_scores)) + 1e-8))
            if weighted_scores
            else 0.0
        )

        fear_greed = float(max(0.0, min(100.0, 50 + weighted_score * 50)))
        if fear_greed >= 75:
            market_state, emoji = "极度贪婪", "🟢"
        elif fear_greed >= 60:
            market_state, emoji = "贪婪", "🟡"
        elif fear_greed >= 40:
            market_state, emoji = "中性", "⚪"
        elif fear_greed >= 25:
            market_state, emoji = "恐惧", "🟠"
        else:
            market_state, emoji = "极度恐惧", "🔴"

        recent_scores = [
            s
            for n, s in zip(news_list, raw_scores)
            if now_ts - int(n.get("timestamp", now_ts)) <= 24 * 3600000
        ]
        old_scores = [
            s
            for n, s in zip(news_list, raw_scores)
            if now_ts - int(n.get("timestamp", now_ts)) > 24 * 3600000
        ]
        momentum = (
            float(np.mean(recent_scores) - np.mean(old_scores))
            if recent_scores and old_scores
            else 0.0
        )

        hot_topics = [
            word for word, _ in self.extract_keywords_tfidf(
                [n.get("title", "") for n in news_list], top_n=8
            )
        ]
        source_diversity = float(
            min(1.0, len(source_dist) / max(1, len(self.news_feeds)))
        )
        result = {
            "symbol": symbol,
            "fear_greed_index": fear_greed,
            "market_state": market_state,
            "market_state_emoji": emoji,
            "avg_sentiment_score": avg_score,
            "weighted_sentiment_score": weighted_score,
            "sentiment_distribution": dict(label_dist),
            "event_distribution": dict(event_dist),
            "source_distribution": dict(source_dist),
            "source_diversity_score": source_diversity,
            "momentum_24h": momentum,
            "news_analyzed": len(news_list),
            "hot_topics": hot_topics,
        }
        self._append_sentiment_history(symbol, result)
        return result

    def forecast_sentiment_trend(
        self,
        symbol: str,
        sentiment_index: Dict[str, Any],
        news_list: List[Dict[str, Any]],
        hours_ahead: int = 24,
    ) -> Dict[str, Any]:
        """
        预测未来舆情趋势（线性趋势 + 动量融合）。
        """
        horizon = max(1, min(int(hours_ahead), 72))
        current_score = float(sentiment_index.get("weighted_sentiment_score", 0.0))
        history_points = list(self.sentiment_history[symbol]["index"])[-240:]

        if not history_points:
            forecast_score = current_score
            slope_per_hour = 0.0
            sample_points = 0
        else:
            timestamps = np.array([float(p.get("timestamp", 0.0)) for p in history_points], dtype=float)
            scores = np.array([float(p.get("weighted_sentiment_score", current_score)) for p in history_points], dtype=float)

            if len(scores) >= 2 and np.max(timestamps) > np.min(timestamps):
                x_hours = (timestamps - np.min(timestamps)) / 3600000.0
                slope_per_hour, intercept = np.polyfit(x_hours, scores, 1)
                trend_forecast = float(intercept + slope_per_hour * (x_hours[-1] + horizon))
            else:
                slope_per_hour = 0.0
                trend_forecast = current_score

            momentum = float(sentiment_index.get("momentum_24h", 0.0))
            forecast_score = float(trend_forecast * 0.75 + (current_score + 0.6 * momentum) * 0.25)
            sample_points = len(scores)

        forecast_score = float(max(-1.0, min(1.0, forecast_score)))
        delta = float(forecast_score - current_score)

        if delta > 0.06:
            direction = "up"
            direction_label = "舆情升温"
        elif delta < -0.06:
            direction = "down"
            direction_label = "舆情降温"
        else:
            direction = "sideways"
            direction_label = "舆情平稳"

        expected_fg = float(max(0.0, min(100.0, 50 + forecast_score * 50)))
        confidence = float(
            max(
                0.35,
                min(
                    0.96,
                    0.45
                    + min(sample_points, 80) / 200
                    + min(abs(delta), 0.3) * 0.8,
                ),
            )
        )

        event_dist = sentiment_index.get("event_distribution", {}) or {}
        top_events = sorted(event_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        drivers = []
        if top_events:
            drivers.append("高频事件: " + ", ".join([f"{evt}({cnt})" for evt, cnt in top_events]))
        hot_topics = sentiment_index.get("hot_topics", []) or []
        if hot_topics:
            drivers.append("热点关键词: " + ", ".join(hot_topics[:5]))
        if not drivers:
            drivers.append("新闻分布较分散，暂无明显单一驱动")

        return {
            "symbol": symbol,
            "hours_ahead": horizon,
            "current_score": current_score,
            "forecast_score": forecast_score,
            "delta": delta,
            "direction": direction,
            "direction_label": direction_label,
            "expected_fear_greed_index": expected_fg,
            "confidence": confidence,
            "slope_per_hour": float(slope_per_hour),
            "sample_points": sample_points,
            "drivers": drivers,
            "model": "linear_momentum_blend",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _append_sentiment_history(self, symbol: str, index_result: Dict[str, Any]) -> None:
        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        rec = {
            "timestamp": now_ts,
            "weighted_sentiment_score": float(index_result.get("weighted_sentiment_score", 0.0)),
            "fear_greed_index": float(index_result.get("fear_greed_index", 50.0)),
        }
        hist = self.sentiment_history[symbol]["index"]
        hist.append(rec)
        if len(hist) > 500:
            del hist[:-500]
    
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
        FinBERT 风格金融情感分析（规则增强版）
        """
        cleaned = text.lower()
        raw_tokens = re.findall(r"[a-zA-Z\u4e00-\u9fff][a-zA-Z0-9\u4e00-\u9fff\-]*", cleaned)
        words = self._preprocess_text(text)
        sentiment_scores: List[float] = []
        matched_words: List[Tuple[str, float]] = []

        # 1) 单词情感分，考虑否定词和程度副词
        for i, token in enumerate(raw_tokens):
            if token not in self.financial_sentiment_dict:
                continue

            base_score = float(self.financial_sentiment_dict[token])
            prev_tokens = raw_tokens[max(0, i - 2):i]
            intensity = 1.0
            for prev in prev_tokens:
                intensity *= self.intensifiers.get(prev, 1.0)

            if any(prev in self.negations for prev in prev_tokens):
                base_score = -0.8 * base_score

            final_score = base_score * intensity
            sentiment_scores.append(final_score)
            matched_words.append((token, round(final_score, 3)))

        # 2) n-gram 匹配补充
        for phrase, phrase_score in self.financial_sentiment_dict.items():
            if " " not in phrase:
                continue
            count = cleaned.count(phrase)
            if count <= 0:
                continue
            for _ in range(count):
                sentiment_scores.append(float(phrase_score))
                matched_words.append((phrase, float(phrase_score)))

        # 3) 汇总分数
        if sentiment_scores:
            raw_score = float(np.mean(sentiment_scores))
            sentiment_score = float(np.tanh(raw_score / 1.5))
        else:
            sentiment_score = 0.0

        if sentiment_score > 0.55:
            sentiment_label = "very_positive"
        elif sentiment_score > 0.15:
            sentiment_label = "positive"
        elif sentiment_score < -0.55:
            sentiment_label = "very_negative"
        elif sentiment_score < -0.15:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        coverage = min(1.0, len(matched_words) / max(len(words), 1))
        confidence = float(
            max(0.35, min(0.98, 0.45 + 0.35 * abs(sentiment_score) + 0.2 * coverage))
        )

        # 4) 语义标签
        entities = self._extract_entities(text)
        keywords_textrank = self.extract_keywords_textrank(text, top_n=8)
        event_tags = self._extract_event_tags(text)
        risk_flags = [evt for evt in event_tags if evt in {"security", "regulation"}]
        
        return {
            "text": text[:180] + "..." if len(text) > 180 else text,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "confidence": float(confidence),
            "matched_words": matched_words[:12],
            "entities": entities,
            "keywords": [word for word, score in keywords_textrank],
            "keyword_scores": keywords_textrank,
            "event_tags": event_tags,
            "risk_flags": risk_flags,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def analyze_news_price_impact(
        self,
        symbol: str,
        news_list: List[Dict[str, Any]],
        price_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        新闻-价格滞后关联分析
        """
        if not news_list or price_data.empty:
            return {"message": "数据不足"}
        
        impacts: List[NewsImpact] = []
        price_dict = {int(row["timestamp"]): float(row["close"]) for _, row in price_data.iterrows()}
        timestamps = sorted(price_dict.keys())
        sent_vals: List[float] = []
        ret_1h_vals: List[float] = []
        ret_4h_vals: List[float] = []
        ret_24h_vals: List[float] = []
        event_impact_map: Dict[str, List[float]] = defaultdict(list)
        
        for news in news_list:
            news_time = int(news.get("timestamp") or self._parse_timestamp(news.get("published_at", "")))
            sentiment_analysis = (
                news.get("enhanced_sentiment")
                or news.get("sentiment_analysis")
                or {}
            )
            sentiment_score = float(sentiment_analysis.get("sentiment_score", 0))
            event_tags = sentiment_analysis.get(
                "event_tags",
                self._extract_event_tags(news.get("title", ""))
            )
            
            # 找到新闻发布前后的价格
            price_before = self._find_closest_price(news_time, timestamps, price_dict, direction="before")
            price_after_1h = self._find_price_after(news_time, timestamps, price_dict, hours=1)
            price_after_4h = self._find_price_after(news_time, timestamps, price_dict, hours=4)
            price_after_24h = self._find_price_after(news_time, timestamps, price_dict, hours=24)
            
            if price_before is None or price_after_24h is None or price_before <= 0:
                continue

            price_change_1h = ((price_after_1h or price_before) - price_before) / price_before
            price_change_4h = ((price_after_4h or price_before) - price_before) / price_before
            price_change_24h = (price_after_24h - price_before) / price_before

            agreement = (
                np.sign(sentiment_score) == np.sign(price_change_24h)
                if sentiment_score != 0
                else True
            )
            impact_score = (
                abs(price_change_24h)
                * (1 if agreement else -1)
                * (0.5 + min(abs(sentiment_score), 1.0) * 0.5)
            )
            
            if impact_score > 0.03:
                impact_label = "strong_positive"
            elif impact_score > 0.01:
                impact_label = "positive"
            elif impact_score < -0.03:
                impact_label = "strong_negative"
            elif impact_score < -0.01:
                impact_label = "negative"
            else:
                impact_label = "neutral"
            
            impact = NewsImpact(
                news_id=str(news.get("id", "")),
                published_at=news_time,
                sentiment_score=sentiment_score,
                price_before=float(price_before),
                price_after_1h=float(price_after_1h or price_before),
                price_after_4h=float(price_after_4h or price_before),
                price_after_24h=float(price_after_24h),
                impact_score=float(impact_score),
                impact_label=impact_label,
                event_tags=event_tags
            )
            impacts.append(impact)

            sent_vals.append(sentiment_score)
            ret_1h_vals.append(price_change_1h)
            ret_4h_vals.append(price_change_4h)
            ret_24h_vals.append(price_change_24h)
            for evt in event_tags:
                event_impact_map[evt].append(price_change_24h)
        
        # 统计分析
        if impacts:
            avg_impact = float(np.mean([i.impact_score for i in impacts]))
            pos_impacts = sum(1 for i in impacts if i.impact_score > 0)
            neg_impacts = sum(1 for i in impacts if i.impact_score < 0)
            agreement_rate = float(
                np.mean(
                    [
                        1
                        if (
                            np.sign(i.sentiment_score)
                            == np.sign((i.price_after_24h - i.price_before) / i.price_before)
                        ) or i.sentiment_score == 0
                        else 0
                        for i in impacts
                    ]
                )
            )
            
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
            "average_impact_score": avg_impact,
            "positive_impacts": pos_impacts,
            "negative_impacts": neg_impacts,
            "agreement_rate": agreement_rate,
            "lag_correlations": {
                "1h": self._safe_corr(sent_vals, ret_1h_vals),
                "4h": self._safe_corr(sent_vals, ret_4h_vals),
                "24h": self._safe_corr(sent_vals, ret_24h_vals),
            },
            "impact_by_event": {
                evt: {
                    "count": len(vals),
                    "avg_return_24h": float(np.mean(vals)),
                    "hit_rate": float(np.mean([1 if v > 0 else 0 for v in vals])),
                }
                for evt, vals in event_impact_map.items()
            },
            "top_impact_news": [
                {
                    "news_id": i.news_id,
                    "impact_score": float(i.impact_score),
                    "impact_label": i.impact_label,
                    "sentiment_score": float(i.sentiment_score),
                    "price_change_1h": float((i.price_after_1h - i.price_before) / i.price_before),
                    "price_change_4h": float((i.price_after_4h - i.price_before) / i.price_before),
                    "event_tags": i.event_tags,
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
        text = re.sub(r'[^\w\s\u4e00-\u9fff-]', ' ', text)
        
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

    def _extract_event_tags(self, text: str) -> List[str]:
        """提取事件标签"""
        text_lower = text.lower()
        tags = []
        for tag, keywords in self.event_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        return tags

    def _safe_corr(self, x: List[float], y: List[float]) -> float:
        """安全计算相关系数"""
        if len(x) < 4 or len(y) < 4:
            return 0.0
        if np.std(x) < 1e-10 or np.std(y) < 1e-10:
            return 0.0
        return float(np.corrcoef(x, y)[0][1])

    def _extract_base_asset(self, symbol: str) -> str:
        """从交易对提取基础币种"""
        sym = symbol.upper().replace("-", "").replace("_", "")
        for suffix in ("USDT", "BUSD", "USDC", "USD", "BTC", "ETH"):
            if sym.endswith(suffix) and len(sym) > len(suffix):
                return sym[:-len(suffix)]
        return sym

    def _is_relevant_news(self, text: str, aliases: List[str], asset: str) -> bool:
        """新闻相关性过滤"""
        if any(alias in text for alias in aliases):
            return True
        if asset in {"BTC", "ETH"} and any(
            key in text
            for key in ("crypto", "bitcoin", "ethereum", "etf", "sec", "regulation", "exchange")
        ):
            return True
        return False

    def _source_weight(self, source: str) -> float:
        """新闻源权重"""
        source_lower = source.lower()
        for key, weight in self.source_weights.items():
            if key in source_lower:
                return weight
        return self.source_weights["unknown"]

    def _normalize_title(self, title: str) -> str:
        """标题归一化用于去重"""
        return re.sub(
            r"\s+",
            " ",
            re.sub(r"[^\w\s\u4e00-\u9fff]", "", title.lower())
        ).strip()

    def _safe_tag_text(self, item: Any, tag_name: str) -> str:
        """安全读取 XML tag"""
        tag = item.find(tag_name)
        if tag is None:
            return ""
        text = getattr(tag, "text", "")
        return text.strip() if text else ""

    def _parse_feed_entries(self, content: str) -> List[Dict[str, str]]:
        """解析 RSS/Atom，优先 bs4，失败回退到 ElementTree。"""
        entries: List[Dict[str, str]] = []
        if not content:
            return entries

        if HAS_BS4:
            try:
                soup = BeautifulSoup(content, "xml")
                items = soup.find_all("item") or soup.find_all("entry")
                for item in items:
                    title = self._safe_tag_text(item, "title")
                    description = (
                        self._safe_tag_text(item, "description")
                        or self._safe_tag_text(item, "summary")
                        or self._safe_tag_text(item, "content")
                    )
                    link_tag = item.find("link")
                    if link_tag is None:
                        link = ""
                    elif link_tag.get("href"):
                        link = link_tag.get("href")
                    else:
                        link = link_tag.text.strip() if link_tag.text else ""
                    published = (
                        self._safe_tag_text(item, "pubDate")
                        or self._safe_tag_text(item, "published")
                        or self._safe_tag_text(item, "updated")
                    )
                    entries.append(
                        {
                            "title": title,
                            "description": description,
                            "link": link,
                            "published": published,
                        }
                    )
                if entries:
                    return entries
            except Exception:
                pass

        try:
            root = ET.fromstring(content)
        except Exception:
            return entries

        def _strip_ns(tag: str) -> str:
            return tag.split("}", 1)[-1] if "}" in tag else tag

        nodes = []
        for el in root.iter():
            tag = _strip_ns(el.tag).lower()
            if tag in {"item", "entry"}:
                nodes.append(el)

        for node in nodes:
            data = {"title": "", "description": "", "link": "", "published": ""}
            for child in node:
                tag = _strip_ns(child.tag).lower()
                text = (child.text or "").strip()
                if tag == "title":
                    data["title"] = text
                elif tag in {"description", "summary", "content"} and not data["description"]:
                    data["description"] = text
                elif tag in {"pubdate", "published", "updated"} and not data["published"]:
                    data["published"] = text
                elif tag == "link":
                    data["link"] = child.attrib.get("href", "") or text
            entries.append(data)

        return entries

    def _parse_timestamp(self, date_str: str) -> int:
        """将日期文本解析为毫秒时间戳"""
        if not date_str:
            return int(datetime.now(timezone.utc).timestamp() * 1000)
        date_str = str(date_str).strip()
        try:
            dt = parsedate_to_datetime(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            pass
        try:
            normalized = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _generate_fallback_news(self, symbol: str, count: int = 12) -> List[Dict[str, Any]]:
        """新闻源不可用时的降级新闻"""
        base_asset = self._extract_base_asset(symbol)
        templates = [
            f"{base_asset} funding rate turns positive as traders position for rebound",
            f"Analysts debate whether {base_asset} is entering a new accumulation range",
            f"Whale transfer activity increases for {base_asset} amid volatility spike",
            f"Regulatory headlines create mixed sentiment for {base_asset} market",
            f"{base_asset} derivatives open interest expands while spot demand remains stable",
            f"On-chain metrics suggest long-term holders are adding {base_asset}",
        ]
        now = datetime.now(timezone.utc)
        news = []
        for idx in range(count):
            ts = int((now - timedelta(hours=idx * 3)).timestamp() * 1000)
            title = templates[idx % len(templates)]
            news.append(
                {
                    "id": f"fallback_{base_asset.lower()}_{idx}",
                    "title": title,
                    "content": title,
                    "source": "FallbackFeed",
                    "url": "",
                    "timestamp": ts,
                    "published_at": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat(),
                    "symbol": symbol,
                }
            )
        return news
    
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

