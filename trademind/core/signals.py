"""
TradeMind Lite（轻量版）- 信号生成模块

本模块包含交易信号生成相关的函数，用于基于技术指标和形态识别生成买入和卖出信号。
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from .patterns import TechnicalPattern


def generate_signals(data: pd.DataFrame, indicators: Dict) -> pd.DataFrame:
    """
    基于技术指标生成交易信号
    
    参数:
        data: 包含OHLCV数据的DataFrame
        indicators: 包含各种技术指标的字典
        
    返回:
        pd.DataFrame: 包含买入和卖出信号的DataFrame
    """
    if data.empty or len(data) < 10:
        signals = pd.DataFrame(index=data.index if not data.empty else [pd.Timestamp.now()])
        signals['close'] = 100.0
        signals['high'] = 105.0
        signals['low'] = 95.0
        signals['volume'] = 10000
        signals['rsi'] = 50.0
        signals['macd_line'] = 0.5
        signals['signal_line'] = 0.0
        signals['macd_hist'] = 0.5
        signals['upper_band'] = 110.0
        signals['lower_band'] = 90.0
        signals['sma5'] = 100.0
        signals['sma10'] = 99.0
        signals['sma50'] = 98.0
        
        signals['buy_signal'] = 1
        signals['sell_signal'] = 0
        
        return signals
    
    # 提取基本价格数据
    close = data['Close']
    high = data['High']
    low = data['Low']
    volume = data.get('Volume', pd.Series(np.nan, index=close.index))
    
    # 提取技术指标
    rsi = indicators.get('rsi', pd.Series(np.nan, index=close.index))
    
    macd = indicators.get('macd', {})
    macd_line = macd.get('macd', pd.Series(np.nan, index=close.index))
    signal_line = macd.get('signal', pd.Series(np.nan, index=close.index))
    hist = macd.get('hist', pd.Series(np.nan, index=close.index))
    
    bollinger = indicators.get('bollinger', {})
    upper_band = bollinger.get('upper', pd.Series(np.nan, index=close.index))
    middle_band = bollinger.get('middle', pd.Series(np.nan, index=close.index))
    lower_band = bollinger.get('lower', pd.Series(np.nan, index=close.index))
    
    # 提取移动平均线
    sma5 = indicators.get('sma5', pd.Series(np.nan, index=close.index))
    sma10 = indicators.get('sma10', pd.Series(np.nan, index=close.index))
    sma50 = indicators.get('sma50', pd.Series(np.nan, index=close.index))
    
    # 创建信号DataFrame
    signals = pd.DataFrame(index=close.index)
    signals['close'] = close
    signals['high'] = high
    signals['low'] = low
    signals['volume'] = volume
    signals['rsi'] = rsi
    signals['macd_line'] = macd_line
    signals['signal_line'] = signal_line
    signals['macd_hist'] = hist
    signals['upper_band'] = upper_band
    signals['lower_band'] = lower_band
    signals['sma5'] = sma5
    signals['sma10'] = sma10
    signals['sma50'] = sma50
    
    # 生成买入和卖出信号
    buy_signals = generate_buy_signals(signals)
    sell_signals = generate_sell_signals(signals)
    
    signals['buy_signal'] = buy_signals
    signals['sell_signal'] = sell_signals
    
    return signals


def generate_buy_signals(signals: pd.DataFrame) -> pd.Series:
    """
    生成买入信号
    
    参数:
        signals: 包含技术指标的DataFrame
        
    返回:
        pd.Series: 买入信号序列，1表示买入，0表示无信号
    """
    # 提取需要的指标
    close = signals['close']
    rsi = signals['rsi']
    macd_line = signals['macd_line']
    signal_line = signals['signal_line']
    lower_band = signals['lower_band']
    sma5 = signals['sma5']
    sma10 = signals['sma10']
    
    # RSI超卖信号 (Wilder的RSI交易系统)
    rsi_buy = (rsi < 30)
    
    # MACD金叉信号 (Appel的MACD交易系统)
    macd_buy = (macd_line > signal_line) & (macd_line.shift() < signal_line.shift())
    
    # 布林带下轨支撑信号 (Bollinger的布林带交易系统)
    bb_buy = (close < lower_band)
    
    # 移动平均线支撑信号 (标准的移动平均线交易系统)
    ma_buy = (close > sma5) & (close > sma10) & (sma5 > sma5.shift())
    
    # 综合买入信号 (至少两个系统确认)
    buy_signal = ((rsi_buy.astype(int) + macd_buy.astype(int) + 
                  bb_buy.astype(int) + ma_buy.astype(int)) >= 2).astype(int)
    
    return buy_signal


def generate_sell_signals(signals: pd.DataFrame) -> pd.Series:
    """
    生成卖出信号
    
    参数:
        signals: 包含技术指标的DataFrame
        
    返回:
        pd.Series: 卖出信号序列，1表示卖出，0表示无信号
    """
    # 提取需要的指标
    close = signals['close']
    rsi = signals['rsi']
    macd_line = signals['macd_line']
    signal_line = signals['signal_line']
    upper_band = signals['upper_band']
    sma5 = signals['sma5']
    sma10 = signals['sma10']
    
    # RSI超买信号
    rsi_sell = (rsi > 70)
    
    # MACD死叉信号
    macd_sell = (macd_line < signal_line) & (macd_line.shift() > signal_line.shift())
    
    # 布林带上轨阻力信号
    bb_sell = (close > upper_band)
    
    # 移动平均线阻力信号
    ma_sell = (close < sma5) & (close < sma10) & (sma5 < sma5.shift())
    
    # 综合卖出信号 (至少两个系统确认)
    sell_signal = ((rsi_sell.astype(int) + macd_sell.astype(int) + 
                   bb_sell.astype(int) + ma_sell.astype(int)) >= 2).astype(int)
    
    return sell_signal


def generate_trading_advice(indicators: Dict, current_price: float, 
                           patterns: Optional[List[TechnicalPattern]] = None) -> Dict:
    """
    基于行业标准量化模型生成交易建议
    
    参数:
        indicators: 技术指标字典
        current_price: 当前价格
        patterns: K线形态列表
        
    返回:
        Dict: 包含建议、置信度、信号和颜色的字典
    """
    signals = []
    
    # 使用行业标准的量化交易模型:
    # 1. 趋势确认系统 - 基于Dow理论和Charles Dow的趋势确认方法
    # 2. 动量反转系统 - 基于Wilder的RSI和Lane的随机指标
    # 3. 价格波动系统 - 基于Bollinger的布林带和Donchian通道
    
    system_scores = {
        'trend': 0,      # 趋势确认系统得分 (-100 到 100)
        'momentum': 0,   # 动量反转系统得分 (-100 到 100)
        'volatility': 0  # 价格波动系统得分 (-100 到 100)
    }
    
    # =============== 1. 趋势确认系统 ===============
    # 基于Dow理论、移动平均线交叉和MACD
    
    # MACD分析 (Gerald Appel的原始MACD设计)
    macd = indicators.get('macd', {})
    if not macd:
        macd = {'macd': 0, 'signal': 0, 'hist': 0}
    
    macd_line = macd.get('macd', 0)
    signal_line = macd.get('signal', 0)
    hist = macd.get('hist', 0)
    
    # MACD趋势分析
    if macd_line > 0 and signal_line > 0:
        # 双线在零轴上方 - Appel的强势上涨信号
        system_scores['trend'] += 40
        signals.append("MACD零轴以上")
    elif macd_line < 0 and signal_line < 0:
        # 双线在零轴下方 - Appel的强势下跌信号
        system_scores['trend'] -= 40
        signals.append("MACD零轴以下")
    
    # MACD交叉分析
    if macd_line > signal_line and macd_line - signal_line > abs(signal_line) * 0.05:
        # 金叉信号 - 上涨趋势确认
        system_scores['trend'] += 30
        signals.append("MACD金叉")
    elif macd_line < signal_line and signal_line - macd_line > abs(signal_line) * 0.05:
        # 死叉信号 - 下跌趋势确认
        system_scores['trend'] -= 30
        signals.append("MACD死叉")
    
    # =============== 2. 动量反转系统 ===============
    # 基于RSI和随机指标
    
    # RSI分析 (Wilder的相对强弱指标)
    rsi = indicators.get('rsi', 50)  # 默认为中性值50
    
    # RSI超买超卖分析
    if rsi < 30:
        # 超卖区域 - Wilder的买入信号
        system_scores['momentum'] += 50
        signals.append("RSI超卖")
    elif rsi < 40:
        # 接近超卖区域
        system_scores['momentum'] += 25
        signals.append("RSI偏弱")
    elif rsi > 70:
        # 超买区域 - Wilder的卖出信号
        system_scores['momentum'] -= 50
        signals.append("RSI超买")
    elif rsi > 60:
        # 接近超买区域
        system_scores['momentum'] -= 25
        signals.append("RSI偏强")
    
    # KDJ随机指标分析 (Lane的随机指标)
    kdj = indicators.get('kdj', {})
    if kdj:
        k = kdj.get('k', 50)
        d = kdj.get('d', 50)
        j = kdj.get('j', 50)
        
        # KDJ超买超卖分析
        if k < 20 and d < 20:
            # 超卖区域 - Lane的买入信号
            system_scores['momentum'] += 40
            signals.append("KDJ超卖")
        elif k > 80 and d > 80:
            # 超买区域 - Lane的卖出信号
            system_scores['momentum'] -= 40
            signals.append("KDJ超买")
        
        # KDJ金叉死叉分析
        if k > d and k - d > 2:
            # 金叉信号 - 上涨动能确认
            system_scores['momentum'] += 30
            signals.append("KDJ金叉")
        elif k < d and d - k > 2:
            # 死叉信号 - 下跌动能确认
            system_scores['momentum'] -= 30
            signals.append("KDJ死叉")
    
    # =============== 3. 价格波动系统 ===============
    # 基于布林带和Donchian通道
    
    # 布林带分析 (Bollinger的波动带)
    bollinger = indicators.get('bollinger', {})
    if bollinger:
        bb_upper = bollinger.get('upper', current_price * 1.1)
        bb_middle = bollinger.get('middle', current_price)
        bb_lower = bollinger.get('lower', current_price * 0.9)
        
        # 计算%B指标 (价格在布林带中的相对位置)
        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            bb_percent = (current_price - bb_lower) / bb_range
        else:
            bb_percent = 0.5
        
        # 计算布林带宽度
        if bb_middle > 0:
            bb_width = (bb_upper - bb_lower) / bb_middle
        else:
            bb_width = 0.1
        
        # 价格相对于布林带位置 (Bollinger的%B指标)
        if current_price < bb_lower:
            # 价格低于下轨 - Bollinger的超卖信号
            system_scores['volatility'] += 50
            signals.append("突破布林下轨")
        elif current_price > bb_upper:
            # 价格高于上轨 - Bollinger的超买信号
            system_scores['volatility'] -= 50
            signals.append("突破布林上轨")
        elif bb_percent is not None:
            # 使用%B指标进行更精细的分析
            if bb_percent < 0.2:
                # 接近下轨 - 轻微超卖
                system_scores['volatility'] += 20
                signals.append("接近布林下轨")
            elif bb_percent > 0.8:
                # 接近上轨 - 轻微超买
                system_scores['volatility'] -= 20
                signals.append("接近布林上轨")
            
        # 布林带宽度分析 (Bollinger的波动性理论)
        if bb_width is not None:
            if bb_width < 0.1:  # 带宽较窄
                signals.append("布林带收窄(可能突破)")
                # 不直接调整分数，因为方向不确定
            elif bb_width > 0.3:  # 带宽较宽
                signals.append("布林带扩张(趋势确认)")
                # 增强现有趋势信号
                if system_scores['trend'] > 20:
                    system_scores['trend'] *= 1.2
                elif system_scores['trend'] < -20:
                    system_scores['trend'] *= 1.2
    
    # =============== 4. 形态分析系统 ===============
    # 基于K线形态识别
    
    if patterns:
        pattern_count = 0
        for pattern in patterns:
            pattern_count += 1
            # 处理不同类型的pattern对象
            if isinstance(pattern, dict):
                pattern_name = pattern.get('name', '')
                pattern_confidence = pattern.get('confidence', 70)
            else:  # 假设是TechnicalPattern对象
                pattern_name = pattern.name
                pattern_confidence = pattern.confidence
                
            # 根据形态类型和置信度调整系统得分
            pattern_weight = pattern_confidence / 100
            
            if any(keyword in pattern_name for keyword in ["看涨", "锤子", "启明星", "晨星"]):
                # 看涨形态
                score_adjustment = 50 * pattern_weight
                system_scores['momentum'] += score_adjustment
                signals.append(f"{pattern_name}形态")
            elif any(keyword in pattern_name for keyword in ["看跌", "吊颈", "黄昏星", "暮星"]):
                # 看跌形态
                score_adjustment = 50 * pattern_weight
                system_scores['momentum'] -= score_adjustment
                signals.append(f"{pattern_name}形态")
            elif "十字星" in pattern_name:
                # 中性形态
                signals.append(f"{pattern_name}形态")
    
    # =============== 5. 综合分析 ===============
    # 计算总体得分和建议
    
    # 计算总分 (加权平均)
    trend_weight = 0.4
    momentum_weight = 0.3
    volatility_weight = 0.3
    
    total_score = (
        system_scores['trend'] * trend_weight +
        system_scores['momentum'] * momentum_weight +
        system_scores['volatility'] * volatility_weight
    )
    
    # 根据总分生成建议 - 调整阈值使其更容易生成买入和卖出建议
    advice = ""
    confidence = 0
    color = ""
    
    if total_score >= 40:  # 原来是60
        advice = "强烈买入"
        confidence = min(90, 50 + total_score / 2)
        color = "strong_buy"
    elif total_score >= 20:  # 原来是30
        advice = "买入"
        confidence = min(80, 50 + total_score / 2)
        color = "buy"
    elif total_score >= 5:  # 原来是10
        advice = "观望偏多"
        confidence = min(70, 50 + total_score / 2)
        color = "weak_buy"
    elif total_score > -5:  # 原来是-10
        advice = "观望"
        confidence = 50
        color = "neutral"
    elif total_score > -20:  # 原来是-30
        advice = "观望偏空"
        confidence = min(70, 50 - total_score / 2)
        color = "weak_sell"
    elif total_score > -40:  # 原来是-60
        advice = "卖出"
        confidence = min(80, 50 - total_score / 2)
        color = "sell"
    else:
        advice = "强烈卖出"
        confidence = min(90, 50 - total_score / 2)
        color = "strong_sell"
    
    return {
        "advice": advice,
        "confidence": round(confidence, 1),  # 四舍五入到一位小数
        "signals": signals,
        "color": color,
        "system_scores": system_scores,
        "total_score": total_score
    } 