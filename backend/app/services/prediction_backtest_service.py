import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os


class PredictionBacktestService:
    """预测结果回测验证服务"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "/root/.config/mihomo/prediction_backtest"
        self.predictions_file = os.path.join(self.data_dir, "predictions.jsonl")
        self.results_file = os.path.join(self.data_dir, "backtest_results.jsonl")
        
        # 缓存
        self.predictions = []
        self.backtest_results = []
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载历史数据
        self._load_data()
    
    def _load_data(self):
        """加载历史数据"""
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            self.predictions.append(data)
                        except:
                            pass
            except Exception as e:
                print(f"加载预测历史时出错: {e}")
        
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            self.backtest_results.append(data)
                        except:
                            pass
            except Exception as e:
                print(f"加载回测结果时出错: {e}")
    
    def _save_prediction(self, prediction: Dict[str, Any]):
        """保存预测记录"""
        self.predictions.append(prediction)
        try:
            with open(self.predictions_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(prediction, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"保存预测记录时出错: {e}")
    
    def _save_backtest_result(self, result: Dict[str, Any]):
        """保存回测结果"""
        self.backtest_results.append(result)
        try:
            with open(self.results_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"保存回测结果时出错: {e}")
    
    def record_prediction(
        self,
        symbol: str,
        prediction: Dict[str, Any],
        actual_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """记录一个新的预测"""
        
        record = {
            "id": len(self.predictions) + 1,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "datetime": datetime.now().isoformat(),
            "symbol": symbol,
            "prediction": prediction,
            "actual_price_at_prediction": actual_price,
            "verified": False,
            "verification_result": None
        }
        
        self._save_prediction(record)
        return record
    
    def verify_prediction(
        self,
        prediction_id: int,
        actual_price: float,
        actual_direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证一个预测"""
        
        # 找到预测记录
        prediction_record = None
        for p in self.predictions:
            if p.get("id") == prediction_id:
                prediction_record = p
                break
        
        if not prediction_record:
            return {
                "success": False,
                "error": f"预测记录 {prediction_id} 不存在"
            }
        
        # 计算验证结果
        prediction = prediction_record.get("prediction", {})
        predicted_direction = prediction.get("direction", "unknown")
        predicted_price = prediction.get("predicted_price")
        confidence = prediction.get("confidence", 0)
        
        # 判断方向是否正确
        direction_correct = None
        if actual_direction and predicted_direction != "unknown":
            direction_correct = (actual_direction == predicted_direction)
        
        # 计算价格误差
        price_error = None
        if predicted_price and actual_price:
            price_error = abs(actual_price - predicted_price) / predicted_price
        
        # 生成验证结果
        verification_result = {
            "verified_at": int(datetime.now().timestamp() * 1000),
            "verified_datetime": datetime.now().isoformat(),
            "actual_price": actual_price,
            "actual_direction": actual_direction,
            "direction_correct": direction_correct,
            "price_error": price_error,
            "confidence": confidence
        }
        
        # 更新预测记录
        prediction_record["verified"] = True
        prediction_record["verification_result"] = verification_result
        
        # 重新保存（简化处理：直接重写整个文件）
        self._rewrite_predictions_file()
        
        # 计算整体准确率
        accuracy_stats = self._calculate_accuracy_stats(prediction_record["symbol"])
        
        return {
            "success": True,
            "prediction": prediction_record,
            "accuracy_stats": accuracy_stats
        }
    
    def _rewrite_predictions_file(self):
        """重写预测文件"""
        try:
            with open(self.predictions_file, 'w', encoding='utf-8') as f:
                for p in self.predictions:
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"重写预测文件时出错: {e}")
    
    def _calculate_accuracy_stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """计算准确率统计"""
        
        verified_predictions = [
            p for p in self.predictions
            if p.get("verified", False)
        ]
        
        if symbol:
            verified_predictions = [
                p for p in verified_predictions
                if p.get("symbol") == symbol
            ]
        
        if not verified_predictions:
            return {
                "total_verified": 0,
                "correct_predictions": 0,
                "accuracy": 0,
                "avg_price_error": 0,
                "confidence_accuracy": {}
            }
        
        # 统计正确预测
        correct_predictions = [
            p for p in verified_predictions
            if p.get("verification_result", {}).get("direction_correct", False)
        ]
        
        # 计算价格误差
        price_errors = [
            p.get("verification_result", {}).get("price_error", 0)
            for p in verified_predictions
            if p.get("verification_result", {}).get("price_error") is not None
        ]
        
        # 按置信度统计准确率
        confidence_buckets = {
            "high (80-100)": {"total": 0, "correct": 0},
            "medium (50-80)": {"total": 0, "correct": 0},
            "low (0-50)": {"total": 0, "correct": 0}
        }
        
        for p in verified_predictions:
            conf = p.get("verification_result", {}).get("confidence", 0)
            correct = p.get("verification_result", {}).get("direction_correct", False)
            
            if conf >= 80:
                bucket = "high (80-100)"
            elif conf >= 50:
                bucket = "medium (50-80)"
            else:
                bucket = "low (0-50)"
            
            confidence_buckets[bucket]["total"] += 1
            if correct:
                confidence_buckets[bucket]["correct"] += 1
        
        # 计算每个置信度的准确率
        confidence_accuracy = {}
        for bucket, stats in confidence_buckets.items():
            if stats["total"] > 0:
                confidence_accuracy[bucket] = {
                    "total": stats["total"],
                    "correct": stats["correct"],
                    "accuracy": stats["correct"] / stats["total"]
                }
        
        return {
            "total_verified": len(verified_predictions),
            "correct_predictions": len(correct_predictions),
            "accuracy": len(correct_predictions) / len(verified_predictions) if verified_predictions else 0,
            "avg_price_error": np.mean(price_errors) if price_errors else 0,
            "confidence_accuracy": confidence_accuracy
        }
    
    def get_predictions(
        self,
        symbol: Optional[str] = None,
        verified: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取预测历史"""
        
        predictions = list(self.predictions)
        
        if symbol:
            predictions = [p for p in predictions if p.get("symbol") == symbol]
        
        if verified is not None:
            predictions = [p for p in predictions if p.get("verified", False) == verified]
        
        return predictions[-limit:]
    
    def get_backtest_report(
        self,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取回测报告"""
        
        accuracy_stats = self._calculate_accuracy_stats(symbol)
        
        # 最近预测
        recent_predictions = self.get_predictions(symbol=symbol, limit=20)
        
        # 预测趋势
        if len(recent_predictions) >= 10:
            recent_accuracies = []
            for p in recent_predictions[-10:]:
                if p.get("verified", False):
                    correct = p.get("verification_result", {}).get("direction_correct", False)
                    recent_accuracies.append(1 if correct else 0)
            
            if recent_accuracies:
                accuracy_trend = np.mean(recent_accuracies)
            else:
                accuracy_trend = None
        else:
            accuracy_trend = None
        
        # 总体评级
        accuracy = accuracy_stats.get("accuracy", 0)
        if accuracy >= 0.8:
            grade = "S"
            label = "🏆 预测大师"
        elif accuracy >= 0.65:
            grade = "A"
            label = "⭐ 准确预测"
        elif accuracy >= 0.55:
            grade = "B"
            label = "👍 基本准确"
        elif accuracy >= 0.5:
            grade = "C"
            label = "⚠️ 需要改进"
        else:
            grade = "D"
            label = "🚨 预测较差"
        
        return {
            "symbol": symbol or "all",
            "generated_at": int(datetime.now().timestamp() * 1000),
            "generated_datetime": datetime.now().isoformat(),
            "accuracy_stats": accuracy_stats,
            "recent_predictions": recent_predictions,
            "accuracy_trend": accuracy_trend,
            "grade": grade,
            "label": label
        }
    
    def run_mock_backtest(
        self,
        symbol: str,
        num_predictions: int = 50
    ) -> Dict[str, Any]:
        """运行模拟回测（用于测试）"""
        
        np.random.seed(42)
        
        # 生成模拟预测
        for i in range(num_predictions):
            # 随机生成预测
            direction = np.random.choice(["up", "down"], p=[0.5, 0.5])
            confidence = np.random.uniform(30, 95)
            predicted_price = 0.5 * (1 + np.random.normal(0, 0.05))
            
            prediction = {
                "direction": direction,
                "confidence": confidence,
                "predicted_price": predicted_price,
                "timeframe": "5h"
            }
            
            # 记录预测
            self.record_prediction(symbol, prediction, 0.5)
            
            # 立即验证（模拟）
            # 让准确率与置信度正相关
            accuracy_prob = confidence / 100 * 0.7 + 0.3  # 30%-100% 概率正确
            actual_direction = direction if np.random.random() < accuracy_prob else ("down" if direction == "up" else "up")
            actual_price = predicted_price * (1 + np.random.normal(0, 0.02))
            
            # 验证
            prediction_id = len(self.predictions)
            self.verify_prediction(prediction_id, actual_price, actual_direction)
        
        # 生成报告
        report = self.get_backtest_report(symbol)
        
        return {
            "success": True,
            "message": f"已完成 {num_predictions} 个模拟预测的回测",
            "report": report
        }


# 全局实例
_prediction_backtest_service = None


def get_prediction_backtest_service(data_dir: str = None) -> PredictionBacktestService:
    """获取预测回测服务单例"""
    global _prediction_backtest_service
    if _prediction_backtest_service is None:
        _prediction_backtest_service = PredictionBacktestService(data_dir)
    return _prediction_backtest_service
