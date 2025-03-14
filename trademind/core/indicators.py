"""
技术指标计算模块

本模块包含各种技术分析指标的计算函数，如MACD、RSI、KDJ和布林带等。
这些函数从原始的StockAnalyzer类中提取，保持相同的功能和接口。

注意: 所有函数都保持与原StockAnalyzer类中相同的参数和返回值，
以确保在重构过程中不破坏现有功能。
"""

import pandas as pd
import numpy as np


def calculate_macd(prices: pd.Series) -> tuple:
    """
    计算MACD指标
    
    参数:
        prices: 价格序列，通常使用收盘价
        
    返回:
        tuple: (MACD线, 信号线, 柱状图)
    """
    # 确保数据足够长
    if len(prices) < 26:
        return 0.0, 0.0, 0.0
        
    # 计算快速和慢速EMA
    ema12 = prices.ewm(span=12, adjust=False, min_periods=12).mean()
    ema26 = prices.ewm(span=26, adjust=False, min_periods=26).mean()
    
    # 计算MACD线 (DIF)
    macd_line = ema12 - ema26
    
    # 计算信号线 (DEA)
    signal_line = macd_line.ewm(span=9, adjust=False, min_periods=9).mean()
    
    # 计算柱状图 (MACD Histogram)
    histogram = macd_line - signal_line
    
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])


def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9) -> tuple:
    """
    计算KDJ指标
    
    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        n: 周期，默认9日
        
    返回:
        tuple: (K值, D值, J值)
    """
    # 计算RSV值 (Raw Stochastic Value)
    low_list = low.rolling(window=n).min()
    high_list = high.rolling(window=n).max()
    
    # 避免除以零错误
    rsv = pd.Series(0.0, index=close.index)
    valid_idx = high_list != low_list
    rsv[valid_idx] = (close[valid_idx] - low_list[valid_idx]) / (high_list[valid_idx] - low_list[valid_idx]) * 100
    
    # 初始化K、D值
    k = pd.Series(50.0, index=close.index)
    d = pd.Series(50.0, index=close.index)
    
    # 计算K、D、J值
    for i in range(n, len(close)):
        k.iloc[i] = 2/3 * k.iloc[i-1] + 1/3 * rsv.iloc[i]
        d.iloc[i] = 2/3 * d.iloc[i-1] + 1/3 * k.iloc[i]
    
    j = 3 * k - 2 * d
    
    # 处理极端值
    k = k.clip(0, 100)
    d = d.clip(0, 100)
    j = j.clip(0, 100)
    
    return float(k.iloc[-1]), float(d.iloc[-1]), float(j.iloc[-1])


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    计算相对强弱指数(RSI)
    
    参数:
        prices: 价格序列，通常使用收盘价
        period: 周期，默认14日
        
    返回:
        float: RSI值
    """
    # 确保数据足够长
    if len(prices) <= period:
        return 50.0  # 数据不足时返回中性值
        
    # 计算价格变化
    delta = prices.diff().dropna()
    
    # 分离上涨和下跌
    gain = delta.copy()
    loss = delta.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    loss = abs(loss)
    
    # 计算初始平均值
    avg_gain = gain.rolling(window=period).mean().iloc[period-1]
    avg_loss = loss.rolling(window=period).mean().iloc[period-1]
    
    # 使用Wilder平滑方法计算后续值
    for i in range(period, len(delta)):
        avg_gain = (avg_gain * (period - 1) + gain.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss.iloc[i]) / period
    
    # 避免除以零
    if avg_loss == 0:
        return 100.0
        
    # 计算相对强度和RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)


def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple:
    """
    计算布林带指标
    
    参数:
        prices: 价格序列，通常使用收盘价
        window: 移动平均窗口，默认20日
        num_std: 标准差倍数，默认2.0
        
    返回:
        tuple: (上轨, 中轨, 下轨, 带宽, 百分比B)
    """
    # 确保数据足够长
    if len(prices) < window:
        return 0.0, 0.0, 0.0, 0.0, 0.0
        
    # 计算中轨(简单移动平均线)
    middle = prices.rolling(window=window).mean()
    
    # 计算标准差
    std = prices.rolling(window=window).std()
    
    # 计算上下轨
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    # 计算带宽 (Bandwidth)
    bandwidth = (upper - lower) / middle
    
    # 计算百分比B (%B)
    percent_b = (prices - lower) / (upper - lower)
    
    # 获取最新值
    latest_upper = float(upper.iloc[-1])
    latest_middle = float(middle.iloc[-1])
    latest_lower = float(lower.iloc[-1])
    latest_bandwidth = float(bandwidth.iloc[-1])
    latest_percent_b = float(percent_b.iloc[-1])
    
    return latest_upper, latest_middle, latest_lower, latest_bandwidth, latest_percent_b 