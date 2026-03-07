import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid


class SimulationService:
    """模拟交易（Dry-run）服务"""
    
    def __init__(self):
        self.accounts = {}  # 模拟账户
        self.orders = defaultdict(list)  # 订单历史
        self.trades = defaultdict(list)  # 成交历史
        self.positions = defaultdict(dict)  # 持仓
    
    def create_account(self, initial_balance: float = 10000.0, name: str = "模拟账户") -> str:
        """创建模拟账户"""
        
        account_id = str(uuid.uuid4())
        
        self.accounts[account_id] = {
            "account_id": account_id,
            "name": name,
            "initial_balance": initial_balance,
            "current_balance": initial_balance,
            "available_balance": initial_balance,
            "unrealized_pnl": 0.0,
            "realized_pnl": 0.0,
            "created_at": int(datetime.now().timestamp() * 1000),
            "is_active": True
        }
        
        return account_id
    
    def place_order(
        self,
        account_id: str,
        symbol: str,
        side: str,  # buy/sell
        order_type: str,  # market/limit
        quantity: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """下单"""
        
        if account_id not in self.accounts:
            return {"success": False, "error": "账户不存在"}
        
        account = self.accounts[account_id]
        
        if not account["is_active"]:
            return {"success": False, "error": "账户已停用"}
        
        # 获取当前价格（模拟）
        current_price = self._get_current_price(symbol)
        
        # 确定成交价格
        if order_type == "market":
            exec_price = current_price
        elif order_type == "limit" and price:
            # 检查是否可以成交
            if side == "buy" and price >= current_price:
                exec_price = price
            elif side == "sell" and price <= current_price:
                exec_price = price
            else:
                # 限价单暂时无法成交，加入订单簿
                order_id = str(uuid.uuid4())
                order = {
                    "order_id": order_id,
                    "account_id": account_id,
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "price": price,
                    "status": "pending",
                    "created_at": int(datetime.now().timestamp() * 1000),
                    "filled_quantity": 0
                }
                self.orders[account_id].append(order)
                return {
                    "success": True,
                    "data": {
                        "order_id": order_id,
                        "status": "pending",
                        "message": "限价单已挂单，等待成交"
                    }
                }
        else:
            return {"success": False, "error": "无效的订单类型"}
        
        # 检查余额和持仓
        cost = exec_price * quantity
        
        if side == "buy":
            if account["available_balance"] < cost:
                return {"success": False, "error": "可用余额不足"}
        elif side == "sell":
            current_position = self.positions[account_id].get(symbol, 0)
            if current_position < quantity:
                return {"success": False, "error": "持仓不足"}
        
        # 执行交易
        order_id = str(uuid.uuid4())
        trade_id = str(uuid.uuid4())
        
        trade = {
            "trade_id": trade_id,
            "order_id": order_id,
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": exec_price,
            "value": cost,
            "fee": cost * 0.001,  # 模拟手续费 0.1%
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        
        self.trades[account_id].append(trade)
        
        # 更新账户和持仓
        if side == "buy":
            account["available_balance"] -= cost + trade["fee"]
            self.positions[account_id][symbol] = self.positions[account_id].get(symbol, 0) + quantity
        elif side == "sell":
            account["available_balance"] += cost - trade["fee"]
            self.positions[account_id][symbol] -= quantity
            if self.positions[account_id][symbol] == 0:
                del self.positions[account_id][symbol]
        
        # 计算未实现盈亏
        self._update_unrealized_pnl(account_id)
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "trade_id": trade_id,
                "status": "filled",
                "price": exec_price,
                "quantity": quantity
            }
        }
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """获取账户信息"""
        
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id].copy()
        
        # 更新未实现盈亏
        self._update_unrealized_pnl(account_id)
        
        # 添加持仓信息
        account["positions"] = []
        for symbol, quantity in self.positions[account_id].items():
            current_price = self._get_current_price(symbol)
            position_value = quantity * current_price
            account["positions"].append({
                "symbol": symbol,
                "quantity": quantity,
                "current_price": current_price,
                "position_value": position_value
            })
        
        return account
    
    def get_trades(self, account_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取交易历史"""
        
        if account_id not in self.trades:
            return []
        
        return self.trades[account_id][-limit:]
    
    def get_orders(self, account_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取订单历史"""
        
        if account_id not in self.orders:
            return []
        
        return self.orders[account_id][-limit:]
    
    def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        
        if account_id not in self.orders:
            return {"success": False, "error": "账户不存在"}
        
        for i, order in enumerate(self.orders[account_id]):
            if order["order_id"] == order_id:
                if order["status"] == "pending":
                    order["status"] = "cancelled"
                    return {
                        "success": True,
                        "data": {"order_id": order_id, "status": "cancelled"}
                    }
                else:
                    return {"success": False, "error": "订单已成交或已取消"}
        
        return {"success": False, "error": "订单不存在"}
    
    def get_performance(self, account_id: str) -> Optional[Dict[str, Any]]:
        """获取账户表现"""
        
        account = self.get_account(account_id)
        if not account:
            return None
        
        trades = self.get_trades(account_id)
        
        # 计算表现指标
        total_return = (account["current_balance"] - account["initial_balance"]) / account["initial_balance"]
        realized_pnl = account["realized_pnl"]
        unrealized_pnl = account["unrealized_pnl"]
        
        # 计算胜率
        buy_trades = [t for t in trades if t["side"] == "buy"]
        sell_trades = [t for t in trades if t["side"] == "sell"]
        profitable_trades = len([t for t in trades if t.get("pnl", 0) > 0])
        
        win_rate = profitable_trades / len(trades) if trades else 0
        
        # 计算最大回撤（简化）
        balance_history = self._generate_balance_history(account_id)
        if balance_history:
            series = pd.Series([b["balance"] for b in balance_history])
            cummax = series.cummax()
            drawdown = (cummax - series) / cummax
            max_drawdown = drawdown.max()
        else:
            max_drawdown = 0
        
        return {
            "account_id": account_id,
            "total_return": float(total_return),
            "realized_pnl": float(realized_pnl),
            "unrealized_pnl": float(unrealized_pnl),
            "total_trades": len(trades),
            "win_rate": float(win_rate),
            "max_drawdown": float(max_drawdown),
            "balance_history": balance_history[-100:]  # 最近100个时间点
        }
    
    def _get_current_price(self, symbol: str) -> float:
        """获取当前价格（模拟）"""
        
        # 基础价格
        base_price = 0.5 if symbol.upper().startswith("RIVER") else 50000
        
        # 模拟价格波动
        np.random.seed(int(datetime.now().timestamp()) % 10000)
        fluctuation = np.random.normal(0, 0.005)
        
        return base_price * (1 + fluctuation)
    
    def _update_unrealized_pnl(self, account_id: str):
        """更新未实现盈亏"""
        
        if account_id not in self.accounts:
            return
        
        account = self.accounts[account_id]
        
        unrealized_pnl = 0.0
        position_value = 0.0
        
        for symbol, quantity in self.positions[account_id].items():
            current_price = self._get_current_price(symbol)
            position_value += quantity * current_price
            # 简化计算：假设开仓价是当前价的 99%
            entry_price = current_price * 0.99
            unrealized_pnl += (current_price - entry_price) * quantity
        
        account["unrealized_pnl"] = unrealized_pnl
        account["current_balance"] = account["available_balance"] + position_value
    
    def _generate_balance_history(self, account_id: str) -> List[Dict[str, Any]]:
        """生成余额历史（简化）"""
        
        if account_id not in self.accounts:
            return []
        
        account = self.accounts[account_id]
        trades = self.get_trades(account_id)
        
        history = []
        
        if not trades:
            # 没有交易，返回初始余额
            history.append({
                "timestamp": account["created_at"],
                "balance": account["initial_balance"],
                "cash": account["initial_balance"],
                "position_value": 0
            })
        else:
            # 从交易记录生成
            current_balance = account["initial_balance"]
            for trade in trades:
                if trade["side"] == "buy":
                    current_balance -= trade["value"] + trade["fee"]
                elif trade["side"] == "sell":
                    current_balance += trade["value"] - trade["fee"]
                
                history.append({
                    "timestamp": trade["timestamp"],
                    "balance": current_balance,
                    "cash": current_balance,
                    "position_value": 0  # 简化
                })
            
            # 添加当前状态
            history.append({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "balance": account["current_balance"],
                "cash": account["available_balance"],
                "position_value": account["unrealized_pnl"]
            })
        
        return history


# 全局实例
_simulation_service = None


def get_simulation_service() -> SimulationService:
    """获取模拟交易服务单例"""
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service
