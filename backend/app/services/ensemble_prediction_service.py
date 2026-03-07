import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime
from collections import defaultdict
from scipy import stats


class EnsemblePredictionService:
    """多模型融合预测服务"""
    
    def __init__(self):
        self.model_weights = {
            "technical": 0.30,
            "machine_learning": 0.25,
            "pattern": 0.20,
            "sentiment": 0.15,
            "multi_timeframe": 0.10
        }
        self.prediction_history = defaultdict(list)
    
    def predict_ensemble(
        self,
        symbol: str,
        individual_predictions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        多模型融合预测
        
        参数:
            symbol: 交易对
            individual_predictions: 各模型的预测结果
                {
                    "technical": { "direction": "up", "confidence": 0.8, ... },
                    "machine_learning": { "direction": "up", "confidence": 0.7, ... },
                    ...
                }
        """
        
        # 1. 收集各模型预测
        model_results = []
        for model_name, pred in individual_predictions.items():
            if model_name in self.model_weights:
                model_results.append({
                    "model": model_name,
                    "direction": pred.get("direction", "sideways"),
                    "confidence": pred.get("confidence", 0.5),
                    "weight": self.model_weights.get(model_name, 0.1)
                })
        
        # 2. 计算加权投票
        up_score = 0.0
        down_score = 0.0
        sideways_score = 0.0
        
        for res in model_results:
            weight = res["weight"]
            conf = res["confidence"]
            weighted_conf = weight * conf
            
            if res["direction"] == "up":
                up_score += weighted_conf
            elif res["direction"] == "down":
                down_score += weighted_conf
            else:
                sideways_score += weighted_conf
        
        # 3. 确定最终预测
        total_score = up_score + down_score + sideways_score
        
        if total_score > 0:
            up_prob = up_score / total_score
            down_prob = down_score / total_score
            sideways_prob = sideways_score / total_score
        else:
            up_prob = down_prob = sideways_prob = 1/3
        
        if up_prob > down_prob and up_prob > sideways_prob:
            final_direction = "up"
            final_label = "🚀 融合看涨"
            final_confidence = up_prob
        elif down_prob > up_prob and down_prob > sideways_prob:
            final_direction = "down"
            final_label = "🔻 融合看跌"
            final_confidence = down_prob
        else:
            final_direction = "sideways"
            final_label = "➡️ 融合震荡"
            final_confidence = sideways_prob
        
        # 4. 计算模型一致性
        directions = [res["direction"] for res in model_results]
        unique_directions = set(directions)
        consensus = len(unique_directions) == 1
        
        # 5. 计算置信度稳定性
        confidences = [res["confidence"] for res in model_results]
        conf_std = np.std(confidences) if len(confidences) > 1 else 0
        
        # 6. 记录历史
        history_record = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "datetime": datetime.now().isoformat(),
            "symbol": symbol,
            "final_direction": final_direction,
            "final_confidence": float(final_confidence),
            "model_results": model_results,
            "probabilities": {
                "up": float(up_prob),
                "down": float(down_prob),
                "sideways": float(sideways_prob)
            }
        }
        self.prediction_history[symbol].append(history_record)
        
        return {
            "symbol": symbol,
            "final_direction": final_direction,
            "final_label": final_label,
            "final_confidence": float(final_confidence),
            "consensus": consensus,
            "confidence_stability": float(1 - conf_std),  # 越高越稳定
            "model_results": model_results,
            "probabilities": {
                "up": float(up_prob),
                "down": float(down_prob),
                "sideways": float(sideways_prob)
            },
            "history_record": history_record
        }
    
    def dynamic_weight_adjustment(
        self,
        symbol: str,
        actual_outcome: str,
        lookback: int = 20
    ) -> Dict[str, float]:
        """
        动态权重调整 - 根据历史预测准确率调整各模型权重
        
        参数:
            symbol: 交易对
            actual_outcome: 实际结果 ("up", "down", "sideways")
            lookback: 回看历史数量
        """
        
        if symbol not in self.prediction_history:
            return self.model_weights.copy()
        
        history = self.prediction_history[symbol][-lookback:]
        
        if not history:
            return self.model_weights.copy()
        
        # 计算各模型准确率
        model_accuracy = defaultdict(list)
        
        for record in history:
            for res in record["model_results"]:
                model = res["model"]
                pred_dir = res["direction"]
                is_correct = pred_dir == actual_outcome
                model_accuracy[model].append(1 if is_correct else 0)
        
        # 计算新权重
        new_weights = {}
        total_accuracy = 0.0
        
        for model in self.model_weights:
            if model in model_accuracy and model_accuracy[model]:
                accuracy = np.mean(model_accuracy[model])
            else:
                accuracy = 0.5  # 默认准确率
            
            new_weights[model] = accuracy
            total_accuracy += accuracy
        
        # 归一化
        if total_accuracy > 0:
            for model in new_weights:
                new_weights[model] = new_weights[model] / total_accuracy
        
        # 更新权重（平滑过渡）
        alpha = 0.3  # 学习率
        for model in self.model_weights:
            if model in new_weights:
                self.model_weights[model] = (
                    (1 - alpha) * self.model_weights[model] +
                    alpha * new_weights[model]
                )
        
        return self.model_weights.copy()
    
    def get_prediction_history(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取预测历史"""
        
        if symbol not in self.prediction_history:
            return []
        
        return self.prediction_history[symbol][-limit:]
    
    def get_backtest_metrics(
        self,
        symbol: str,
        actual_outcomes: List[Tuple[int, str]]
    ) -> Dict[str, Any]:
        """
        获取回测指标
        
        参数:
            symbol: 交易对
            actual_outcomes: 实际结果列表 [(timestamp, direction), ...]
        """
        
        if symbol not in self.prediction_history:
            return {
                "symbol": symbol,
                "message": "无预测历史"
            }
        
        history = self.prediction_history[symbol]
        
        if not history or not actual_outcomes:
            return {
                "symbol": symbol,
                "message": "数据不足"
            }
        
        # 匹配预测和实际结果
        matches = []
        outcome_dict = {ts: dir for ts, dir in actual_outcomes}
        
        for pred in history:
            pred_ts = pred["timestamp"]
            # 找最近的实际结果
            closest_ts = min(outcome_dict.keys(), key=lambda x: abs(x - pred_ts))
            actual_dir = outcome_dict[closest_ts]
            
            matches.append({
                "prediction": pred,
                "actual": actual_dir,
                "correct": pred["final_direction"] == actual_dir
            })
        
        # 计算指标
        total = len(matches)
        correct = sum(1 for m in matches if m["correct"])
        accuracy = correct / total if total > 0 else 0
        
        # 按方向计算准确率
        dir_accuracy = {}
        for direction in ["up", "down", "sideways"]:
            dir_matches = [m for m in matches if m["prediction"]["final_direction"] == direction]
            if dir_matches:
                dir_correct = sum(1 for m in dir_matches if m["correct"])
                dir_accuracy[direction] = dir_correct / len(dir_matches)
        
        # 按置信度分组
        conf_groups = defaultdict(list)
        for m in matches:
            conf = m["prediction"]["final_confidence"]
            group = int(conf * 10) / 10  # 0.1 分组
            conf_groups[group].append(m["correct"])
        
        conf_accuracy = {}
        for group in sorted(conf_groups.keys()):
            if conf_groups[group]:
                conf_accuracy[f"{group:.1f}-{group+0.1:.1f}"] = np.mean(conf_groups[group])
        
        return {
            "symbol": symbol,
            "total_predictions": total,
            "correct_predictions": correct,
            "overall_accuracy": float(accuracy),
            "direction_accuracy": dir_accuracy,
            "confidence_accuracy": conf_accuracy,
            "matches": matches[-20:]  # 最近20条
        }
    
    def calculate_price_range(
        self,
        current_price: float,
        volatility: float,
        prediction: Dict[str, Any],
        horizon_hours: int = 24
    ) -> Dict[str, float]:
        """
        计算价格区间
        
        参数:
            current_price: 当前价格
            volatility: 历史波动率（年化）
            prediction: 融合预测结果
            horizon_hours: 预测时间跨度（小时）
        """
        
        # 时间缩放（假设 24/7 交易）
        time_scalar = np.sqrt(horizon_hours / (365 * 24))
        horizon_volatility = volatility * time_scalar
        
        direction = prediction["final_direction"]
        confidence = prediction["final_confidence"]
        
        # 基于预测方向调整中心价格
        if direction == "up":
            center_multiplier = 1 + horizon_volatility * confidence * 0.5
        elif direction == "down":
            center_multiplier = 1 - horizon_volatility * confidence * 0.5
        else:
            center_multiplier = 1
        
        center_price = current_price * center_multiplier
        
        # 95% 置信区间 (1.96 * sigma)
        lower_bound = center_price * (1 - 1.96 * horizon_volatility)
        upper_bound = center_price * (1 + 1.96 * horizon_volatility)
        
        # 目标价格和止损价格
        if direction == "up":
            target_price = upper_bound * 0.9
            stop_loss = current_price * (1 - horizon_volatility * 0.5)
        elif direction == "down":
            target_price = lower_bound * 1.1
            stop_loss = current_price * (1 + horizon_volatility * 0.5)
        else:
            target_price = upper_bound * 0.95
            stop_loss = lower_bound * 1.05
        
        return {
            "current_price": float(current_price),
            "center_price": float(center_price),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "target_price": float(target_price),
            "stop_loss": float(stop_loss),
            "horizon_volatility": float(horizon_volatility),
            "horizon_hours": horizon_hours
        }


# 全局实例
_ensemble_prediction_service = None


def get_ensemble_prediction_service() -> EnsemblePredictionService:
    """获取多模型融合预测服务单例"""
    global _ensemble_prediction_service
    if _ensemble_prediction_service is None:
        _ensemble_prediction_service = EnsemblePredictionService()
    return _ensemble_prediction_service
