import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os
import threading
import time


class RealtimePredictionService:
    """实时预测更新服务"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "/root/.config/mihomo/realtime_prediction"
        self.updates_file = os.path.join(self.data_dir, "prediction_updates.jsonl")
        
        # 实时更新缓存
        self.latest_predictions = {}  # symbol -> latest prediction
        self.prediction_history = defaultdict(lambda: deque(maxlen=100))  # 每个symbol保留最近100条
        
        # 更新回调
        self.update_callbacks = []
        
        # 后台更新线程
        self.update_thread = None
        self.running = False
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载历史数据
        self._load_history()
    
    def _load_history(self):
        """加载历史数据"""
        if os.path.exists(self.updates_file):
            try:
                with open(self.updates_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            symbol = data.get("symbol")
                            if symbol:
                                self.prediction_history[symbol].append(data)
                                self.latest_predictions[symbol] = data
                        except:
                            pass
            except Exception as e:
                print(f"加载预测历史时出错: {e}")
    
    def _save_update(self, update: Dict[str, Any]):
        """保存更新记录"""
        try:
            with open(self.updates_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(update, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"保存预测更新时出错: {e}")
    
    def update_prediction(
        self,
        symbol: str,
        prediction: Dict[str, Any],
        source: str = "manual"
    ) -> Dict[str, Any]:
        """更新预测"""
        
        update_record = {
            "id": len(self.prediction_history[symbol]) + 1,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "datetime": datetime.now().isoformat(),
            "symbol": symbol,
            "prediction": prediction,
            "source": source,
            "version": len(self.prediction_history[symbol]) + 1
        }
        
        # 更新缓存
        self.prediction_history[symbol].append(update_record)
        self.latest_predictions[symbol] = update_record
        
        # 保存
        self._save_update(update_record)
        
        # 触发回调
        self._trigger_callbacks(update_record)
        
        return update_record
    
    def get_latest_prediction(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取最新预测"""
        return self.latest_predictions.get(symbol)
    
    def get_prediction_history(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取预测历史"""
        history = list(self.prediction_history.get(symbol, []))
        return history[-limit:]
    
    def get_all_latest_predictions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有最新预测"""
        return self.latest_predictions.copy()
    
    def register_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注册更新回调"""
        self.update_callbacks.append(callback)
    
    def unregister_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注销更新回调"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def _trigger_callbacks(self, update_record: Dict[str, Any]):
        """触发所有更新回调"""
        for callback in self.update_callbacks:
            try:
                callback(update_record)
            except Exception as e:
                print(f"触发更新回调时出错: {e}")
    
    def start_auto_update(
        self,
        update_func: Callable[[str], Dict[str, Any]],
        symbols: List[str],
        interval_seconds: int = 300
    ):
        """启动自动更新"""
        
        if self.running:
            return {
                "success": False,
                "message": "自动更新已在运行中"
            }
        
        self.running = True
        
        def update_loop():
            while self.running:
                try:
                    for symbol in symbols:
                        try:
                            prediction = update_func(symbol)
                            self.update_prediction(symbol, prediction, "auto")
                        except Exception as e:
                            print(f"自动更新 {symbol} 时出错: {e}")
                    
                    # 等待下一次更新
                    for _ in range(interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
                except Exception as e:
                    print(f"自动更新循环出错: {e}")
                    time.sleep(10)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
        return {
            "success": True,
            "message": f"已启动自动更新，间隔 {interval_seconds} 秒",
            "symbols": symbols,
            "interval_seconds": interval_seconds
        }
    
    def stop_auto_update(self):
        """停止自动更新"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        
        return {
            "success": True,
            "message": "已停止自动更新"
        }
    
    def get_prediction_changes(
        self,
        symbol: str,
        lookback: int = 10
    ) -> Dict[str, Any]:
        """获取预测变化分析"""
        
        history = self.get_prediction_history(symbol, lookback + 1)
        
        if len(history) < 2:
            return {
                "symbol": symbol,
                "message": "历史数据不足，无法分析变化"
            }
        
        latest = history[-1]
        previous = history[-(lookback + 1)] if len(history) > lookback else history[0]
        
        latest_pred = latest.get("prediction", {})
        prev_pred = previous.get("prediction", {})
        
        # 方向变化
        latest_dir = latest_pred.get("direction", "unknown")
        prev_dir = prev_pred.get("direction", "unknown")
        
        if latest_dir != prev_dir:
            direction_change = {
                "changed": True,
                "from": prev_dir,
                "to": latest_dir,
                "significance": "high"
            }
        else:
            direction_change = {
                "changed": False,
                "current": latest_dir
            }
        
        # 置信度变化
        latest_conf = latest_pred.get("confidence", 0)
        prev_conf = prev_pred.get("confidence", 0)
        conf_change = latest_conf - prev_conf
        
        # 价格预测变化
        latest_price = latest_pred.get("predicted_price")
        prev_price = prev_pred.get("predicted_price")
        price_change_pct = None
        if latest_price and prev_price and prev_price > 0:
            price_change_pct = (latest_price - prev_price) / prev_price
        
        # 变化等级
        if direction_change.get("changed"):
            change_level = "major"
            change_label = "🚨 重大变化"
        elif abs(conf_change) > 15:
            change_level = "significant"
            change_label = "⚠️ 显著变化"
        elif abs(conf_change) > 5:
            change_level = "moderate"
            change_label = "📊 适度变化"
        else:
            change_level = "minor"
            change_label = "➡️ 轻微变化"
        
        return {
            "symbol": symbol,
            "change_level": change_level,
            "change_label": change_label,
            "direction_change": direction_change,
            "confidence_change": {
                "previous": prev_conf,
                "current": latest_conf,
                "delta": conf_change
            },
            "price_change": {
                "previous": prev_price,
                "current": latest_price,
                "change_pct": price_change_pct
            },
            "latest_update": latest,
            "previous_update": previous,
            "time_span": {
                "start": previous.get("datetime"),
                "end": latest.get("datetime")
            }
        }
    
    def get_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """获取实时预测摘要"""
        
        if symbol:
            latest = self.get_latest_prediction(symbol)
            history = self.get_prediction_history(symbol, 20)
            changes = self.get_prediction_changes(symbol, 10)
            
            return {
                "symbol": symbol,
                "latest_prediction": latest,
                "history_count": len(history),
                "changes": changes
            }
        else:
            # 所有symbol的摘要
            all_latest = self.get_all_latest_predictions()
            
            summary = {
                "total_symbols": len(all_latest),
                "symbols": list(all_latest.keys()),
                "latest_predictions": all_latest,
                "generated_at": int(datetime.now().timestamp() * 1000),
                "generated_datetime": datetime.now().isoformat()
            }
            
            return summary


# 全局实例
_realtime_prediction_service = None


def get_realtime_prediction_service(data_dir: str = None) -> RealtimePredictionService:
    """获取实时预测服务单例"""
    global _realtime_prediction_service
    if _realtime_prediction_service is None:
        _realtime_prediction_service = RealtimePredictionService(data_dir)
    return _realtime_prediction_service
