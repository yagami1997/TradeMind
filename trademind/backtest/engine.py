"""
TradeMind Lite（轻量版）- 回测系统模块

本模块包含交易策略回测相关的函数，用于评估交易策略的性能。
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import random
import logging

# 设置日志
logger = logging.getLogger(__name__)

def run_backtest(data: pd.DataFrame, signals: pd.DataFrame, 
                 initial_capital: float = 10000.0,
                 risk_per_trade_pct: float = 0.02,
                 stop_loss_pct: float = 0.07,
                 take_profit_pct: float = 0.15,
                 max_hold_days: int = 20) -> Dict:
    """
    执行回测，评估交易策略性能
    
    参数:
        data: 包含OHLCV数据的DataFrame
        signals: 包含买入和卖出信号的DataFrame
        initial_capital: 初始资金
        risk_per_trade_pct: 每笔交易风险资金的百分比
        stop_loss_pct: 止损百分比
        take_profit_pct: 止盈百分比
        max_hold_days: 最大持有天数
        
    返回:
        Dict: 回测结果统计
    """
    try:
        # 检查数据有效性
        if data is None or signals is None or len(data) < 50:
            logger.warning("回测数据不足或无效")
            return get_empty_results()
        
        # 确保数据和信号的索引匹配
        if not data.index.equals(signals.index):
            logger.warning("数据和信号的时间索引不匹配")
            try:
                # 尝试重新索引信号数据
                signals = signals.reindex(data.index)
            except Exception as e:
                logger.error(f"重新索引信号数据失败: {str(e)}")
                return get_empty_results()
        
        # 执行交易模拟
        try:
            trades, equity = simulate_trades(
                data, signals, 
                initial_capital=initial_capital,
                risk_per_trade_pct=risk_per_trade_pct,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                max_hold_days=max_hold_days
            )
            
            # 计算性能指标
            results = calculate_performance_metrics(trades, equity, initial_capital, data.index)
            return results
            
        except Exception as e:
            logger.error(f"执行交易模拟时出错: {str(e)}")
            return get_empty_results()
            
    except Exception as e:
        logger.error(f"回测过程中发生错误: {str(e)}")
        return get_empty_results()


def get_empty_results() -> Dict:
    """返回空的回测结果"""
    return {
        'total_trades': 0,
        'win_rate': 0,
        'avg_profit': 0,
        'max_profit': 0,
        'max_loss': 0,
        'profit_factor': 0,
        'max_drawdown': 0,
        'consecutive_losses': 0,
        'avg_hold_days': 0,
        'final_return': 0,
        'sharpe_ratio': 0,
        'sortino_ratio': 0,
        'net_profit': 0,
        'annualized_return': 0,
        'confidence_level': 0
    }


def simulate_trades(data: pd.DataFrame, signals: pd.DataFrame,
                   initial_capital: float = 10000.0,
                   risk_per_trade_pct: float = 0.02,
                   stop_loss_pct: float = 0.07,
                   take_profit_pct: float = 0.15,
                   max_hold_days: int = 20) -> Tuple[List[Dict], List[float]]:
    """
    模拟交易执行，生成交易记录和权益曲线
    
    参数:
        data: 包含OHLCV数据的DataFrame
        signals: 包含买入和卖出信号的DataFrame
        initial_capital: 初始资金
        risk_per_trade_pct: 每笔交易风险资金的百分比
        stop_loss_pct: 止损百分比
        take_profit_pct: 止盈百分比
        max_hold_days: 最大持有天数
        
    返回:
        Tuple[List[Dict], List[float]]: 交易记录和权益曲线
    """
    # 准备数据
    close = data['Close'].copy()
    high = data['High'].copy()
    low = data['Low'].copy()
    dates = data.index
    
    # 交易成本模型 (基于IBKR的固定费率模型)
    commission_per_share = 0.005  # 每股0.005美元 (IBKR固定费率)
    min_commission = 1.0  # 最低每单1美元
    max_commission_pct = 0.01  # 最高为总成交金额的1%
    
    # 滑点模型
    base_slippage_pct = 0.0005  # 基础滑点
    market_impact_factor = 0.1  # 市场冲击系数
    
    # 初始化回测变量
    position = 0  # 0表示空仓，1表示多头，-1表示空头
    entry_price = 0.0  # 入场价格
    entry_date = None  # 入场日期
    capital = initial_capital  # 当前资金
    equity = [initial_capital]  # 权益曲线
    trades = []  # 交易记录
    
    # 计算ATR (真实波动幅度)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    # 使用Wilder的平滑方法
    for i in range(14, len(tr)):
        atr.iloc[i] = (atr.iloc[i-1] * 13 + tr.iloc[i]) / 14
    
    # 计算平均成交量
    volume = data.get('Volume', pd.Series(np.ones(len(close)), index=close.index))
    
    # 确保信号数据包含必要的列
    if 'buy_signal' not in signals.columns:
        signals['buy_signal'] = False
    if 'sell_signal' not in signals.columns:
        signals['sell_signal'] = False
    
    # 增强信号 - 添加额外的技术指标信号
    enhanced_buy_signals = signals['buy_signal'].copy()
    enhanced_sell_signals = signals['sell_signal'].copy()
    
    # 如果有RSI数据，添加RSI超买超卖信号
    if 'rsi' in signals.columns:
        rsi = signals['rsi']
        # RSI < 30 为买入信号
        enhanced_buy_signals = enhanced_buy_signals | (rsi < 30)
        # RSI > 70 为卖出信号
        enhanced_sell_signals = enhanced_sell_signals | (rsi > 70)
    
    # 如果有MACD数据，添加MACD金叉死叉信号
    if all(col in signals.columns for col in ['macd_line', 'signal_line']):
        macd_line = signals['macd_line']
        signal_line = signals['signal_line']
        # MACD金叉为买入信号
        macd_cross_up = (macd_line > signal_line) & (macd_line.shift() < signal_line.shift())
        enhanced_buy_signals = enhanced_buy_signals | macd_cross_up
        # MACD死叉为卖出信号
        macd_cross_down = (macd_line < signal_line) & (macd_line.shift() > signal_line.shift())
        enhanced_sell_signals = enhanced_sell_signals | macd_cross_down
    
    # 如果有布林带数据，添加布林带突破信号
    if all(col in signals.columns for col in ['upper_band', 'lower_band']):
        upper_band = signals['upper_band']
        lower_band = signals['lower_band']
        # 价格突破下轨为买入信号
        bb_lower_break = (close < lower_band)
        enhanced_buy_signals = enhanced_buy_signals | bb_lower_break
        # 价格突破上轨为卖出信号
        bb_upper_break = (close > upper_band)
        enhanced_sell_signals = enhanced_sell_signals | bb_upper_break
    
    # 遍历每个交易日
    for i in range(50, len(signals)):
        current_date = dates[i]
        current_price = close.iloc[i]
        current_high = high.iloc[i]
        current_low = low.iloc[i]
        current_volume = volume.iloc[i]
        avg_volume = volume.iloc[i-20:i].mean() if 'Volume' in data.columns else 1000  # 20日平均成交量
        
        # 计算当前ATR
        current_atr = atr.iloc[i]
        
        # 如果有持仓，检查止损止盈
        if position != 0:
            days_held = (current_date - entry_date).days
            
            # 计算浮动盈亏
            if position == 1:  # 多头
                profit_pct = (current_price - entry_price) / entry_price
            else:  # 空头
                profit_pct = (entry_price - current_price) / entry_price
            
            # 检查止损条件
            stop_triggered = False
            if position == 1 and current_low <= entry_price * (1 - stop_loss_pct):
                # 多头止损 - 使用当日最低价检查
                stop_price = entry_price * (1 - stop_loss_pct)
                stop_triggered = True
            elif position == -1 and current_high >= entry_price * (1 + stop_loss_pct):
                # 空头止损 - 使用当日最高价检查
                stop_price = entry_price * (1 + stop_loss_pct)
                stop_triggered = True
            
            # 检查止盈条件
            take_profit_triggered = False
            if position == 1 and current_high >= entry_price * (1 + take_profit_pct):
                # 多头止盈 - 使用当日最高价检查
                take_profit_price = entry_price * (1 + take_profit_pct)
                take_profit_triggered = True
            elif position == -1 and current_low <= entry_price * (1 - take_profit_pct):
                # 空头止盈 - 使用当日最低价检查
                take_profit_price = entry_price * (1 - take_profit_pct)
                take_profit_triggered = True
            
            # 检查最大持有天数
            max_hold_triggered = days_held >= max_hold_days
            
            # 检查反向信号
            reverse_signal = (position == 1 and enhanced_sell_signals.iloc[i]) or (position == -1 and enhanced_buy_signals.iloc[i])
            
            # 如果触发任何平仓条件，执行平仓
            if stop_triggered or take_profit_triggered or max_hold_triggered or reverse_signal:
                # 确定平仓价格
                if stop_triggered:
                    exit_price = stop_price
                    exit_reason = "止损"
                elif take_profit_triggered:
                    exit_price = take_profit_price
                    exit_reason = "止盈"
                elif max_hold_triggered:
                    exit_price = current_price
                    exit_reason = "最大持有期限"
                else:  # reverse_signal
                    exit_price = current_price
                    exit_reason = "反向信号"
                
                # 计算滑点
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                slippage_pct = base_slippage_pct + (market_impact_factor * volume_ratio / 100)
                
                # 应用滑点
                if position == 1:  # 多头平仓，卖出
                    exit_price *= (1 - slippage_pct)
                else:  # 空头平仓，买入
                    exit_price *= (1 + slippage_pct)
                
                # 计算交易数量
                position_value = capital * risk_per_trade_pct / stop_loss_pct
                shares = position_value / entry_price
                
                # 计算交易成本
                commission = max(min_commission, min(shares * commission_per_share, position_value * max_commission_pct))
                
                # 计算交易盈亏
                if position == 1:  # 多头
                    profit = shares * (exit_price - entry_price) - commission
                else:  # 空头
                    profit = shares * (entry_price - exit_price) - commission
                
                # 更新资金
                capital += profit
                
                # 记录交易
                trades.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'exit_date': current_date,
                    'exit_price': exit_price,
                    'position': 'long' if position == 1 else 'short',
                    'shares': shares,
                    'profit': profit,
                    'profit_pct': profit / (shares * entry_price) * 100,
                    'exit_reason': exit_reason,
                    'hold_days': days_held
                })
                
                # 平仓后重置持仓状态
                position = 0
    
        # 如果没有持仓，检查开仓信号
        if position == 0:
            # 检查买入信号
            if enhanced_buy_signals.iloc[i]:
                position = 1  # 多头
                entry_price = current_price * (1 + base_slippage_pct)  # 考虑滑点
                entry_date = current_date
            
            # 检查卖出信号 (做空)
            elif enhanced_sell_signals.iloc[i]:
                position = -1  # 空头
                entry_price = current_price * (1 - base_slippage_pct)  # 考虑滑点
                entry_date = current_date
        
        # 更新权益曲线
        equity.append(capital)
    
    return trades, equity


def calculate_performance_metrics(trades: List[Dict], equity: List[float], 
                                 initial_capital: float, dates: pd.DatetimeIndex) -> Dict:
    """
    计算回测性能指标
    
    参数:
        trades: 交易记录列表
        equity: 权益曲线
        initial_capital: 初始资金
        dates: 日期索引
        
    返回:
        Dict: 性能指标字典
    """
    # 如果没有交易，返回空结果
    if not trades:
        return get_empty_results()
    
    # 计算交易统计
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['profit'] > 0]
    losing_trades = [t for t in trades if t['profit'] <= 0]
    
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
    
    avg_profit = sum(t['profit'] for t in trades) / total_trades if total_trades > 0 else 0
    max_profit = max([t['profit'] for t in trades]) if trades else 0
    max_loss = min([t['profit'] for t in trades]) if trades else 0
    
    # 计算盈亏比 (Profit Factor)
    gross_profit = sum(t['profit'] for t in winning_trades) if winning_trades else 0
    gross_loss = abs(sum(t['profit'] for t in losing_trades)) if losing_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # 计算最大连续亏损次数
    consecutive_losses = 0
    max_consecutive_losses = 0
    for t in trades:
        if t['profit'] <= 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0
    
    # 计算平均持仓天数
    avg_hold_days = sum(t['hold_days'] for t in trades) / total_trades if total_trades > 0 else 0
    
    # 计算最终收益率
    capital = equity[-1]
    final_return = (capital - initial_capital) / initial_capital * 100
    
    # 计算净利润
    net_profit = capital - initial_capital
    
    # 计算权益曲线的日收益率
    equity_series = pd.Series(equity)
    daily_returns = equity_series.pct_change().dropna()
    
    # 计算最大回撤 (Maximum Drawdown)
    peak = equity_series.expanding().max()
    drawdown = (equity_series / peak - 1) * 100
    max_drawdown = abs(drawdown.min())
    
    # 计算Sharpe比率
    risk_free_rate = 0.02 / 252  # 假设年化无风险利率为2%，转换为日利率
    excess_returns = daily_returns - risk_free_rate
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if len(excess_returns) > 0 and excess_returns.std() > 0 else 0
    
    # 计算Sortino比率 (只考虑下行风险)
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
    
    # 避免除以零的情况
    if downside_std > 0 and len(excess_returns) > 0:
        sortino_ratio = (excess_returns.mean() / downside_std) * np.sqrt(252)
    else:
        # 如果没有下行风险或者收益率为空，返回0或者一个高值
        sortino_ratio = 0 if len(excess_returns) == 0 or excess_returns.mean() <= 0 else 10
    
    # 计算年化收益率
    days = (dates[-1] - dates[0]).days if len(dates) > 1 else 1
    years = max(days / 365, 0.01)  # 避免除以零
    annualized_return = ((1 + final_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    # 计算策略置信水平
    # 基于多个指标的加权平均值
    confidence_factors = {
        'win_rate': win_rate * 100 * 0.25,  # 胜率权重25%
        'profit_factor': min(profit_factor * 10, 25) if profit_factor > 0 else 0,  # 盈亏比权重25%
        'sharpe': min(sharpe_ratio * 10, 25) if sharpe_ratio > 0 else 0,  # Sharpe比率权重25%
        'drawdown': max(0, 25 - (max_drawdown / 2)) if max_drawdown < 50 else 0  # 回撤权重25%
    }
    
    # 计算总置信度
    confidence_level = sum(confidence_factors.values())
    
    # 根据交易次数调整置信度
    if total_trades < 10:
        confidence_level *= (total_trades / 10)
    
    # 返回回测结果
    return {
        'total_trades': total_trades,
        'win_rate': round(win_rate * 100, 1),
        'avg_profit': round(avg_profit, 2),
        'max_profit': round(max_profit, 2),
        'max_loss': round(max_loss, 2),
        'profit_factor': round(profit_factor, 2),
        'max_drawdown': round(max_drawdown, 1),
        'consecutive_losses': max_consecutive_losses,
        'avg_hold_days': round(avg_hold_days, 1),
        'final_return': round(final_return, 1),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'sortino_ratio': round(sortino_ratio, 2),
        'net_profit': round(net_profit, 2),
        'annualized_return': round(annualized_return, 1),
        'confidence_level': round(confidence_level, 1)
    }


def generate_trade_summary(trades: List[Dict]) -> Dict:
    """
    生成交易摘要，包括按月、按交易类型的统计
    
    参数:
        trades: 交易记录列表
        
    返回:
        Dict: 交易摘要统计
    """
    if not trades:
        return {
            'monthly_performance': {},
            'exit_reason_stats': {},
            'position_stats': {}
        }
    
    # 按月统计
    monthly_performance = {}
    for trade in trades:
        month_key = trade['exit_date'].strftime('%Y-%m')
        if month_key not in monthly_performance:
            monthly_performance[month_key] = {
                'trades': 0,
                'profit': 0,
                'win_rate': 0,
                'winning_trades': 0
            }
        
        monthly_performance[month_key]['trades'] += 1
        monthly_performance[month_key]['profit'] += trade['profit']
        if trade['profit'] > 0:
            monthly_performance[month_key]['winning_trades'] += 1
    
    # 计算每月胜率
    for month, stats in monthly_performance.items():
        if stats['trades'] > 0:
            stats['win_rate'] = round(stats['winning_trades'] / stats['trades'] * 100, 1)
            stats['profit'] = round(stats['profit'], 2)
    
    # 按平仓原因统计
    exit_reason_stats = {}
    for trade in trades:
        reason = trade['exit_reason']
        if reason not in exit_reason_stats:
            exit_reason_stats[reason] = {
                'count': 0,
                'profit': 0,
                'avg_profit': 0,
                'win_rate': 0,
                'winning_trades': 0
            }
        
        exit_reason_stats[reason]['count'] += 1
        exit_reason_stats[reason]['profit'] += trade['profit']
        if trade['profit'] > 0:
            exit_reason_stats[reason]['winning_trades'] += 1
    
    # 计算每种平仓原因的胜率和平均利润
    for reason, stats in exit_reason_stats.items():
        if stats['count'] > 0:
            stats['win_rate'] = round(stats['winning_trades'] / stats['count'] * 100, 1)
            stats['avg_profit'] = round(stats['profit'] / stats['count'], 2)
            stats['profit'] = round(stats['profit'], 2)
    
    # 按持仓方向统计
    position_stats = {
        'long': {'count': 0, 'profit': 0, 'win_rate': 0, 'winning_trades': 0},
        'short': {'count': 0, 'profit': 0, 'win_rate': 0, 'winning_trades': 0}
    }
    
    for trade in trades:
        position = trade['position']
        position_stats[position]['count'] += 1
        position_stats[position]['profit'] += trade['profit']
        if trade['profit'] > 0:
            position_stats[position]['winning_trades'] += 1
    
    # 计算每个持仓方向的胜率和平均利润
    for position, stats in position_stats.items():
        if stats['count'] > 0:
            stats['win_rate'] = round(stats['winning_trades'] / stats['count'] * 100, 1)
            stats['avg_profit'] = round(stats['profit'] / stats['count'], 2)
            stats['profit'] = round(stats['profit'], 2)
    
    return {
        'monthly_performance': monthly_performance,
        'exit_reason_stats': exit_reason_stats,
        'position_stats': position_stats
    } 