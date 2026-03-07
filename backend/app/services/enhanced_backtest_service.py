"""
增强回测系统服务 - 参考 Freqtrade、Backtrader、Jesse
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Trade:
    """交易记录"""
    timestamp: int
    symbol: str
    side: str  # "buy" or "sell"
    price: float
    amount: float
    value: float
    reason: str
    balance_before: float
    balance_after: float


@dataclass
class Position:
    """持仓记录"""
    symbol: str
    amount: float
    avg_price: float
    entry_timestamp: int
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class EnhancedBacktestService:
    """增强回测系统服务"""
    
    def __init__(self):
        self.initial_balance = 10000.0
        self.commission_rate = 0.001  # 0.1% 手续费
        self.slippage = 0.001  # 0.1% 滑点
        self.trades: List[Trade] = []
        self.positions: Dict[str, Position] = {}
        self.equity_curve: List[Dict[str, Any]] = []
        self.drawdowns: List[Dict[str, Any]] = []
        
    def reset(self):
        """重置回测状态"""
        self.trades = []
        self.positions = {}
        self.equity_curve = []
        self.drawdowns = []
        
    def run_backtest(
        self,
        df: pd.DataFrame,
        signal_func: Callable[[pd.DataFrame, int], Optional[str]],
        initial_balance: float = 10000.0,
        symbol: str = "BTCUSDT"
    ) -> Dict[str, Any]:
        """
        运行回测
        
        参数:
            df: K线数据 DataFrame
            signal_func: 信号生成函数 (df, idx) -> "buy" | "sell" | None
            initial_balance: 初始资金
            symbol: 交易对
        """
        self.reset()
        self.initial_balance = initial_balance
        balance = initial_balance
        
        for idx in range(len(df)):
            current_data = df.iloc[idx]
            current_price = current_data["close"]
            
            # 生成交易信号
            signal = signal_func(df, idx)
            
            # 执行交易
            if signal == "buy" and symbol not in self.positions:
                # 买入
                amount = (balance * 0.95) / current_price  # 使用 95% 资金
                commission = amount * current_price * self.commission_rate
                slippage_price = current_price * (1 + self.slippage)
                total_cost = amount * slippage_price + commission
                
                if total_cost <= balance:
                    balance_before = balance
                    balance -= total_cost
                    
                    position = Position(
                        symbol=symbol,
                        amount=amount,
                        avg_price=slippage_price,
                        entry_timestamp=int(current_data.get("timestamp", idx))
                    )
                    self.positions[symbol] = position
                    
                    trade = Trade(
                        timestamp=int(current_data.get("timestamp", idx)),
                        symbol=symbol,
                        side="buy",
                        price=slippage_price,
                        amount=amount,
                        value=total_cost,
                        reason="strategy_signal",
                        balance_before=balance_before,
                        balance_after=balance
                    )
                    self.trades.append(trade)
            
            elif signal == "sell" and symbol in self.positions:
                # 卖出
                position = self.positions[symbol]
                slippage_price = current_price * (1 - self.slippage)
                revenue = position.amount * slippage_price
                commission = revenue * self.commission_rate
                net_revenue = revenue - commission
                
                balance_before = balance
                balance += net_revenue
                
                # 计算盈亏
                pnl = net_revenue - (position.amount * position.avg_price)
                position.realized_pnl = pnl
                
                trade = Trade(
                    timestamp=int(current_data.get("timestamp", idx)),
                    symbol=symbol,
                    side="sell",
                    price=slippage_price,
                    amount=position.amount,
                    value=net_revenue,
                    reason="strategy_signal",
                    balance_before=balance_before,
                    balance_after=balance
                )
                self.trades.append(trade)
                
                del self.positions[symbol]
            
            # 更新未实现盈亏
            if symbol in self.positions:
                position = self.positions[symbol]
                unrealized_pnl = (current_price - position.avg_price) * position.amount
                position.unrealized_pnl = unrealized_pnl
            
            # 记录资金曲线
            total_equity = balance
            if symbol in self.positions:
                position = self.positions[symbol]
                total_equity += position.amount * current_price
            
            self.equity_curve.append({
                "timestamp": int(current_data.get("timestamp", idx)),
                "datetime": datetime.fromtimestamp(
                    current_data.get("timestamp", idx) / 1000
                ).isoformat() if "timestamp" in current_data else "",
                "balance": float(balance),
                "total_equity": float(total_equity),
                "positions": dict(self.positions)
            })
        
        # 计算回测指标
        metrics = self.calculate_metrics(df)
        
        return {
            "initial_balance": self.initial_balance,
            "final_balance": float(balance),
            "total_trades": len(self.trades),
            "winning_trades": sum(1 for t in self.trades if t.side == "sell"),
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "metrics": metrics,
            "drawdowns": self.drawdowns
        }
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算回测指标"""
        if not self.equity_curve:
            return {}
        
        equity = [e["total_equity"] for e in self.equity_curve]
        returns = pd.Series(equity).pct_change().dropna()
        
        # 基础指标
        total_return = (equity[-1] - self.initial_balance) / self.initial_balance
        
        # 年化收益率（假设 365 天）
        days = len(df) / 24  # 假设是小时数据
        annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1
        
        # 波动率
        volatility = returns.std() * np.sqrt(365 * 24)
        
        # 夏普比率（假设无风险利率 0）
        sharpe_ratio = annual_return / (volatility + 1e-10) if volatility > 0 else 0
        
        # 最大回撤
        peak = equity[0]
        max_drawdown = 0
        peak_idx = 0
        trough_idx = 0
        
        for i, val in enumerate(equity):
            if val > peak:
                peak = val
                peak_idx = i
            drawdown = (peak - val) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                trough_idx = i
        
        # 卡玛比率
        calmar_ratio = annual_return / (max_drawdown + 1e-10) if max_drawdown > 0 else 0
        
        # 交易指标
        sell_trades = [t for t in self.trades if t.side == "sell"]
        if sell_trades:
            profits = []
            for sell_trade in sell_trades:
                # 找到对应的买入交易
                buy_trade = next(
                    (t for t in self.trades if t.side == "buy" and t.timestamp < sell_trade.timestamp),
                    None
                )
                if buy_trade:
                    profit = sell_trade.balance_after - buy_trade.balance_before
                    profits.append(profit)
            
            if profits:
                win_rate = sum(1 for p in profits if p > 0) / len(profits)
                avg_profit = np.mean(profits)
                avg_win = np.mean([p for p in profits if p > 0]) if any(p > 0 for p in profits) else 0
                avg_loss = np.mean([p for p in profits if p < 0]) if any(p < 0 for p in profits) else 0
                profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            else:
                win_rate = 0
                avg_profit = 0
                avg_win = 0
                avg_loss = 0
                profit_factor = 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        return {
            "total_return": float(total_return),
            "total_return_pct": float(total_return * 100),
            "annual_return": float(annual_return),
            "annual_return_pct": float(annual_return * 100),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "max_drawdown_pct": float(max_drawdown * 100),
            "calmar_ratio": float(calmar_ratio),
            "win_rate": float(win_rate),
            "win_rate_pct": float(win_rate * 100),
            "avg_profit": float(avg_profit),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "profit_factor": float(profit_factor),
            "total_trades": len(self.trades),
            "buy_trades": sum(1 for t in self.trades if t.side == "buy"),
            "sell_trades": len(sell_trades)
        }
    
    def simple_ma_crossover_strategy(
        self,
        df: pd.DataFrame,
        idx: int,
        fast_period: int = 5,
        slow_period: int = 20
    ) -> Optional[str]:
        """简单移动平均线交叉策略"""
        if idx < slow_period:
            return None
        
        close = df["close"]
        fast_ma = close.rolling(fast_period).mean()
        slow_ma = close.rolling(slow_period).mean()
        
        # 金叉：短期均线上穿长期均线
        if fast_ma.iloc[idx] > slow_ma.iloc[idx] and fast_ma.iloc[idx-1] <= slow_ma.iloc[idx-1]:
            return "buy"
        
        # 死叉：短期均线下穿长期均线
        if fast_ma.iloc[idx] < slow_ma.iloc[idx] and fast_ma.iloc[idx-1] >= slow_ma.iloc[idx-1]:
            return "sell"
        
        return None
    
    def rsi_strategy(
        self,
        df: pd.DataFrame,
        idx: int,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70
    ) -> Optional[str]:
        """RSI 策略"""
        if idx < period + 1:
            return None
        
        # 计算 RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[idx]
        prev_rsi = rsi.iloc[idx-1]
        
        # RSI 从超卖区回升
        if prev_rsi <= oversold and current_rsi > oversold:
            return "buy"
        
        # RSI 从超买区回落
        if prev_rsi >= overbought and current_rsi < overbought:
            return "sell"
        
        return None
    
    def bollinger_bands_strategy(
        self,
        df: pd.DataFrame,
        idx: int,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Optional[str]:
        """布林带策略"""
        if idx < period + 1:
            return None
        
        close = df["close"]
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        current_close = close.iloc[idx]
        current_upper = upper.iloc[idx]
        current_lower = lower.iloc[idx]
        
        # 价格跌破下轨 → 买入
        if current_close < current_lower:
            return "buy"
        
        # 价格突破上轨 → 卖出
        if current_close > current_upper:
            return "sell"
        
        return None


# 全局实例
_enhanced_backtest_service = None


def get_enhanced_backtest_service() -> EnhancedBacktestService:
    """获取增强回测服务单例"""
    global _enhanced_backtest_service
    if _enhanced_backtest_service is None:
        _enhanced_backtest_service = EnhancedBacktestService()
    return _enhanced_backtest_service

