"""
主题建模服务 - LDA (Latent Dirichlet Allocation)
参考: BERTopic, Gensim LDA
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import re
import math


class TopicModelingService:
    """主题建模服务 - LDA 风格"""
    
    def __init__(self):
        # 加密货币主题关键词库
        self.topic_keywords = {
            "regulation": [
                "regulation", "sec", "cftc", "fed", "ban", "law", "legal",
                "compliance", "license", "audit", "监管", "法律", "合规", "禁止"
            ],
            "adoption": [
                "adoption", "institutional", "payment", "visa", "mastercard",
                "paypal", "merchant", "store", "采用", "机构", "支付", "商家"
            ],
            "technology": [
                "blockchain", "protocol", "upgrade", "fork", "scaling", "layer2",
                "ethereum", "solana", "polygon", "技术", "升级", "分叉", "扩容"
            ],
            "market": [
                "bull", "bear", "rally", "crash", "ath", "all-time", "high", "low",
                "牛市", "熊市", "上涨", "暴跌", "新高", "新低"
            ],
            "exchange": [
                "binance", "coinbase", "okx", "bybit", "listing", "delisting",
                "withdrawal", "deposit", "币安", "上市", "下架", "提币", "充币"
            ],
            "security": [
                "hack", "exploit", "vulnerability", "phish", "scam", "rug", "pull",
                "黑客", "漏洞", "钓鱼", "骗局", "跑路"
            ],
            "defi": [
                "defi", "lending", "borrowing", "yield", "farm", "staking", "liquidity",
                "pool", "dex", "uniswap", "去中心化", "借贷", "挖矿", "质押", "流动性"
            ],
            "nft": [
                "nft", "opensea", "collection", "mint", "metaverse", "gamefi",
                "play-to-earn", "非同质化", "元宇宙", "链游"
            ]
        }
        
        # 停用词
        self.stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "up", "down", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may", "might",
            "must", "shall", "can", "need", "dare", "ought", "used", "bitcoin",
            "btc", "eth", "ethereum", "crypto", "cryptocurrency", "price",
            "market", "trade", "trading", "token", "coin", "比特币", "以太坊"
        }
    
    def simple_lda_topic_modeling(
        self,
        texts: List[str],
        num_topics: int = 5,
        num_words: int = 10
    ) -> Dict[str, Any]:
        """
        简化版 LDA 主题建模
        
        基于关键词匹配和统计的主题识别
        """
        if not texts:
            return {"topics": []}
        
        # 1. 预处理所有文本
        all_words = []
        doc_words_list = []
        
        for text in texts:
            words = self._preprocess_text(text)
            doc_words_list.append(words)
            all_words.extend(words)
        
        # 2. 计算词频
        word_freq = Counter(all_words)
        
        # 3. 识别文档主题
        doc_topics = []
        topic_doc_counts = defaultdict(int)
        topic_word_counts = defaultdict(Counter)
        
        for doc_words in doc_words_list:
            # 统计文档中各主题的关键词匹配数
            topic_scores = defaultdict(float)
            
            for topic, keywords in self.topic_keywords.items():
                match_count = sum(1 for word in doc_words if word in keywords)
                if match_count > 0:
                    topic_scores[topic] = match_count
            
            # 确定文档主题
            if topic_scores:
                best_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
                doc_topics.append(best_topic)
                topic_doc_counts[best_topic] += 1
                
                # 收集该文档的高频词
                doc_word_freq = Counter(doc_words)
                for word, count in doc_word_freq.items():
                    if word not in self.stopwords and len(word) >= 3:
                        topic_word_counts[best_topic][word] += count
            else:
                doc_topics.append("other")
                topic_doc_counts["other"] += 1
        
        # 4. 生成主题结果
        topics = []
        total_docs = len(texts)
        
        for topic in sorted(topic_doc_counts.keys(), key=lambda x: -topic_doc_counts[x]):
            if topic == "other":
                continue
            
            doc_count = topic_doc_counts[topic]
            proportion = doc_count / total_docs
            
            # 获取该主题的关键词
            topic_words = topic_word_counts.get(topic, Counter())
            top_words = [
                word for word, count in topic_words.most_common(num_words)
                if word not in self.stopwords
            ][:num_words]
            
            # 如果没有足够的词，使用预定义的主题关键词
            if len(top_words) < 5:
                predef_words = self.topic_keywords.get(topic, [])
                top_words = list(dict.fromkeys(top_words + predef_words[:num_words]))[:num_words]
            
            topics.append({
                "topic_id": topic,
                "topic_name": self._get_topic_name(topic),
                "document_count": doc_count,
                "proportion": float(proportion),
                "top_words": top_words,
                "predefined_keywords": self.topic_keywords.get(topic, [])[:10]
            })
        
        # 5. 计算主题分布
        topic_distribution = {
            topic: float(count / total_docs)
            for topic, count in topic_doc_counts.items()
        }
        
        return {
            "num_documents": total_docs,
            "num_topics": len(topics),
            "topics": topics,
            "topic_distribution": topic_distribution,
            "document_topics": doc_topics,
            "timestamp": datetime.now().isoformat()
        }
    
    def extract_themes(
        self,
        texts: List[str],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        从文本中提取主题
        
        使用简化版主题提取
        """
        if not texts:
            return []
        
        # 1. 预处理和收集所有词
        all_words = []
        for text in texts:
            words = self._preprocess_text(text)
            all_words.extend(words)
        
        # 2. 计算词频
        word_freq = Counter(all_words)
        
        # 3. 过滤停用词和短词
        filtered_words = [
            (word, count) for word, count in word_freq.items()
            if word not in self.stopwords and len(word) >= 3
        ]
        
        # 4. 按词频排序
        filtered_words.sort(key=lambda x: -x[1])
        
        # 5. 识别主题
        themes = []
        used_words = set()
        
        for topic, keywords in self.topic_keywords.items():
            # 计算该主题的匹配分数
            score = 0
            matched_words = []
            
            for word, count in filtered_words:
                if word in keywords:
                    score += count
                    matched_words.append(word)
            
            if score > 0:
                themes.append({
                    "theme": self._get_topic_name(topic),
                    "theme_id": topic,
                    "score": score,
                    "matched_words": matched_words[:8]
                })
        
        # 6. 按分数排序
        themes.sort(key=lambda x: -x["score"])
        
        # 7. 添加高频词作为补充主题
        other_words = [
            word for word, count in filtered_words[:20]
            if word not in used_words
        ]
        
        if other_words:
            themes.append({
                "theme": "其他热门话题",
                "theme_id": "other",
                "score": 0,
                "matched_words": other_words[:10]
            })
        
        return themes[:top_n]
    
    def analyze_event_types(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        事件类型分析
        
        识别新闻中的事件类型
        """
        event_types = {
            "price_movement": [
                "soar", "surge", "rally", "jump", "rise", "gain", "grow",
                "drop", "fall", "plunge", "crash", "slide", "decline",
                "暴涨", "暴跌", "上涨", "下跌", "突破", "新高", "新低"
            ],
            "partnership": [
                "partnership", "collaboration", "alliance", "deal", "agreement",
                "合作", "联盟", "协议", "伙伴"
            ],
            "listing": [
                "list", "listing", "launch", "debut", "上市", "上线", "推出"
            ],
            "regulation": [
                "regulation", "law", "ban", "approve", "监管", "法律", "禁止", "批准"
            ],
            "security": [
                "hack", "exploit", "vulnerability", "attack",
                "黑客", "漏洞", "攻击", "安全"
            ],
            "technology": [
                "upgrade", "update", "fork", "launch", "release",
                "升级", "更新", "分叉", "发布"
            ]
        }
        
        text_lower = text.lower()
        detected_events = []
        
        for event_type, keywords in event_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_events.append({
                        "event_type": event_type,
                        "event_name": self._get_event_name(event_type),
                        "matched_keyword": keyword
                    })
                    break
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "detected_events": detected_events,
            "event_count": len(detected_events)
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
            if word not in self.stopwords
            and len(word) >= 2
        ]
        
        return words
    
    def _get_topic_name(self, topic_id: str) -> str:
        """获取主题名称"""
        topic_names = {
            "regulation": "监管政策",
            "adoption": "机构采用",
            "technology": "技术发展",
            "market": "市场动态",
            "exchange": "交易所",
            "security": "安全事件",
            "defi": "DeFi 生态",
            "nft": "NFT/元宇宙",
            "other": "其他"
        }
        return topic_names.get(topic_id, topic_id)
    
    def _get_event_name(self, event_type: str) -> str:
        """获取事件名称"""
        event_names = {
            "price_movement": "价格变动",
            "partnership": "合作关系",
            "listing": "上新上市",
            "regulation": "监管政策",
            "security": "安全事件",
            "technology": "技术更新"
        }
        return event_names.get(event_type, event_type)


# 全局实例
_topic_modeling_service = None


def get_topic_modeling_service() -> TopicModelingService:
    """获取主题建模服务单例"""
    global _topic_modeling_service
    if _topic_modeling_service is None:
        _topic_modeling_service = TopicModelingService()
    return _topic_modeling_service

