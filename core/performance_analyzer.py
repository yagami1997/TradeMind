"""Performance analyzer for calculating backtest metrics."""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

class PerformanceAnalyzer:
    """
    性能分析器：计算回测性能指标
    
    功能：
    1. 计算收益率指标
    2. 计算风险指标
    3. 计算交易统计
    4. 生成绩效报告
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        初始化性能分析器
        
        Args:
            risk_free_rate: 无风险利率，默认2%
        """
        self.risk_free_rate = risk_free_rate
        self.daily_returns = []
        self.equity_values = []
        self.trades = []
        self.dates = []
        self.high_watermark = 0
        self.drawdowns = []
        
    def update(self, date: datetime, portfolio_value: float, trades: List[Dict]) -> None:
        """
        更新每日数据
        
        Args:
            date: 当前日期
            portfolio_value: 组合市值
            trades: 当日交易记录
        """
        self.dates.append(date)
        self.equity_values.append(portfolio_value)
        
        # 计算日收益率
        if len(self.equity_values) > 1:
            daily_return = (portfolio_value / self.equity_values[-2]) - 1
            self.daily_returns.append(daily_return)
        
        # 更新最高水位
        self.high_watermark = max(self.high_watermark, portfolio_value)
        
        # 计算回撤
        drawdown = (self.high_watermark - portfolio_value) / self.high_watermark
        self.drawdowns.append({
            'date': date,
            'value': portfolio_value,
            'drawdown': drawdown
        })
        
        # 记录交易
        self.trades.extend(trades)
        
    def calculate_metrics(self) -> Dict:
        """计算性能指标"""
        if not self.equity_values or len(self.equity_values) < 2:
            return {}
            
        # 基础指标
        total_return = (self.equity_values[-1] / self.equity_values[0]) - 1
        
        # 转换为numpy数组便于计算
        returns = np.array(self.daily_returns)
        
        # 年化指标
        trading_days = len(returns)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1
        
        # 风险指标
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = (annual_return - self.risk_free_rate) / volatility if volatility != 0 else 0
        
        # 回撤指标
        max_drawdown = max(dd['drawdown'] for dd in self.drawdowns)
        
        # 交易统计
        profitable_trades = [t for t in self.trades if t.get('profit', 0) > 0]
        loss_trades = [t for t in self.trades if t.get('profit', 0) <= 0]
        
        win_rate = len(profitable_trades) / len(self.trades) if self.trades else 0
        
        avg_profit = np.mean([t['profit'] for t in profitable_trades]) if profitable_trades else 0
        avg_loss = np.mean([t['profit'] for t in loss_trades]) if loss_trades else 0
        profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf')
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': len(self.trades),
            'profitable_trades': len(profitable_trades),
            'loss_trades': len(loss_trades),
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'risk_free_rate': self.risk_free_rate
        }
        
    def get_drawdowns(self) -> List[Dict]:
        """获取回撤历史"""
        return self.drawdowns
        
    def get_daily_returns(self) -> List[float]:
        """获取日收益率序列"""
        return self.daily_returns
        
    def get_monthly_returns(self) -> pd.Series:
        """计算月度收益率"""
        if not self.dates or not self.daily_returns:
            return pd.Series()
            
        # 创建日收益率序列
        daily_returns = pd.Series(
            self.daily_returns,
            index=self.dates[1:]  # 第一天没有收益率
        )
        
        # 计算月度收益率
        monthly_returns = daily_returns.resample('M').agg(
            lambda x: (1 + x).prod() - 1
        )
        
        return monthly_returns 