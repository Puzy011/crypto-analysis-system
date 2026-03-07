import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class BacktestService:
    """策略回测服务"""
    
    @staticmethod
    def run_backtest(
        symbol: str,
        initial_balance: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005
    ) -> Dict[str, Any]:
        """运行策略回测"""
        
        # 生成模拟历史数据
        klines = BacktestService._generate_mock_klines(symbol, 500)
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 计算技术指标
        df = BacktestService._calculate_indicators(df)
        
        # 生成交易信号
        df = BacktestService._generate_signals(df)
        
        # 模拟交易
        trades, balance_history = BacktestService._simulate_trading(
            df,
            initial_balance,
            commission,
            slippage
        )
        
        # 计算回测结果
        results = BacktestService._calculate_results(
            df,
            trades,
            balance_history,
            initial_balance
        )
        
        return {
            "symbol": symbol,
            "initial_balance": initial_balance,
            "results": results,
            "trades": trades[:50],  # 只返回最近50笔交易
            "balance_history": balance_history,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    @staticmethod
    def _generate_mock_klines(symbol: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟K线数据"""
        
        np.random.seed(42)
        
        base_price = 0.5 if symbol.upper().startswith("RIVER") else 50000
        
        # 生成带趋势的价格序列
        prices = [base_price]
        for i in range(1, count):
            trend = 0.0001 if i < count * 0.6 else -0.0002
            noise = np.random.normal(0, 0.015)
            change = trend + noise
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # 生成K线数据
        klines = []
        now = datetime.now()
        
        for i in range(count):
            timestamp = int((now - timedelta(hours=count-i)).timestamp() * 1000)
            
            open_p = prices[i]
            close_p = prices[i]
            high_p = prices[i] * (1 + abs(np.random.normal(0, 0.008)))
            low_p = prices[i] * (1 - abs(np.random.normal(0, 0.008)))
            volume = np.random.uniform(10000, 100000)
            
            klines.append({
                "timestamp": timestamp,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": volume
            })
        
        return klines
    
    @staticmethod
    def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        
        # MA
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        return df
    
    @staticmethod
    def _generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        
        df['signal'] = 0
        
        # 做多信号
        # 1. MA5 上穿 MA20
        df.loc[(df['ma5'] > df['ma20']) & (df['ma5'].shift(1) <= df['ma20'].shift(1)), 'signal'] = 1
        
        # 2. RSI < 30 (超卖)
        df.loc[(df['rsi'] < 30) & (df['rsi'].shift(1) >= 30), 'signal'] = 1
        
        # 3. MACD 金叉
        df.loc[(df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'signal'] = 1
        
        # 做空信号
        # 1. MA5 下穿 MA20
        df.loc[(df['ma5'] < df['ma20']) & (df['ma5'].shift(1) >= df['ma20'].shift(1)), 'signal'] = -1
        
        # 2. RSI > 70 (超买)
        df.loc[(df['rsi'] > 70) & (df['rsi'].shift(1) <= 70), 'signal'] = -1
        
        # 3. MACD 死叉
        df.loc[(df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'signal'] = -1
        
        return df
    
    @staticmethod
    def _simulate_trading(
        df: pd.DataFrame,
        initial_balance: float,
        commission: float,
        slippage: float
    ) -> tuple:
        """模拟交易"""
        
        balance = initial_balance
        position = 0.0  # 持仓数量
        trades = []
        balance_history = []
        
        for idx, row in df.iterrows():
            # 记录余额历史
            balance_history.append({
                "timestamp": int(idx.timestamp() * 1000),
                "balance": balance + position * row['close'],
                "cash": balance,
                "position": position
            })
            
            # 交易信号
            signal = row['signal']
            
            if signal == 1 and position <= 0:
                # 做多
                if position < 0:
                    # 平空仓
                    close_price = row['close'] * (1 + slippage)
                    profit = -position * close_price
                    balance += profit
                    trades.append({
                        "timestamp": int(idx.timestamp() * 1000),
                        "type": "close_short",
                        "price": close_price,
                        "amount": -position,
                        "profit": profit
                    })
                    position = 0
                
                # 开多仓
                buy_price = row['close'] * (1 + slippage)
                fee = balance * commission
                amount = (balance - fee) / buy_price
                position = amount
                balance -= amount * buy_price + fee
                trades.append({
                    "timestamp": int(idx.timestamp() * 1000),
                    "type": "buy",
                    "price": buy_price,
                    "amount": amount,
                    "profit": 0
                })
            
            elif signal == -1 and position >= 0:
                # 做空
                if position > 0:
                    # 平多仓
                    close_price = row['close'] * (1 - slippage)
                    profit = position * close_price
                    balance += profit
                    trades.append({
                        "timestamp": int(idx.timestamp() * 1000),
                        "type": "close_long",
                        "price": close_price,
                        "amount": position,
                        "profit": profit - (position * close_price) * commission
                    })
                    position = 0
                
                # 开空仓（简化：用余额的一半做空）
                sell_price = row['close'] * (1 - slippage)
                fee = balance * 0.5 * commission
                amount = (balance * 0.5 - fee) / sell_price
                position = -amount
                balance += amount * sell_price - fee
                trades.append({
                    "timestamp": int(idx.timestamp() * 1000),
                    "type": "sell",
                    "price": sell_price,
                    "amount": amount,
                    "profit": 0
                })
        
        # 最后平仓
        if position != 0:
            last_price = df['close'].iloc[-1]
            if position > 0:
                close_price = last_price * (1 - slippage)
                profit = position * close_price
                balance += profit
                trades.append({
                    "timestamp": int(df.index[-1].timestamp() * 1000),
                    "type": "final_close_long",
                    "price": close_price,
                    "amount": position,
                    "profit": profit - (position * close_price) * commission
                })
            else:
                close_price = last_price * (1 + slippage)
                profit = -position * close_price
                balance += profit
                trades.append({
                    "timestamp": int(df.index[-1].timestamp() * 1000),
                    "type": "final_close_short",
                    "price": close_price,
                    "amount": -position,
                    "profit": profit
                })
        
        return trades, balance_history
    
    @staticmethod
    def _calculate_results(
        df: pd.DataFrame,
        trades: List[Dict[str, Any]],
        balance_history: List[Dict[str, Any]],
        initial_balance: float
    ) -> Dict[str, Any]:
        """计算回测结果"""
        
        final_balance = balance_history[-1]['balance']
        total_return = (final_balance - initial_balance) / initial_balance
        
        # 计算年化收益率
        days = (df.index[-1] - df.index[0]).days
        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
        else:
            annual_return = 0
        
        # 计算最大回撤
        balance_series = pd.Series([b['balance'] for b in balance_history])
        cummax = balance_series.cummax()
        drawdown = (cummax - balance_series) / cummax
        max_drawdown = drawdown.max()
        
        # 计算夏普比率
        returns = balance_series.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(365 * 24)  # 假设小时级
        else:
            sharpe_ratio = 0
        
        # 计算交易统计
        buy_trades = [t for t in trades if t['type'] in ['buy', 'close_short']]
        sell_trades = [t for t in trades if t['type'] in ['sell', 'close_long']]
        profitable_trades = [t for t in trades if t.get('profit', 0) > 0]
        
        win_rate = len(profitable_trades) / len(trades) if trades else 0
        
        # 总盈利/亏损
        total_profit = sum(t.get('profit', 0) for t in trades if t.get('profit', 0) > 0)
        total_loss = abs(sum(t.get('profit', 0) for t in trades if t.get('profit', 0) < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 确定回测等级
        if total_return > 0.5 and max_drawdown < 0.2 and sharpe_ratio > 1.5:
            grade = "S"
            label = "🏆 优秀"
        elif total_return > 0.3 and max_drawdown < 0.3 and sharpe_ratio > 1.0:
            grade = "A"
            label = "⭐ 良好"
        elif total_return > 0.1 and max_drawdown < 0.4:
            grade = "B"
            label = "👍 一般"
        elif total_return > 0:
            grade = "C"
            label = "⚠️ 较差"
        else:
            grade = "D"
            label = "🚨 亏损"
        
        return {
            "initial_balance": initial_balance,
            "final_balance": final_balance,
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe_ratio),
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "total_profit": float(total_profit),
            "total_loss": float(total_loss),
            "grade": grade,
            "label": label
        }
