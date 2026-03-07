import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os


class RealtimeSentimentService:
    """实时舆情监控服务"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "/root/.config/mihomo/sentiment_data"
        self.history_file = os.path.join(self.data_dir, "sentiment_history.jsonl")
        self.alert_history_file = os.path.join(self.data_dir, "alert_history.jsonl")
        
        # 历史数据缓存
        self.history = deque(maxlen=1000)  # 保留最近1000条
        self.alerts = deque(maxlen=500)    # 保留最近500条
        self.current_sentiment = None
        
        # 加载历史数据
        self._load_history()
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_history(self):
        """加载历史数据"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            self.history.append(data)
                        except:
                            pass
            except Exception as e:
                print(f"加载历史数据时出错: {e}")
        
        if os.path.exists(self.alert_history_file):
            try:
                with open(self.alert_history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            self.alerts.append(data)
                        except:
                            pass
            except Exception as e:
                print(f"加载预警历史时出错: {e}")
    
    def _save_history(self, data: Dict[str, Any]):
        """保存历史数据"""
        self.history.append(data)
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"保存历史数据时出错: {e}")
    
    def _save_alert(self, alert: Dict[str, Any]):
        """保存预警"""
        self.alerts.append(alert)
        try:
            with open(self.alert_history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"保存预警时出错: {e}")
    
    def update_sentiment(self, keyword: str, sentiment_data: Dict[str, Any]):
        """更新舆情数据"""
        
        record = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "datetime": datetime.now().isoformat(),
            "keyword": keyword,
            "data": sentiment_data
        }
        
        self.current_sentiment = record
        self._save_history(record)
        
        # 检查是否触发预警
        alerts = self._check_alerts(keyword, sentiment_data, record)
        
        return {
            "success": True,
            "record": record,
            "alerts": alerts
        }
    
    def _check_alerts(
        self,
        keyword: str,
        sentiment_data: Dict[str, Any],
        record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检查舆情预警"""
        
        alerts = []
        overall_score = sentiment_data.get("overall_score", {})
        score = overall_score.get("score", 50)
        
        # 获取历史数据用于比较
        prev_records = list(self.history)[-10:-1] if len(self.history) > 1 else []
        
        # 预警1：分数突变
        if prev_records:
            prev_score = prev_records[-1].get("data", {}).get("overall_score", {}).get("score", 50)
            score_change = abs(score - prev_score)
            
            if score_change > 15:
                alert = {
                    "id": len(self.alerts) + 1,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "datetime": datetime.now().isoformat(),
                    "type": "score_jump",
                    "level": "warning" if score_change > 20 else "info",
                    "keyword": keyword,
                    "title": "舆情分数突变",
                    "message": f"舆情分数从 {prev_score:.1f} 变化到 {score:.1f}，变化幅度 {score_change:.1f}",
                    "data": {
                        "prev_score": prev_score,
                        "current_score": score,
                        "change": score_change
                    }
                }
                alerts.append(alert)
                self._save_alert(alert)
        
        # 预警2：分数过高/过低
        if score > 85:
            alert = {
                "id": len(self.alerts) + 1,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "datetime": datetime.now().isoformat(),
                "type": "extreme_positive",
                "level": "warning",
                "keyword": keyword,
                "title": "舆情极度乐观",
                "message": f"舆情分数达到 {score:.1f}，处于极度乐观区间，注意可能的回调风险",
                "data": {"score": score}
            }
            alerts.append(alert)
            self._save_alert(alert)
        elif score < 25:
            alert = {
                "id": len(self.alerts) + 1,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "datetime": datetime.now().isoformat(),
                "type": "extreme_negative",
                "level": "warning",
                "keyword": keyword,
                "title": "舆情极度悲观",
                "message": f"舆情分数低至 {score:.1f}，处于极度悲观区间，关注是否有超卖机会",
                "data": {"score": score}
            }
            alerts.append(alert)
            self._save_alert(alert)
        
        # 预警3：新闻情感突变
        news_sentiment = sentiment_data.get("news_sentiment", {})
        news_score = news_sentiment.get("sentiment_score", 0)
        
        if len(prev_records) >= 3:
            prev_news_scores = [
                r.get("data", {}).get("news_sentiment", {}).get("sentiment_score", 0)
                for r in prev_records[-3:]
            ]
            avg_prev_news = sum(prev_news_scores) / len(prev_news_scores)
            news_change = abs(news_score - avg_prev_news)
            
            if news_change > 0.4:
                alert = {
                    "id": len(self.alerts) + 1,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "datetime": datetime.now().isoformat(),
                    "type": "news_sentiment_jump",
                    "level": "info",
                    "keyword": keyword,
                    "title": "新闻情感突变",
                    "message": f"新闻情感从平均 {avg_prev_news:.2f} 变化到 {news_score:.2f}",
                    "data": {
                        "avg_prev": avg_prev_news,
                        "current": news_score,
                        "change": news_change
                    }
                }
                alerts.append(alert)
                self._save_alert(alert)
        
        return alerts
    
    def get_realtime_status(self, keyword: str) -> Dict[str, Any]:
        """获取实时舆情状态"""
        
        # 最近数据
        recent = list(self.history)[-50:]
        keyword_recent = [r for r in recent if r.get("keyword") == keyword]
        
        if not keyword_recent:
            return {
                "keyword": keyword,
                "status": "no_data",
                "message": "暂无该关键词的舆情数据"
            }
        
        latest = keyword_recent[-1]
        latest_data = latest.get("data", {})
        
        # 趋势分析
        if len(keyword_recent) >= 10:
            recent_scores = [
                r.get("data", {}).get("overall_score", {}).get("score", 50)
                for r in keyword_recent[-10:]
            ]
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            
            if trend > 0.5:
                trend_label = "📈 快速上升"
            elif trend > 0.1:
                trend_label = "📈 缓慢上升"
            elif trend < -0.5:
                trend_label = "📉 快速下降"
            elif trend < -0.1:
                trend_label = "📉 缓慢下降"
            else:
                trend_label = "➡️ 稳定"
        else:
            trend_label = "➡️ 数据不足"
            trend = 0
        
        # 最近预警
        recent_alerts = [
            a for a in list(self.alerts)[-10:]
            if a.get("keyword") == keyword
        ]
        
        return {
            "keyword": keyword,
            "status": "active",
            "latest": latest,
            "latest_data": latest_data,
            "trend": {
                "label": trend_label,
                "slope": float(trend)
            },
            "recent_alerts": recent_alerts[:5],
            "data_points": len(keyword_recent)
        }
    
    def get_history(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史舆情数据"""
        
        keyword_history = [
            r for r in list(self.history)
            if r.get("keyword") == keyword
        ]
        
        return keyword_history[-limit:]
    
    def get_alerts(
        self,
        keyword: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取预警历史"""
        
        alerts = list(self.alerts)
        
        if keyword:
            alerts = [a for a in alerts if a.get("keyword") == keyword]
        
        if level:
            alerts = [a for a in alerts if a.get("level") == level]
        
        return alerts[-limit:]
    
    def get_summary(self, keyword: str) -> Dict[str, Any]:
        """获取舆情摘要"""
        
        history = self.get_history(keyword, limit=200)
        
        if not history:
            return {
                "keyword": keyword,
                "summary": "暂无数据"
            }
        
        # 统计数据
        scores = [
            r.get("data", {}).get("overall_score", {}).get("score", 50)
            for r in history
        ]
        
        news_scores = [
            r.get("data", {}).get("news_sentiment", {}).get("sentiment_score", 0)
            for r in history
        ]
        
        social_scores = [
            r.get("data", {}).get("social_sentiment", {}).get("overall_sentiment", 0)
            for r in history
        ]
        
        return {
            "keyword": keyword,
            "period": {
                "start": history[0].get("datetime") if history else None,
                "end": history[-1].get("datetime") if history else None,
                "count": len(history)
            },
            "overall_score": {
                "min": float(min(scores)),
                "max": float(max(scores)),
                "mean": float(np.mean(scores)),
                "std": float(np.std(scores)),
                "current": float(scores[-1]) if scores else 50
            },
            "news_sentiment": {
                "min": float(min(news_scores)),
                "max": float(max(news_scores)),
                "mean": float(np.mean(news_scores)),
                "current": float(news_scores[-1]) if news_scores else 0
            },
            "social_sentiment": {
                "min": float(min(social_scores)),
                "max": float(max(social_scores)),
                "mean": float(np.mean(social_scores)),
                "current": float(social_scores[-1]) if social_scores else 0
            },
            "alert_count": len([
                a for a in list(self.alerts)
                if a.get("keyword") == keyword
            ])
        }


# 全局实例
_realtime_sentiment_service = None


def get_realtime_sentiment_service(data_dir: str = None) -> RealtimeSentimentService:
    """获取实时舆情服务单例"""
    global _realtime_sentiment_service
    if _realtime_sentiment_service is None:
        _realtime_sentiment_service = RealtimeSentimentService(data_dir)
    return _realtime_sentiment_service
