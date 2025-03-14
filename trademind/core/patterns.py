"""
TradeMind Lite（轻量版）- 形态识别模块

本模块包含K线形态识别相关的类和函数，用于识别各种技术形态。
"""

from dataclasses import dataclass
from typing import List
import pandas as pd


@dataclass
class TechnicalPattern:
    """
    技术形态数据类，用于存储识别出的K线形态信息。
    
    属性:
        name: 形态名称
        confidence: 置信度（0-100）
        description: 形态描述
    """
    name: str
    confidence: float
    description: str


def identify_candlestick_patterns(data: pd.DataFrame) -> List[TechnicalPattern]:
    """
    识别K线图中的蜡烛图形态。
    
    参数:
        data: 包含OHLC数据的DataFrame，至少需要5根K线
        
    返回:
        List[TechnicalPattern]: 识别出的形态列表
    """
    patterns = []
    
    if len(data) < 5:  # 增加到5根K线以获取更多上下文
        return patterns
    
    # 获取最近的K线数据
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    prev2 = data.iloc[-3]
    prev3 = data.iloc[-4]
    prev4 = data.iloc[-5]
    
    open_price = latest['Open']
    close = latest['Close']
    high = latest['High']
    low = latest['Low']
    
    body = abs(open_price - close)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low
    total_length = high - low
    
    # 计算前几天的平均波动范围作为参考
    avg_range = (data['High'] - data['Low']).iloc[-5:].mean()
    
    # 十字星形态 - 改进判断标准
    if body <= total_length * 0.15 and total_length >= avg_range * 0.8:
        # 增加位置判断，提高准确性
        if prev['Close'] > prev['Open'] and close < open_price:  # 可能是看跌十字星
            patterns.append(TechnicalPattern(
                name="看跌十字星",
                confidence=80,
                description="开盘价和收盘价接近，位于上升趋势之后，可能预示着反转"
            ))
        elif prev['Close'] < prev['Open'] and close > open_price:  # 可能是看涨十字星
            patterns.append(TechnicalPattern(
                name="看涨十字星",
                confidence=80,
                description="开盘价和收盘价接近，位于下降趋势之后，可能预示着反转"
            ))
        else:
            patterns.append(TechnicalPattern(
                name="十字星",
                confidence=70,
                description="开盘价和收盘价接近，表示市场犹豫不决"
            ))
    
    # 锤子线 - 改进判断标准
    if (lower_shadow > body * 2) and (upper_shadow < body * 0.3) and (body > 0):
        # 增加趋势确认
        if data['Close'].iloc[-5:].mean() > data['Close'].iloc[-10:-5].mean():
            confidence = 60  # 在上升趋势中出现锤子线，降低置信度
        else:
            confidence = 85  # 在下降趋势中出现锤子线，提高置信度
            
        patterns.append(TechnicalPattern(
            name="锤子线",
            confidence=confidence,
            description="下影线较长，可能预示着底部反转"
        ))
    
    # 吊颈线 - 改进判断标准
    if (upper_shadow > body * 2) and (lower_shadow < body * 0.3) and (body > 0):
        # 增加趋势确认
        if data['Close'].iloc[-5:].mean() < data['Close'].iloc[-10:-5].mean():
            confidence = 60  # 在下降趋势中出现吊颈线，降低置信度
        else:
            confidence = 85  # 在上升趋势中出现吊颈线，提高置信度
            
        patterns.append(TechnicalPattern(
            name="吊颈线",
            confidence=confidence,
            description="上影线较长，可能预示着顶部反转"
        ))
    
    # 增加启明星形态识别
    if (len(data) >= 5 and 
        prev2['Close'] < prev2['Open'] and  # 第一天是阴线
        abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.5 and  # 第二天是小实体
        close > open_price and  # 第三天是阳线
        close > (prev2['Open'] + prev2['Close']) / 2):  # 第三天收盘价高于第一天实体中点
        
        patterns.append(TechnicalPattern(
            name="启明星",
            confidence=85,
            description="三日反转形态，预示着可能的底部反转"
        ))
    
    # 增加黄昏星形态识别
    if (len(data) >= 5 and 
        prev2['Close'] > prev2['Open'] and  # 第一天是阳线
        abs(prev['Close'] - prev['Open']) < abs(prev2['Close'] - prev2['Open']) * 0.5 and  # 第二天是小实体
        close < open_price and  # 第三天是阴线
        close < (prev2['Open'] + prev2['Close']) / 2):  # 第三天收盘价低于第一天实体中点
        
        patterns.append(TechnicalPattern(
            name="黄昏星",
            confidence=85,
            description="三日反转形态，预示着可能的顶部反转"
        ))
    
    # 增加吞没形态识别
    if (prev['Close'] < prev['Open'] and  # 前一天是阴线
        close > open_price and  # 当天是阳线
        open_price < prev['Close'] and  # 当天开盘价低于前一天收盘价
        close > prev['Open']):  # 当天收盘价高于前一天开盘价
        
        patterns.append(TechnicalPattern(
            name="看涨吞没",
            confidence=80,
            description="两日反转形态，当天阳线吞没前一天阴线，预示着可能的底部反转"
        ))
    
    if (prev['Close'] > prev['Open'] and  # 前一天是阳线
        close < open_price and  # 当天是阴线
        open_price > prev['Close'] and  # 当天开盘价高于前一天收盘价
        close < prev['Open']):  # 当天收盘价低于前一天开盘价
        
        patterns.append(TechnicalPattern(
            name="看跌吞没",
            confidence=80,
            description="两日反转形态，当天阴线吞没前一天阳线，预示着可能的顶部反转"
        ))
    
    return patterns 