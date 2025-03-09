from dataclasses import dataclass
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import json
import warnings
import webbrowser
import os
import sys
from tqdm import tqdm
import time

warnings.filterwarnings('ignore', category=Warning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

@dataclass
class TechnicalPattern:
    name: str
    confidence: float
    description: str

class StockAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.setup_paths()
        self.setup_colors()

    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/stock_analyzer.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("stock_analyzer")

    def setup_paths(self):
        self.results_path = Path("reports/stocks")
        self.results_path.mkdir(parents=True, exist_ok=True)

    def setup_colors(self):
        self.colors = {
            "primary": "#1976D2",
            "secondary": "#0D47A1",
            "success": "#2E7D32",
            "warning": "#F57F17",
            "danger": "#C62828",
            "info": "#0288D1",
            "background": "#FFFFFF",
            "text": "#212121",
            "card": "#FFFFFF",
            "border": "#E0E0E0",
            "gradient_start": "#1976D2",
            "gradient_end": "#0D47A1",
            "strong_buy": "#00796B",
            "buy": "#26A69A",
            "strong_sell": "#D32F2F",
            "sell": "#EF5350",
            "neutral": "#FFA000"
        }

    def identify_candlestick_patterns(self, data: pd.DataFrame) -> List[TechnicalPattern]:
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

    def calculate_macd(self, prices: pd.Series) -> tuple:
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

    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9) -> tuple:
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

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
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

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple:
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

    def generate_trading_advice(self, indicators: Dict, current_price: float, patterns: List[TechnicalPattern] = None) -> Dict:
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
        macd = indicators['macd']
        macd_line = macd['macd']
        signal_line = macd['signal']
        hist = macd['hist']
        
        # MACD趋势分析
        if macd_line > 0 and signal_line > 0:
            # 双线在零轴上方 - Appel的强势上涨信号
            system_scores['trend'] += 40
            signals.append("MACD零轴以上")
        elif macd_line < 0 and signal_line < 0:
            # 双线在零轴下方 - Appel的强势下跌信号
            system_scores['trend'] -= 40
            signals.append("MACD零轴以下")
            
        # MACD交叉信号
        if hist > 0 and hist > hist * 1.05:  # 柱状图为正且增长
            # 金叉信号增强中
            system_scores['trend'] += 30
            signals.append("MACD金叉增强")
        elif hist > 0:
            # 普通金叉
            system_scores['trend'] += 20
            signals.append("MACD金叉")
        elif hist < 0 and hist < hist * 1.05:  # 柱状图为负且继续走低
            # 死叉信号增强中
            system_scores['trend'] -= 30
            signals.append("MACD死叉增强")
        elif hist < 0:
            # 普通死叉
            system_scores['trend'] -= 20
            signals.append("MACD死叉")
            
        # 移动平均线分析 (基于Dow理论的趋势确认)
        if 'sma' in indicators:
            sma = indicators['sma']
            sma_short = sma.get('short', 0)  # 短期均线 (如5日或10日)
            sma_medium = sma.get('medium', 0)  # 中期均线 (如20日或50日)
            sma_long = sma.get('long', 0)  # 长期均线 (如100日或200日)
            
            # 多头排列 (短期>中期>长期)
            if sma_short > sma_medium > sma_long:
                system_scores['trend'] += 30
                signals.append("均线多头排列")
            # 空头排列 (短期<中期<长期)
            elif sma_short < sma_medium < sma_long:
                system_scores['trend'] -= 30
                signals.append("均线空头排列")
                
            # 黄金交叉 (短期上穿长期)
            if sma_short > sma_long and indicators.get('sma_cross', False):
                system_scores['trend'] += 20
                signals.append("均线黄金交叉")
            # 死亡交叉 (短期下穿长期)
            elif sma_short < sma_long and indicators.get('sma_cross', False):
                system_scores['trend'] -= 20
                signals.append("均线死亡交叉")
        
        # =============== 2. 动量反转系统 ===============
        # 基于Wilder的RSI和Lane的随机指标KDJ
        
        # RSI分析 (Wilder的原始RSI设计)
        rsi = indicators['rsi']
        
        # RSI超买超卖信号 (Wilder的标准区间)
        if rsi <= 30:
            # 超卖区域 - Wilder的反转信号
            oversold_strength = 40 + (30 - rsi)  # 30->40, 20->50, 10->60
            system_scores['momentum'] += oversold_strength
            if rsi < 20:
                signals.append("RSI极度超卖")
            else:
                signals.append("RSI超卖")
        elif rsi >= 70:
            # 超买区域 - Wilder的反转信号
            overbought_strength = 40 + (rsi - 70)  # 70->40, 80->50, 90->60
            system_scores['momentum'] -= overbought_strength
            if rsi > 80:
                signals.append("RSI极度超买")
            else:
                signals.append("RSI超买")
                
        # RSI背离分析 (Cardwell的RSI背离理论)
        if indicators.get('rsi_divergence') == 'bullish':
            system_scores['momentum'] += 50
            signals.append("RSI看涨背离")
        elif indicators.get('rsi_divergence') == 'bearish':
            system_scores['momentum'] -= 50
            signals.append("RSI看跌背离")
            
        # KDJ分析 (George Lane的随机指标理论)
        kdj = indicators['kdj']
        k_value = kdj['k']
        d_value = kdj['d']
        j_value = kdj['j']
        
        # KDJ信号 (Lane的信号系统)
        if k_value < 20 and k_value > d_value:
            # KDJ金叉(超卖区) - Lane的强烈买入信号
            system_scores['momentum'] += 40
            signals.append("KDJ金叉(超卖区)")
        elif k_value > 80 and k_value < d_value:
            # KDJ死叉(超买区) - Lane的强烈卖出信号
            system_scores['momentum'] -= 40
            signals.append("KDJ死叉(超买区)")
            
        # J值极值分析 (Lane的超买超卖理论扩展)
        if j_value < 0:
            # J值超卖 - 极端超卖信号
            system_scores['momentum'] += 30
            signals.append("J值超卖")
        elif j_value > 100:
            # J值超买 - 极端超买信号
            system_scores['momentum'] -= 30
            signals.append("J值超买")
            
        # =============== 3. 价格波动系统 ===============
        # 基于Bollinger带和Donchian通道
        
        # 布林带分析 (John Bollinger的原始设计)
        bb = indicators['bollinger']
        bb_upper = bb['upper']
        bb_middle = bb['middle']
        bb_lower = bb['lower']
        bb_width = bb.get('bandwidth', 0)
        bb_percent = bb.get('percent_b', 0.5)
        
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
                    
        # Donchian通道分析 (Richard Donchian的突破系统)
        if 'donchian' in indicators:
            dc = indicators['donchian']
            dc_upper = dc.get('upper', 0)  # 最高价通道
            dc_lower = dc.get('lower', 0)  # 最低价通道
            
            if current_price > dc_upper:
                # 突破上轨 - Donchian的买入信号
                system_scores['volatility'] += 40
                signals.append("突破Donchian上轨")
            elif current_price < dc_lower:
                # 突破下轨 - Donchian的卖出信号
                system_scores['volatility'] -= 40
                signals.append("突破Donchian下轨")
        
        # =============== 4. K线形态分析 ===============
        # 基于Steve Nison的蜡烛图理论
        
        if patterns:
            pattern_score = 0
            pattern_count = 0
            
            for pattern in patterns:
                pattern_count += 1
                pattern_weight = pattern.confidence / 100
                
                # 基于Nison和Bulkowski的研究对不同形态赋予权重
                if "启明星" in pattern.name or "晨星" in pattern.name:
                    # 启明星是强烈的底部反转信号
                    pattern_score += 100 * pattern_weight
                    signals.append(f"{pattern.name}形态")
                elif "黄昏星" in pattern.name or "暮星" in pattern.name:
                    # 黄昏星是强烈的顶部反转信号
                    pattern_score -= 100 * pattern_weight
                    signals.append(f"{pattern.name}形态")
                elif "看涨吞没" in pattern.name or "锤子" in pattern.name:
                    # 看涨吞没和锤子线是较强的底部反转信号
                    pattern_score += 80 * pattern_weight
                    signals.append(f"{pattern.name}形态")
                elif "看跌吞没" in pattern.name or "吊颈" in pattern.name:
                    # 看跌吞没和吊颈线是较强的顶部反转信号
                    pattern_score -= 80 * pattern_weight
                    signals.append(f"{pattern.name}形态")
                elif "看涨" in pattern.name:
                    # 其他看涨形态
                    pattern_score += 60 * pattern_weight
                    signals.append(f"{pattern.name}形态")
                elif "看跌" in pattern.name:
                    # 其他看跌形态
                    pattern_score -= 60 * pattern_weight
                    signals.append(f"{pattern.name}形态")
                    
            # 将形态得分分配到各个系统中
            if pattern_count > 0:
                normalized_pattern_score = pattern_score / pattern_count
                
                # 形态主要影响动量系统和波动系统
                system_scores['momentum'] += normalized_pattern_score * 0.5
                system_scores['volatility'] += normalized_pattern_score * 0.5
        
        # =============== 5. 系统综合评分 ===============
        # 基于多因子模型理论
        
        # 规范化各系统得分到 -100 到 100 的范围
        for key in system_scores:
            system_scores[key] = max(-100, min(100, system_scores[key]))
        
        # 系统权重 (基于市场环境的动态权重)
        # 在不同市场环境下，不同系统的有效性不同
        weights = {
            'trend': 0.4,      # 趋势确认系统权重
            'momentum': 0.3,   # 动量反转系统权重
            'volatility': 0.3  # 价格波动系统权重
        }
        
        # 计算加权得分
        weighted_score = sum(system_scores[key] * weights[key] for key in weights)
        
        # 将加权得分转换为0-100的置信度
        # 使用线性映射，更直观且符合行业惯例
        confidence = 50 + weighted_score / 2
        
        # 将置信度四舍五入到一位小数
        confidence = round(confidence, 1)
        
        # 根据置信度生成交易建议
        if confidence >= 75:
            advice = "强烈买入"
            color = self.colors['strong_buy']
        elif confidence >= 60:
            advice = "建议买入"
            color = self.colors['buy']
        elif confidence <= 25:
            advice = "强烈卖出"
            color = self.colors['strong_sell']
        elif confidence <= 40:
            advice = "建议卖出"
            color = self.colors['sell']
        else:
            advice = "观望"
            color = self.colors['neutral']
            
        # 添加置信度解释
        confidence_explanation = self.get_confidence_explanation(system_scores, confidence)
            
        return {
            'advice': advice,
            'confidence': confidence,
            'signals': signals,
            'color': color,
            'explanation': confidence_explanation,
            'system_scores': system_scores
        }
        
    def get_confidence_explanation(self, system_scores: Dict, confidence: float) -> str:
        """
        生成置信度解释，基于各量化系统的得分
        
        参数:
            system_scores: 各系统得分
            confidence: 最终置信度
            
        返回:
            str: 置信度解释
        """
        # 确定主导系统
        abs_scores = {k: abs(v) for k, v in system_scores.items()}
        dominant_system = max(abs_scores, key=abs_scores.get)
        
        # 确定信号强度描述
        if confidence >= 80 or confidence <= 20:
            strength = "极强"
        elif confidence >= 70 or confidence <= 30:
            strength = "强烈"
        elif confidence >= 60 or confidence <= 40:
            strength = "明确"
        elif confidence >= 55 or confidence <= 45:
            strength = "轻微"
        else:
            strength = "中性"
            
        # 确定方向
        if confidence > 50:
            direction = "看涨"
        elif confidence < 50:
            direction = "看跌"
        else:
            direction = "中性"
            
        # 系统解释
        system_explanations = {
            'trend': {
                'positive': "趋势确认系统显示上升趋势",
                'negative': "趋势确认系统显示下降趋势",
                'neutral': "趋势确认系统显示无明确趋势"
            },
            'momentum': {
                'positive': "动量反转系统显示超卖状态",
                'negative': "动量反转系统显示超买状态",
                'neutral': "动量反转系统处于中性区域"
            },
            'volatility': {
                'positive': "价格波动系统显示支撑突破信号",
                'negative': "价格波动系统显示阻力突破信号",
                'neutral': "价格波动系统无明确突破信号"
            }
        }
        
        # 确定主导系统的状态
        if system_scores[dominant_system] > 30:
            system_state = 'positive'
        elif system_scores[dominant_system] < -30:
            system_state = 'negative'
        else:
            system_state = 'neutral'
            
        # 生成主要解释
        main_explanation = system_explanations[dominant_system][system_state]
        
        # 生成次要系统解释
        secondary_systems = []
        for system, score in system_scores.items():
            if system != dominant_system and abs(score) > 30:
                if score > 30:
                    secondary_systems.append(system_explanations[system]['positive'])
                elif score < -30:
                    secondary_systems.append(system_explanations[system]['negative'])
        
        # 组合解释，确保置信度只显示一位小数
        if secondary_systems:
            explanation = f"{strength}{direction}信号 ({confidence:.1f}%): {main_explanation}，同时{'，'.join(secondary_systems)}"
        else:
            explanation = f"{strength}{direction}信号 ({confidence:.1f}%): {main_explanation}"
            
        return explanation

    def backtest_strategy(self, data: pd.DataFrame) -> Dict:
        """
        基于行业标准模型的回测策略
        
        使用标准的回测方法论，包括:
        - 基于Markowitz的投资组合理论
        - Sharpe比率计算
        - 基于Kestner的交易系统评估指标
        - 标准的交易成本模型
        
        参数:
            data: 股票历史数据
            
        返回:
            Dict: 回测结果统计
        """
        # 确保有足够的数据进行回测 (至少需要50个交易日)
        if len(data) < 50:
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
                'annualized_return': 0
            }
            
        # 准备数据
        close = data['Close'].copy()
        high = data['High'].copy()
        low = data['Low'].copy()
        open_price = data['Open'].copy()
        volume = data['Volume'].copy() if 'Volume' in data.columns else pd.Series(np.ones(len(close)), index=close.index)
        dates = data.index
        
        # =============== 1. 交易参数设置 ===============
        # 使用标准的交易成本模型
        
        # 交易成本模型 (基于IBKR的固定费率模型)
        commission_per_share = 0.005  # 每股0.005美元 (IBKR固定费率)
        min_commission = 1.0  # 最低每单1美元
        max_commission_pct = 0.01  # 最高为总成交金额的1%
        
        # 滑点模型 (基于Kissell和Glantz的市场冲击模型)
        # 滑点 = 基础滑点 + 市场冲击系数 * (交易量/日均交易量)
        base_slippage_pct = 0.0005  # 基础滑点，假设为成交价的0.05%
        market_impact_factor = 0.1  # 市场冲击系数
        
        # 风险管理参数 (基于专业交易系统的标准设置)
        stop_loss_pct = 0.07  # 7%止损 (行业标准风险管理)
        take_profit_pct = 0.15  # 15%止盈 (风险回报比约为1:2)
        max_hold_days = 20  # 最长持有20个交易日 (约一个月)
        
        # 头寸规模 (基于Van K. Tharp的头寸规模模型)
        risk_per_trade_pct = 0.02  # 每笔交易风险资金的2%
        initial_capital = 10000.0  # 初始资金
        
        # =============== 2. 技术指标计算 ===============
        # 使用标准的技术指标计算方法
        
        # 计算RSI (Wilder的原始RSI计算方法)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        # 使用Wilder的平滑方法
        for i in range(14, len(delta)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * 13 + gain.iloc[i]) / 14
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * 13 + loss.iloc[i]) / 14
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 计算MACD (Appel的原始MACD计算方法)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal_line
        
        # 计算布林带 (Bollinger的原始布林带计算方法)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)
        
        # 计算移动平均线 (标准SMA计算)
        sma5 = close.rolling(window=5).mean()
        sma10 = close.rolling(window=10).mean()
        sma50 = close.rolling(window=50).mean()
        sma200 = close.rolling(window=200).mean() if len(close) >= 200 else pd.Series(np.nan, index=close.index)
        
        # 计算ATR (Wilder的真实波动幅度计算方法)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        # 使用Wilder的平滑方法
        for i in range(14, len(tr)):
            atr.iloc[i] = (atr.iloc[i-1] * 13 + tr.iloc[i]) / 14
        
        # =============== 3. 信号生成 ===============
        # 使用标准的交易信号生成方法
        
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
        signals['atr'] = atr
        
        # 生成买入信号 (基于多重确认系统)
        signals['buy_signal'] = 0
        
        # RSI超卖信号 (Wilder的RSI交易系统)
        rsi_buy = (rsi < 30)
        
        # MACD金叉信号 (Appel的MACD交易系统)
        macd_buy = (macd_line > signal_line) & (macd_line.shift() < signal_line.shift())
        
        # 布林带下轨支撑信号 (Bollinger的布林带交易系统)
        bb_buy = (close < lower_band)
        
        # 移动平均线支撑信号 (标准的移动平均线交易系统)
        ma_buy = (close > sma5) & (close > sma10) & (sma5 > sma5.shift())
        
        # 综合买入信号 (至少两个系统确认)
        signals['buy_signal'] = ((rsi_buy.astype(int) + macd_buy.astype(int) + 
                                 bb_buy.astype(int) + ma_buy.astype(int)) >= 2).astype(int)
        
        # 生成卖出信号 (基于多重确认系统)
        signals['sell_signal'] = 0
        
        # RSI超买信号
        rsi_sell = (rsi > 70)
        
        # MACD死叉信号
        macd_sell = (macd_line < signal_line) & (macd_line.shift() > signal_line.shift())
        
        # 布林带上轨阻力信号
        bb_sell = (close > upper_band)
        
        # 移动平均线阻力信号
        ma_sell = (close < sma5) & (close < sma10) & (sma5 < sma5.shift())
        
        # 综合卖出信号 (至少两个系统确认)
        signals['sell_signal'] = ((rsi_sell.astype(int) + macd_sell.astype(int) + 
                                  bb_sell.astype(int) + ma_sell.astype(int)) >= 2).astype(int)
        
        # =============== 4. 回测执行 ===============
        # 使用标准的回测执行方法
        
        # 初始化回测变量
        position = 0  # 0表示空仓，1表示多头，-1表示空头
        entry_price = 0.0  # 入场价格
        entry_date = None  # 入场日期
        capital = initial_capital  # 当前资金
        equity = [initial_capital]  # 权益曲线
        trades = []  # 交易记录
        
        # 遍历每个交易日
        for i in range(50, len(signals)):
            current_date = dates[i]
            current_price = close.iloc[i]
            current_high = high.iloc[i]
            current_low = low.iloc[i]
            current_volume = volume.iloc[i]
            avg_volume = volume.iloc[i-20:i].mean()  # 20日平均成交量
            
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
                reverse_signal = (position == 1 and signals['sell_signal'].iloc[i]) or \
                                (position == -1 and signals['buy_signal'].iloc[i])
                
                # 平仓条件
                if stop_triggered or take_profit_triggered or max_hold_triggered or reverse_signal:
                    # 计算交易头寸大小 (在计算滑点前先确定shares)
                    shares = int(risk_per_trade_pct * capital / (stop_loss_pct * entry_price))
                    shares = max(1, min(shares, int(capital / entry_price)))  # 确保头寸合理
                    
                    # 确定平仓价格
                    if stop_triggered:
                        exit_price = stop_price
                        exit_reason = "止损"
                    elif take_profit_triggered:
                        exit_price = take_profit_price
                        exit_reason = "止盈"
                    elif max_hold_triggered:
                        exit_price = current_price
                        exit_reason = "持有时间到期"
                    else:  # reverse_signal
                        exit_price = current_price
                        exit_reason = "反向信号"
                    
                    # 计算滑点
                    volume_ratio = min(1.0, shares / avg_volume) if avg_volume > 0 else 0.1  # 防止除以0
                    slippage_pct = base_slippage_pct + market_impact_factor * volume_ratio
                    
                    if position == 1:  # 多头平仓
                        exit_price = exit_price * (1 - slippage_pct)  # 考虑滑点
                    else:  # 空头平仓
                        exit_price = exit_price * (1 + slippage_pct)  # 考虑滑点
                    
                    # 计算交易成本
                    commission = max(min_commission, min(shares * commission_per_share, 
                                                       exit_price * shares * max_commission_pct))
                    
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
                if signals['buy_signal'].iloc[i]:
                    position = 1  # 多头
                    entry_price = current_price * (1 + base_slippage_pct)  # 考虑滑点
                    entry_date = current_date
                
                # 检查卖出信号 (做空)
                elif signals['sell_signal'].iloc[i]:
                    position = -1  # 空头
                    entry_price = current_price * (1 - base_slippage_pct)  # 考虑滑点
                    entry_date = current_date
            
            # 更新权益曲线
            equity.append(capital)
        
        # =============== 5. 回测结果分析 ===============
        # 使用标准的回测评估指标
        
        # 如果没有交易，返回空结果
        if not trades:
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
                'annualized_return': 0
            }
        
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
        final_return = (capital - initial_capital) / initial_capital * 100
        
        # 计算净利润
        net_profit = capital - initial_capital
        
        # 计算权益曲线的日收益率
        equity_series = pd.Series(equity)
        daily_returns = equity_series.pct_change().dropna()
        
        # 计算最大回撤 (Maximum Drawdown)
        # 使用Kestner的方法计算最大回撤
        peak = equity_series.expanding().max()
        drawdown = (equity_series / peak - 1) * 100
        max_drawdown = abs(drawdown.min())
        
        # 计算Sharpe比率 (使用标准的Sharpe比率计算方法)
        # Sharpe = (平均收益率 - 无风险利率) / 收益率标准差
        risk_free_rate = 0.02 / 252  # 假设年化无风险利率为2%，转换为日利率
        excess_returns = daily_returns - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if len(excess_returns) > 0 and excess_returns.std() > 0 else 0
        
        # 计算Sortino比率 (只考虑下行风险)
        # Sortino = (平均收益率 - 无风险利率) / 下行风险标准差
        downside_returns = excess_returns[excess_returns < 0]
        sortino_ratio = (excess_returns.mean() / downside_returns.std()) * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        # 计算年化收益率
        days = (dates[-1] - dates[50]).days
        years = days / 365
        annualized_return = ((1 + final_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
        
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
            'annualized_return': round(annualized_return, 1)
        }
    
    def analyze_stocks(self, symbols: List[str], names: Dict[str, str]) -> List[Dict]:
        results = []
        total = len(symbols)
        print("\n开始技术分析...")
        
        for index, symbol in enumerate(symbols, 1):
            try:
                print(f"\n[{index}/{total} - {index/total*100:.1f}%] 分析: {names.get(symbol, symbol)} ({symbol})")
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1y")
                
                if hist.empty:
                    print(f"⚠️ 无法获取 {symbol} 的数据，跳过")
                    continue
                
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                print("计算技术指标...")
                rsi = self.calculate_rsi(hist['Close'])
                macd, signal, hist_macd = self.calculate_macd(hist['Close'])
                k, d, j = self.calculate_kdj(hist['High'], hist['Low'], hist['Close'])
                bb_upper, bb_middle, bb_lower, bb_width, bb_percent = self.calculate_bollinger_bands(hist['Close'])
                
                print("分析K线形态...")
                patterns = self.identify_candlestick_patterns(hist.tail(5))
                
                indicators = {
                    'rsi': rsi,
                    'macd': {'macd': macd, 'signal': signal, 'hist': hist_macd},
                    'kdj': {'k': k, 'd': d, 'j': j},
                    'bollinger': {
                        'upper': bb_upper, 
                        'middle': bb_middle, 
                        'lower': bb_lower,
                        'bandwidth': bb_width,
                        'percent_b': bb_percent
                    }
                }
                
                print("生成交易建议...")
                advice = self.generate_trading_advice(indicators, current_price, patterns)
                
                print("执行策略回测...")
                backtest_results = self.backtest_strategy(hist)
                
                results.append({
                    'symbol': symbol,
                    'name': names.get(symbol, symbol),
                    'price': current_price,
                    'change': price_change,
                    'indicators': indicators,
                    'patterns': patterns,
                    'advice': advice,
                    'backtest': backtest_results
                })
                
                print(f"✅ {symbol} 分析完成")
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错", exc_info=True)
                print(f"❌ {symbol} 分析失败: {str(e)}")
                continue
        
        return results

    def generate_html_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        """
        生成HTML分析报告
        
        参数:
            results: 分析结果列表
            title: 报告标题
            
        返回:
            str: HTML报告内容
        """
        timestamp = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')
        report_file = self.results_path / f"stock_analysis_{timestamp}.html"
        
        # 生成时间戳
        formatted_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        
        # HTML头部
        html = f"""<!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header-banner {{
                    background-color: #3A7CA5; /* 更重的青蓝色 */
                    padding: 30px 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .header-banner h1 {{
                    color: white;
                    font-weight: 600;
                    margin-bottom: 10px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
                }}
                .header-banner p {{
                    color: rgba(255,255,255,0.9);
                    font-size: 16px;
                }}
                .stock-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stock-card {{
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    overflow: hidden;
                    transition: transform 0.3s ease;
                }}
                .stock-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                }}
                .card-header {{
                    padding: 15px;
                    color: white;
                    font-weight: 600;
                    height: 80px; /* 固定高度 */
                    display: flex;
                    align-items: center;
                }}
                .card-body {{
                    padding: 12px; /* 从20px减小到12px，约60% */
                }}
                .stock-info {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    width: 100%;
                }}
                .stock-name {{
                    font-size: 16px;
                    font-weight: 600;
                    max-width: 65%;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .stock-price {{
                    font-size: 16px;
                    font-weight: 600;
                    text-align: right;
                }}
                .price-change {{
                    font-size: 14px;
                    margin-left: 5px;
                }}
                .positive {{
                    color: #28a745;
                }}
                .negative {{
                    color: #dc3545;
                }}
                .neutral {{
                    color: #ffc107;
                }}
                .indicator-section {{
                    margin-bottom: 12px; /* 从20px减小到12px */
                    background-color: #E8F5E9; /* 温和的薄荷绿 */
                    padding: 15px;
                    border-radius: 10px; /* 从12px减小到10px */
                    height: 220px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid rgba(0,0,0,0.05);
                }}
                .pattern-section-container {{
                    margin-bottom: 12px; /* 从20px减小到12px */
                    background-color: #F3E5F5; /* 温和的淡紫色 */
                    padding: 15px;
                    border-radius: 10px; /* 从12px减小到10px */
                    height: 150px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid rgba(0,0,0,0.05);
                }}
                .section-title {{
                    font-weight: 600;
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #ddd;
                    color: #2E8B57; /* 海绿色标题 */
                }}
                .indicator-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                .indicator-table td {{
                    padding: 6px 10px;
                    border-bottom: 1px solid #eee;
                }}
                .indicator-label {{
                    font-size: 13px;
                    color: #666;
                    width: 40%;
                }}
                .indicator-value {{
                    font-size: 13px;
                    color: #333;
                }}
                .pattern-section {{
                    text-align: center;
                    margin: 15px 0;
                    min-height: 50px; /* 最小高度 */
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-wrap: wrap;
                }}
                .pattern-tag {{
                    display: inline-block;
                    background: {self.colors['info']};
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                    margin-right: 5px;
                    margin-bottom: 5px;
                    font-size: 12px;
                }}
                .advice-section {{
                    margin-bottom: 12px; /* 从20px减小到12px */
                    padding: 15px;
                    background: #E3F2FD; /* 温和的天蓝色 */
                    border-radius: 10px; /* 从12px减小到10px */
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid rgba(0,0,0,0.05);
                }}
                .advice-header {{
                    text-align: center;
                    margin-bottom: 15px;
                }}
                .advice-text {{
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                .confidence {{
                    font-size: 14px;
                    color: #666;
                }}
                .explanation {{
                    font-size: 14px;
                    color: #333;
                    margin: 10px 0;
                    text-align: left;
                    line-height: 1.5;
                }}
                .signals-container {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 15px;
                }}
                .signal-tag {{
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    color: #333;
                }}
                .signal-trend {{
                    background-color: #D4E6F1; /* 浅蓝色 - 趋势信号 */
                }}
                .signal-momentum {{
                    background-color: #D5F5E3; /* 浅绿色 - 动量信号 */
                }}
                .signal-volatility {{
                    background-color: #FCF3CF; /* 浅黄色 - 波动信号 */
                }}
                .signal-pattern {{
                    background-color: #FADBD8; /* 浅红色 - 形态信号 */
                }}
                .signal-macd {{
                    background-color: #F9E79F; /* 淡金色 - MACD信号 */
                }}
                .signal-rsi {{
                    background-color: #D7BDE2; /* 浅紫色 - RSI信号 */
                }}
                .signal-kdj {{
                    background-color: #F5CBA7; /* 浅橙色 - KDJ信号 */
                }}
                .signal-bb {{
                    background-color: #AED6F1; /* 天蓝色 - 布林带信号 */
                }}
                .signal-ma {{
                    background-color: #A3E4D7; /* 薄荷色 - 均线信号 */
                }}
                .backtest-section {{
                    margin-bottom: 3px; /* 从5px减小到3px */
                    background-color: #FFF8E1; /* 温和的浅黄色 */
                    padding: 15px;
                    border-radius: 10px; /* 从12px减小到10px */
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid rgba(0,0,0,0.05);
                }}
                .backtest-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                .backtest-table td {{
                    padding: 6px 10px;
                    border-bottom: 1px solid #eee;
                }}
                .backtest-label {{
                    font-size: 13px;
                    color: #666;
                    width: 40%;
                }}
                .backtest-value {{
                    font-size: 13px;
                    color: #333;
                }}
                .manual-card {{
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 30px;
                }}
                .manual-title {{
                    font-weight: 600;
                    font-size: 20px;
                    margin-bottom: 15px;
                    color: #2E8B57;
                    border-bottom: 2px solid #88BDBC;
                    padding-bottom: 8px;
                }}
                .manual-section {{
                    margin-bottom: 15px;
                }}
                .manual-section-title {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #2E8B57;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                }}
                @media (max-width: 768px) {{
                    .stock-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .indicator-section {{
                        height: auto;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-banner">
                    <h1>{title}</h1>
                    <p>生成时间: {formatted_time}</p>
                </div>
                
                <div class="stock-grid">
        """
        
        # 生成股票卡片
        for result in results:
            # 确保数值有效，避免NaN或无效值
            rsi_value = result['indicators']['rsi']
            rsi_display = f"{rsi_value:.1f}" if not pd.isna(rsi_value) else "N/A"
            
            k_value = result['indicators']['kdj']['k']
            d_value = result['indicators']['kdj']['d']
            j_value = result['indicators']['kdj']['j']
            k_display = f"{k_value:.1f}" if not pd.isna(k_value) else "N/A"
            d_display = f"{d_value:.1f}" if not pd.isna(d_value) else "N/A"
            j_display = f"{j_value:.1f}" if not pd.isna(j_value) else "N/A"
            
            macd_value = result['indicators']['macd']['macd']
            signal_value = result['indicators']['macd']['signal']
            hist_value = result['indicators']['macd']['hist']
            macd_display = f"{macd_value:.3f}" if not pd.isna(macd_value) else "N/A"
            signal_display = f"{signal_value:.3f}" if not pd.isna(signal_value) else "N/A"
            hist_display = f"{hist_value:.3f}" if not pd.isna(hist_value) else "N/A"
            
            bb_upper = result['indicators']['bollinger']['upper']
            bb_middle = result['indicators']['bollinger']['middle']
            bb_lower = result['indicators']['bollinger']['lower']
            bb_upper_display = f"{bb_upper:.2f}" if not pd.isna(bb_upper) else "N/A"
            bb_middle_display = f"{bb_middle:.2f}" if not pd.isna(bb_middle) else "N/A"
            bb_lower_display = f"{bb_lower:.2f}" if not pd.isna(bb_lower) else "N/A"
            
            # 生成K线形态HTML
            patterns_html = ""
            if result.get('patterns'):
                for p in result['patterns']:
                    patterns_html += f"<span class='pattern-tag' title='{p.description}'>{p.name} ({p.confidence}%)</span>"
            
            # 生成信号标签
            signals_html = ""
            for signal in result['advice']['signals']:
                signal_class = "signal-tag"
                
                # 根据信号类型添加不同的样式类
                if "MACD" in signal:
                    signal_class += " signal-macd"
                elif "RSI" in signal:
                    signal_class += " signal-rsi"
                elif "KDJ" in signal or "J值" in signal:
                    signal_class += " signal-kdj"
                elif "布林" in signal:
                    signal_class += " signal-bb"
                elif "均线" in signal:
                    signal_class += " signal-ma"
                elif "趋势" in signal:
                    signal_class += " signal-trend"
                elif "形态" in signal:
                    signal_class += " signal-pattern"
                elif "超买" in signal or "超卖" in signal:
                    signal_class += " signal-momentum"
                elif "突破" in signal:
                    signal_class += " signal-volatility"
                else:
                    signal_class += " signal-trend"  # 默认类别
                
                signals_html += f"<span class='{signal_class}'>{signal}</span>"
            
            # 确定价格变化的颜色类
            price_change_class = "positive" if result['change'] > 0 else "negative"
            
            # 构建股票卡片HTML
            card = f"""
                <div class="stock-card">
                    <div class="card-header" style="background-color: {result['advice']['color']}">
                        <div class="stock-info">
                            <span class="stock-name" title="{result['name']} ({result['symbol']})">{result['name']} ({result['symbol']})</span>
                            <span class="stock-price">${result['price']:.2f}<br><span class="{price_change_class}">({result['change']:+.2f}%)</span></span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="indicator-section">
                            <div class="section-title">技术指标分析</div>
                            <table class="indicator-table">
                                <tr>
                                    <td class="indicator-label">RSI (14日)</td>
                                    <td class="indicator-value">{rsi_display}</td>
                                </tr>
                                <tr>
                                    <td class="indicator-label">KDJ (9日)</td>
                                    <td class="indicator-value">K: {k_display} | D: {d_display} | J: {j_display}</td>
                                </tr>
                                <tr>
                                    <td class="indicator-label">MACD (12,26,9)</td>
                                    <td class="indicator-value">MACD: {macd_display} | Signal: {signal_display} | Hist: {hist_display}</td>
                                </tr>
                                <tr>
                                    <td class="indicator-label">布林带 (20日)</td>
                                    <td class="indicator-value">上轨: {bb_upper_display} | 中轨: {bb_middle_display} | 下轨: {bb_lower_display}</td>
                                </tr>
                            </table>
                </div>

                        <div class="pattern-section-container">
                            <div class="section-title">K线形态分析</div>
                            <div class="pattern-section">
                                {patterns_html if result.get('patterns') else "<span style='color: #666; font-style: italic;'>无明显K线形态</span>"}
                        </div>
                        </div>
                        
                        <div class="advice-section">
                            <div class="advice-header">
                                <div class="advice-text" style="color: {result['advice']['color']}">{result['advice']['advice']}</div>
                                <div class="confidence">置信度: {result['advice']['confidence']}%</div>
                        </div>
                            <div class="explanation">
                                {result['advice']['explanation']}
                        </div>
                            <div class="signals-container">
                                {signals_html}
                        </div>
                        </div>
                        
                        <div class="backtest-section">
                            <div class="section-title">回测结果</div>
                            <table class="backtest-table">
                                <tr>
                                    <td class="backtest-label">总交易次数</td>
                                    <td class="backtest-value">{result['backtest']['total_trades']}</td>
                                    <td class="backtest-label">胜率</td>
                                    <td class="backtest-value">{result['backtest']['win_rate']}%</td>
                                </tr>
                                <tr>
                                    <td class="backtest-label">平均收益</td>
                                    <td class="backtest-value">${result['backtest']['avg_profit']}</td>
                                    <td class="backtest-label">盈亏比</td>
                                    <td class="backtest-value">{result['backtest']['profit_factor']}</td>
                                </tr>
                                <tr>
                                    <td class="backtest-label">最大收益</td>
                                    <td class="backtest-value">${result['backtest']['max_profit']}</td>
                                    <td class="backtest-label">最大亏损</td>
                                    <td class="backtest-value">${result['backtest']['max_loss']}</td>
                                </tr>
                                <tr>
                                    <td class="backtest-label">最大回撤</td>
                                    <td class="backtest-value">{result['backtest']['max_drawdown']}%</td>
                                    <td class="backtest-label">连续亏损次数</td>
                                    <td class="backtest-value">{result['backtest']['consecutive_losses']}</td>
                                </tr>
                                <tr>
                                    <td class="backtest-label">平均持仓天数</td>
                                    <td class="backtest-value">{result['backtest']['avg_hold_days']}</td>
                                    <td class="backtest-label">总收益率</td>
                                    <td class="backtest-value">{result['backtest']['final_return']}%</td>
                                </tr>
                                <tr>
                                    <td class="backtest-label">Sharpe比率</td>
                                    <td class="backtest-value">{result['backtest']['sharpe_ratio']}</td>
                                    <td class="backtest-label">Sortino比率</td>
                                    <td class="backtest-value">{result['backtest']['sortino_ratio']}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            """
            html += card
        
        # 添加说明书卡片
        html += """
                </div>
                
                        <div class="manual-card">
                    <div class="manual-title">分析方法说明</div>
                    
                    <div class="manual-section">
                        <div class="manual-section-title">技术指标分析</div>
                        <p>本工具采用多系统量化模型进行技术分析，基于以下权威交易系统：</p>
                        <ul>
                            <li><strong>趋势确认系统</strong> - 基于Dow理论和Appel的MACD原始设计，通过分析价格趋势和动量变化，识别市场主导方向。</li>
                            <li><strong>动量反转系统</strong> - 基于Wilder的RSI和Lane的随机指标，捕捉市场超买超卖状态和潜在反转点。</li>
                            <li><strong>价格波动系统</strong> - 基于Bollinger带和Donchian通道，分析价格波动性和突破模式。</li>
                        </ul>
                        </div>
                    
                    <div class="manual-section">
                        <div class="manual-section-title">交易建议生成</div>
                        <p>交易建议基于多因子模型理论，综合评估各系统信号，置信度表示信号强度：</p>
                        <ul>
                            <li><strong>强烈买入/卖出</strong>: 置信度≥75%或≤25%，表示多个系统高度一致的信号</li>
                            <li><strong>建议买入/卖出</strong>: 置信度在60-75%或25-40%之间，表示系统间存在较强共识</li>
                            <li><strong>观望</strong>: 置信度在40-60%之间，表示系统间信号不明确或相互矛盾</li>
                        </ul>
                    </div>
                    
                    <div class="manual-section">
                        <div class="manual-section-title">回测分析方法</div>
                        <p>回测采用行业标准方法论，包括：</p>
                        <ul>
                            <li><strong>Markowitz投资组合理论</strong> - 科学的风险管理方法，优化资产配置和风险控制</li>
                            <li><strong>Kestner交易系统评估</strong> - 专业的回撤计算和系统性能评估方法</li>
                            <li><strong>Sharpe/Sortino比率</strong> - 标准化风险调整收益指标，衡量策略的风险回报效率</li>
                            <li><strong>Van K. Tharp头寸模型</strong> - 优化资金管理和头寸规模，控制单笔交易风险</li>
                        </ul>
                </div>
                
                    <div class="manual-section">
                        <div class="manual-section-title">使用建议</div>
                        <p>本工具提供的分析结果应作为投资决策的参考，而非唯一依据。建议结合基本面分析、市场环境和个人风险偏好综合考量。交易策略的有效性可能随市场环境变化而改变，请定期评估策略表现。</p>
                        <div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <strong>免责声明：</strong> 本工具仅供参考，不构成投资建议。投资有风险，入市需谨慎。
                        </div>
                    </div>
            </div>
            
                <div class="footer">
                    <p>美股技术面分析工具 Alpha v0.2.5 | &copy; 2025</p>
            </div>
            </div>
        </body>
        </html>
        """
        
        # 保存HTML报告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n✅ 报告已生成: {report_file}")
            
            # 获取绝对路径（仅用于返回和显示）
            abs_path = os.path.abspath(report_file)
            print(f"📊 报告路径：{abs_path}")
            
            # 注意：不在这里打开浏览器，而是返回路径让主程序决定是否打开
        except Exception as e:
            print(f"❌ 保存报告时出错: {str(e)}")
        
        return str(report_file)

    def clean_reports(self, days_threshold=None):
        """
        清理生成的HTML报告文件
        
        参数:
            days_threshold: 清理多少天前的文件，None表示清理所有文件
            
        返回:
            int: 删除的文件数量
        """
        report_files = list(self.results_path.glob("stock_analysis_*.html"))
        
        if not report_files:
            print("没有找到任何报告文件")
            return 0
        
        # 如果指定了天数阈值，筛选出符合条件的文件
        if days_threshold is not None:
            current_time = datetime.now()
            threshold_date = current_time - pd.Timedelta(days=days_threshold)
            
            filtered_files = []
            for file in report_files:
                # 从文件名中提取时间戳 (格式: stock_analysis_YYYYMMDD_HHMMSS.html)
                try:
                    timestamp_str = file.stem.split('_')[2] + '_' + file.stem.split('_')[3]
                    file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if file_date < threshold_date:
                        filtered_files.append(file)
                except (IndexError, ValueError):
                    # 如果文件名格式不符合预期，保守起见不删除
                    continue
                    
            report_files = filtered_files
            time_desc = f"{days_threshold}天前" if days_threshold > 0 else "所有"
        else:
            time_desc = "所有"
            
        count = len(report_files)
        if count == 0:
            print(f"没有找到{time_desc}的报告文件")
            return 0
            
        print(f"找到 {count} 个{time_desc}的报告文件，准备删除...")
        
        for file in report_files:
            try:
                file.unlink()
                print(f"已删除: {file.name}")
            except Exception as e:
                print(f"删除 {file.name} 时出错: {str(e)}")
                
        print(f"\n✅ 成功清理 {count} 个报告文件")
        return count
        
    def show_clean_menu(self):
        """
        显示清理报告文件的子菜单
        """
        while True:
            print("\n" + "=" * 50)
            print("清理报告文件".center(50))
            print("=" * 50)
            
            print("请选择清理选项：")
            print("1. 清理一周前的报告文件")
            print("2. 清理一个月前的报告文件")
            print("3. 清理所有报告文件")
            print("0. 返回主菜单")
            
            choice = input("\n请输入选项 (0-3): ").strip()
            
            if choice == "0":
                return
            elif choice == "1":
                confirm = input("\n确定要删除一周前的所有报告文件吗？此操作不可恢复 (y/n): ").strip().lower()
                if confirm == 'y' or confirm == 'yes':
                    self.clean_reports(days_threshold=7)
                else:
                    print("已取消清理操作")
            elif choice == "2":
                confirm = input("\n确定要删除一个月前的所有报告文件吗？此操作不可恢复 (y/n): ").strip().lower()
                if confirm == 'y' or confirm == 'yes':
                    self.clean_reports(days_threshold=30)
                else:
                    print("已取消清理操作")
            elif choice == "3":
                confirm = input("\n确定要删除所有报告文件吗？此操作不可恢复 (y/n): ").strip().lower()
                if confirm == 'y' or confirm == 'yes':
                    self.clean_reports(days_threshold=None)
                else:
                    print("已取消清理操作")
            else:
                print("无效的选项，请重新输入")
                
            input("\n按Enter键继续...")

if __name__ == "__main__":
    try:
        analyzer = StockAnalyzer()
        
        print("\n")
        print("=" * 50)
        print("美股技术面分析工具 Alpha v0.2.5".center(50))
        print("=" * 50)
        
        print("请选择操作模式：")
        print("1. 手动输入股票代码")
        print("2. 使用预设股票组合")  
        print("3. 清理历史报告文件")
        print("0. 退出程序")      
        mode = input("\n请输入模式编号 (0-3): ").strip()
        
        symbols = []
        names = {}
        title = "美股技术面分析工具Alpha v0.3"
        
        if mode == "0":
            print("\n正在退出程序...")
            print("提示：如需关闭虚拟环境，请在终端输入 'deactivate'")
            sys.exit(0)
        
        elif mode == "3":
            analyzer.show_clean_menu()
            sys.exit(0)
        
        elif mode == "1":
            print("\n请输入股票代码（最多10个，每行一个，支持自定义名称，格式：代码=名称）")
            print("示例：")
            print("AAPL=苹果")
            print("MSFT=微软")
            print("输入空行结束\n")
            
            count = 0
            while count < 10:
                line = input().strip()
                if not line:
                    break
                    
                if "=" in line:
                    code, name = line.split("=", 1)
                    code = code.strip().upper()
                    name = name.strip()
                else:
                    code = line.strip().upper()
                    name = code
                
                if code:
                    symbols.append(code)
                    names[code] = name
                    count += 1
            
            title = "自选股票分析报告"
            
        elif mode == "2":
            config_file = Path("config/watchlists.json")
            if not config_file.exists():
                config_dir = Path("config")
                config_dir.mkdir(exist_ok=True)
                
                watchlists_example = {
                    "美股科技": {
                        "AAPL": "苹果",
                        "MSFT": "微软",
                        "GOOGL": "谷歌",
                        "AMZN": "亚马逊",
                        "META": "Meta",
                        "NVDA": "英伟达",
                        "TSLA": "特斯拉"
                    },
                    "中概股": {
                        "BABA": "阿里巴巴",
                        "PDD": "拼多多",
                        "JD": "京东",
                        "BIDU": "百度",
                        "NIO": "蔚来",
                        "XPEV": "小鹏汽车",
                        "LI": "理想汽车"
                    },
                    "新能源": {
                        "TSLA": "特斯拉",
                        "NIO": "蔚来",
                        "XPEV": "小鹏汽车",
                        "LI": "理想汽车",
                        "RIVN": "Rivian",
                        "LCID": "Lucid"
                    }
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(watchlists_example, f, ensure_ascii=False, indent=4)
            
            with open(config_file, 'r', encoding='utf-8') as f:
                watchlists = json.load(f)
            
            print("\n可用的股票组合：")
            for i, group in enumerate(watchlists.keys(), 1):
                print(f"{i}. {group} ({len(watchlists[group])}支)")
            print(f"{len(watchlists) + 1}. 分析所有股票")
            
            choice = input("\n请选择要分析的组合 (输入编号): ").strip()
            
            if choice.isdigit():
                choice_idx = int(choice)
                if choice_idx <= len(watchlists):
                    group_name = list(watchlists.keys())[choice_idx - 1]
                    symbols = list(watchlists[group_name].keys())
                    names = watchlists[group_name]
                    title = f"{group_name}分析报告"
                elif choice_idx == len(watchlists) + 1:
                    for group_stocks in watchlists.values():
                        for code, name in group_stocks.items():
                            if code not in names:  # 避免重复
                                symbols.append(code)
                                names[code] = name
                    title = "全市场分析报告（预置股票列表）"
                else:
                    raise ValueError("无效的选择")
            else:
                raise ValueError("无效的输入")
        
        else:
            raise ValueError("无效的模式选择")
        
        if not symbols:
            raise ValueError("没有选择任何股票")
        
        print(f"\n开始分析 {len(symbols)} 支股票...")
        
        results = analyzer.analyze_stocks(symbols, names)
        
        if results:
            report_path = analyzer.generate_html_report(results, title)
            abs_path = os.path.abspath(report_path)
            
            print(f"\n✅ 分析完成！")
            print(f"📊 报告已生成：{abs_path}")
            
            # 在这里打开浏览器，确保只打开一次
            try:
                webbrowser.open(f'file://{abs_path}')
                print("🌐 报告已在浏览器中打开")
            except Exception as e:
                print(f"⚠️ 无法自动打开报告：{str(e)}")
                print("请手动打开上述文件查看报告")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except ValueError as e:
        print("\n")
        print("❌ 输入错误 ".center(50, "="))
        print(f"• 原因：{str(e)}")
        print("• 请重新运行程序并选择正确的选项")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n")
        print("⚠️ 程序已停止 ".center(50, "="))
        print("• 用户主动中断程序")
        print("• 感谢使用，再见！")
        print("="*50)
        
    except Exception as e:
        print("\n")
        print("❌ 程序异常 ".center(50, "="))
        print(f"• 错误信息：{str(e)}")
        print("• 请检查输入或联系开发者")
        print("="*50)
        logging.error("程序异常", exc_info=True)
    finally:
        print("\n感谢使用美股技术面分析工具！")
