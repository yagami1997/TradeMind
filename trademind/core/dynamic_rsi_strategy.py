"""
动态RSI策略模块

本模块提供基于ATR的动态RSI算法，使用相对历史波动率来调整RSI阈值，
以及基于该算法的交易信号生成和回测功能。
"""

import pandas as pd
import numpy as np
from trademind.core.indicators import calculate_rsi

def dynamic_atr_rsi(price_data, rsi_period=14, atr_period=14, lookback_period=252):
    """
    基于ATR的动态RSI算法，使用相对历史波动率来调整RSI阈值
    
    参数:
    price_data (DataFrame): 包含 'High', 'Low', 'Close' 列的价格数据
    rsi_period (int): RSI计算周期
    atr_period (int): ATR计算周期
    lookback_period (int): 用于计算波动率百分位的历史回溯期
    
    返回:
    DataFrame: 包含RSI值和动态阈值的数据框
    """
    # 计算RSI (使用indicators模块中的函数)
    delta = price_data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # 计算ATR
    high = price_data['High']
    low = price_data['Low']
    close = price_data['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=atr_period).mean()
    
    # 计算ATR占价格的百分比
    atr_pct = (atr / close) * 100
    
    # 计算波动率的历史百分位
    volatility_percentile = atr_pct.rolling(window=lookback_period).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1]
    )
    
    # 平滑地调整RSI阈值
    base_oversold = 30
    base_overbought = 70
    max_adjustment = 15  # 最大调整幅度
    
    # 根据波动率百分位平滑调整阈值
    oversold = base_oversold - (volatility_percentile * max_adjustment)
    overbought = base_overbought + (volatility_percentile * max_adjustment)
    
    # 创建结果DataFrame
    result = pd.DataFrame({
        'close': price_data['Close'],
        'rsi': rsi,
        'atr_pct': atr_pct,
        'volatility_percentile': volatility_percentile,
        'oversold_threshold': oversold,
        'overbought_threshold': overbought
    })
    
    return result

def generate_signals(result_df):
    """
    基于动态RSI阈值生成交易信号
    
    参数:
    result_df (DataFrame): dynamic_atr_rsi函数的输出结果
    
    返回:
    DataFrame: 添加了交易信号的数据框
    """
    signals = result_df.copy()
    
    # 初始化信号列
    signals['signal'] = 0
    
    # 生成买入信号 (RSI低于动态超卖阈值)
    signals.loc[signals['rsi'] < signals['oversold_threshold'], 'signal'] = 1
    
    # 生成卖出信号 (RSI高于动态超买阈值)
    signals.loc[signals['rsi'] > signals['overbought_threshold'], 'signal'] = -1
    
    return signals

def backtest_dynamic_rsi(price_data, initial_capital=10000):
    """
    回测动态RSI策略
    
    参数:
    price_data (DataFrame): 价格数据
    initial_capital (float): 初始资金
    
    返回:
    DataFrame: 回测结果
    """
    # 计算动态RSI和信号
    results = dynamic_atr_rsi(price_data)
    signals = generate_signals(results)
    
    # 创建回测结果DataFrame
    backtest = signals.copy()
    backtest['position'] = signals['signal'].shift(1).fillna(0).cumsum()
    backtest['returns'] = price_data['Close'].pct_change()
    backtest['strategy_returns'] = backtest['position'] * backtest['returns']
    
    # 计算累积收益
    backtest['cumulative_returns'] = (1 + backtest['returns']).cumprod()
    backtest['strategy_cumulative_returns'] = (1 + backtest['strategy_returns']).cumprod()
    
    # 计算资金曲线
    backtest['capital'] = initial_capital * backtest['strategy_cumulative_returns']
    
    return backtest 