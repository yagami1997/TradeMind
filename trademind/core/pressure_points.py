"""
TradeMind - 压力位分析器模块

本模块实现了股票压力位和支撑位的自动识别功能，包括：
- Fibonacci回调位计算
- 历史价格分布密度分析（基于Market Profile理论）
- 移动平均线支撑压力系统
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PressurePointAnalyzer:
    def __init__(self, price_data: pd.DataFrame):
        """
        初始化压力位分析器
        
        参数:
            price_data: 包含OHLCV数据的DataFrame
        """
        self.price_data = price_data
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.ma_periods = [20, 50, 200]
        
        # 保存分析结果
        self.support_levels = []
        self.resistance_levels = []
        self.all_levels = {}
        
    def calculate_fibonacci_levels(self, window: int = 120) -> Dict[float, float]:
        """
        计算Fibonacci回调位
        
        参数:
            window: 用于寻找高低点的窗口大小
            
        返回:
            Dict: Fibonacci水平位对应的价格
        """
        # 获取最近窗口期内的数据
        recent_data = self.price_data.tail(window)
        
        # 找到窗口期内的最高价和最低价
        trend_high = recent_data['High'].max()
        trend_low = recent_data['Low'].min()
        
        price_range = trend_high - trend_low
        fib_prices = {}
        
        # 计算上涨浪回调位（高到低）
        if self.is_downtrend(window=20):
            for level in self.fib_levels:
                fib_prices[level] = trend_high - price_range * level
                
        # 计算下跌浪反弹位（低到高）
        else:
            for level in self.fib_levels:
                fib_prices[level] = trend_low + price_range * level
                
        logger.debug(f"Fibonacci levels: {fib_prices}")
        return fib_prices
    
    def is_downtrend(self, window: int = 20) -> bool:
        """
        判断当前是否处于下降趋势
        
        参数:
            window: 判断趋势的窗口大小
            
        返回:
            bool: 如果是下降趋势则为True，否则为False
        """
        if len(self.price_data) < window:
            return False
        
        recent_data = self.price_data.tail(window)
        first_price = recent_data['Close'].iloc[0]
        last_price = recent_data['Close'].iloc[-1]
        
        return last_price < first_price
    
    def analyze_price_distribution(self, window: int = 60, bins: int = 20) -> List[Dict]:
        """
        基于Market Profile理论分析价格分布
        
        参数:
            window: 分析窗口大小
            bins: 价格区间的数量
            
        返回:
            List[Dict]: 主要价格区域及其强度
        """
        # 获取最近窗口期内的数据
        recent_data = self.price_data.tail(window)
        
        # 获取价格范围
        min_price = recent_data['Low'].min()
        max_price = recent_data['High'].max()
        
        # 创建价格区间
        bin_edges = np.linspace(min_price, max_price, bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # 统计每个价格区间的交易量
        hist, _ = np.histogram(recent_data['Close'], bins=bin_edges, weights=recent_data['Volume'])
        
        # 标准化成强度百分比
        if hist.sum() > 0:
            strength = (hist / hist.sum() * 100).astype(int)
        else:
            strength = np.zeros_like(hist)
        
        # 创建价格分布结果
        distribution = []
        for i in range(len(bin_centers)):
            distribution.append({
                'price': bin_centers[i],
                'strength': int(strength[i]),
                'volume': int(hist[i])
            })
        
        # 按强度降序排序
        distribution.sort(key=lambda x: x['strength'], reverse=True)
        
        # 过滤强度高于平均值的价格区域
        avg_strength = sum(item['strength'] for item in distribution) / len(distribution)
        significant_areas = [item for item in distribution if item['strength'] > avg_strength]
        
        return significant_areas
    
    def get_ma_support_resistance(self) -> Dict[str, float]:
        """
        计算移动平均线支撑压力位
        
        返回:
            Dict: 各周期均线位置
        """
        current_price = self.price_data['Close'].iloc[-1]
        ma_levels = {}
        
        for period in self.ma_periods:
            if len(self.price_data) >= period:
                ma = self.price_data['Close'].rolling(window=period).mean().iloc[-1]
                ma_name = f'MA{period}'
                ma_levels[ma_name] = ma
                
                # 判断当前价格与均线的关系
                if ma <= current_price:
                    self.support_levels.append((ma, ma_name))
                else:
                    self.resistance_levels.append((ma, ma_name))
        
        return ma_levels
    
    def find_recent_swing_points(self, window: int = 60, lookaround: int = 5) -> Dict[str, List]:
        """
        寻找最近的高点和低点（摇摆点）
        
        参数:
            window: 分析窗口大小
            lookaround: 判断局部极值的前后看几个点
            
        返回:
            Dict: 包含高点和低点的字典
        """
        # 获取最近窗口期内的数据
        recent_data = self.price_data.tail(window)
        
        highs = []
        lows = []
        
        # 找出局部高点和低点
        for i in range(lookaround, len(recent_data) - lookaround):
            # 获取当前位置的高低价
            current_high = recent_data['High'].iloc[i]
            current_low = recent_data['Low'].iloc[i]
            
            # 检查是否是局部高点
            if all(current_high >= recent_data['High'].iloc[i-lookaround:i]) and \
               all(current_high >= recent_data['High'].iloc[i+1:i+lookaround+1]):
                highs.append((recent_data.index[i], current_high))
            
            # 检查是否是局部低点
            if all(current_low <= recent_data['Low'].iloc[i-lookaround:i]) and \
               all(current_low <= recent_data['Low'].iloc[i+1:i+lookaround+1]):
                lows.append((recent_data.index[i], current_low))
        
        # 排序并保留最显著的几个点
        highs.sort(key=lambda x: x[1], reverse=True)
        lows.sort(key=lambda x: x[1])
        
        # 提取价格值
        high_prices = [price for _, price in highs[:3]]  # 取最高的3个点
        low_prices = [price for _, price in lows[:3]]    # 取最低的3个点
        
        for price in high_prices:
            self.resistance_levels.append((price, "摇摆高点"))
        
        for price in low_prices:
            self.support_levels.append((price, "摇摆低点"))
        
        return {
            'highs': high_prices,
            'lows': low_prices
        }
    
    def find_volume_clusters(self, window: int = 60, threshold_pct: float = 70) -> List[Dict]:
        """
        寻找成交量聚集区
        
        参数:
            window: 分析窗口大小
            threshold_pct: 成交量百分比阈值
            
        返回:
            List[Dict]: 成交量聚集区列表
        """
        # 获取最近窗口期内的数据
        recent_data = self.price_data.tail(window)
        
        # 创建价格区间
        bins = 20
        min_price = recent_data['Low'].min()
        max_price = recent_data['High'].max()
        price_range = max_price - min_price
        
        # 如果价格范围太小，增加分辨率
        if price_range < 0.05 * min_price:
            bin_size = 0.005 * min_price
            bins = int(price_range / bin_size) + 1
        
        bin_edges = np.linspace(min_price, max_price, bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # 计算每日价格范围内的成交量分布
        daily_vol_dist = []
        
        for _, row in recent_data.iterrows():
            # 对每个交易日，计算其成交量在各价格区间的分布
            price_span = row['High'] - row['Low']
            if price_span <= 0:
                continue
                
            daily_bins = np.clip(
                np.searchsorted(bin_edges, [row['Low'], row['High']]), 
                0, 
                len(bin_edges) - 1
            )
            
            # 将当天成交量平均分配到价格区间内
            vol_per_bin = row['Volume'] / (daily_bins[1] - daily_bins[0])
            
            for bin_idx in range(daily_bins[0], daily_bins[1]):
                if bin_idx < len(bin_centers):
                    daily_vol_dist.append((bin_centers[bin_idx], vol_per_bin))
        
        # 按价格分组并汇总成交量
        price_vol = {}
        for price, vol in daily_vol_dist:
            price_bin = np.digitize(price, bin_edges) - 1
            if 0 <= price_bin < len(bin_centers):
                bin_price = bin_centers[price_bin]
                price_vol[bin_price] = price_vol.get(bin_price, 0) + vol
        
        # 计算总成交量
        total_vol = sum(price_vol.values())
        
        # 找出成交量占比高于阈值的价格区域
        vol_clusters = []
        for price, vol in price_vol.items():
            vol_pct = (vol / total_vol) * 100 if total_vol > 0 else 0
            if vol_pct >= threshold_pct / bins:  # 根据bin数量调整阈值
                vol_clusters.append({
                    'price': price,
                    'volume': vol,
                    'volume_pct': vol_pct
                })
                
                # 添加到支撑/阻力位列表
                current_price = self.price_data['Close'].iloc[-1]
                if price <= current_price:
                    self.support_levels.append((price, "成交量聚集区"))
                else:
                    self.resistance_levels.append((price, "成交量聚集区"))
        
        # 按成交量占比排序
        vol_clusters.sort(key=lambda x: x['volume_pct'], reverse=True)
        
        return vol_clusters
    
    def analyze(self) -> Dict:
        """
        执行完整的压力位分析
        
        返回:
            Dict: 包含所有分析结果的字典
        """
        # 清空之前的结果
        self.support_levels = []
        self.resistance_levels = []
        
        # 获取当前价格
        current_price = self.price_data['Close'].iloc[-1] if not self.price_data.empty else 0
        
        # 计算Fibonacci回调位
        fib_levels = self.calculate_fibonacci_levels()
        
        # 分析价格分布
        price_distribution = self.analyze_price_distribution()
        
        # 获取移动平均线支撑压力位
        ma_levels = self.get_ma_support_resistance()
        
        # 寻找摇摆点
        swing_points = self.find_recent_swing_points()
        
        # 寻找成交量聚集区
        volume_clusters = self.find_volume_clusters()
        
        # 对支撑位和阻力位进行排序，并选择最接近当前价格的几个
        self.support_levels.sort(key=lambda x: current_price - x[0] if x[0] < current_price else float('inf'))
        self.resistance_levels.sort(key=lambda x: x[0] - current_price if x[0] > current_price else float('inf'))
        
        # 过滤掉距离当前价格过远的位置（超过20%）
        self.support_levels = [(price, source) for price, source in self.support_levels 
                               if price > current_price * 0.8]
        self.resistance_levels = [(price, source) for price, source in self.resistance_levels 
                                 if price < current_price * 1.2]
        
        # 获取最近的支撑位和阻力位
        nearest_support = self.support_levels[0] if self.support_levels else (current_price * 0.95, "默认支撑")
        nearest_resistance = self.resistance_levels[0] if self.resistance_levels else (current_price * 1.05, "默认阻力")
        
        # 计算买入区间
        buy_zone = {
            'low': nearest_support[0],
            'high': min(nearest_support[0] * 1.02, current_price)  # 支撑位上方2%以内，但不超过当前价
        }
        
        # 计算止损位
        stop_loss = nearest_support[0] * 0.98  # 支撑位下方2%
        
        # 整合所有分析结果
        result = {
            'current_price': current_price,
            'support_levels': [{'price': price, 'source': source} for price, source in self.support_levels],
            'resistance_levels': [{'price': price, 'source': source} for price, source in self.resistance_levels],
            'nearest_support': {
                'price': nearest_support[0],
                'source': nearest_support[1]
            },
            'nearest_resistance': {
                'price': nearest_resistance[0],
                'source': nearest_resistance[1]
            },
            'fibonacci_levels': fib_levels,
            'price_distribution': price_distribution,
            'ma_levels': ma_levels,
            'swing_points': swing_points,
            'volume_clusters': volume_clusters,
            'buy_zone': buy_zone,
            'stop_loss': stop_loss
        }
        
        return result 