"""
TradeMind Lite（轻量版）- 数据加载器

本模块包含股票数据加载相关的功能。
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

# 设置日志
logger = logging.getLogger("trademind.data")

def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    获取股票历史数据
    
    参数:
        symbol: 股票代码
        period: 数据周期，如1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: 数据间隔，如1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        
    返回:
        pd.DataFrame: 股票历史数据
    """
    try:
        # 获取更长时间的历史数据，确保有足够的数据进行回测
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty or len(hist) < 100:  # 确保至少有100个交易日的数据
            print(f"⚠️ {symbol} 的历史数据不足，尝试获取最大可用数据")
            # 尝试获取最大可用数据
            hist = stock.history(period="max")
        
        return hist
    except Exception as e:
        logger.error(f"获取 {symbol} 的历史数据时出错: {str(e)}")
        print(f"❌ 获取 {symbol} 的历史数据失败: {str(e)}")
        return pd.DataFrame()

def get_stock_info(symbol: str) -> Dict:
    """
    获取股票信息
    
    参数:
        symbol: 股票代码
        
    返回:
        Dict: 股票信息
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return info
    except Exception as e:
        logger.error(f"获取 {symbol} 的信息时出错: {str(e)}")
        return {'shortName': symbol} 