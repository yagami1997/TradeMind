"""
TradeMind Lite（轻量版）- 兼容层模块

本模块提供与旧版StockAnalyzer兼容的接口，确保现有代码可以无缝迁移到新的模块化结构。
"""

import os
import warnings
import logging
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# 导入新版模块
from trademind.core.analyzer import StockAnalyzer as NewStockAnalyzer

if TYPE_CHECKING:
    from trademind.core.patterns import TechnicalPattern
else:
    from trademind.core.patterns import TechnicalPattern as _TechnicalPattern
    TechnicalPattern = _TechnicalPattern

# 废弃警告消息
DEPRECATION_WARNING = """
警告: 您正在使用TradeMind Lite的兼容层接口，该接口将在未来版本中移除。
请迁移到新的模块化接口:
    from trademind.core.analyzer import StockAnalyzer
详细迁移指南请参考文档: https://trademind-lite.docs/migration-guide
"""

# 创建全局分析器实例，用于单个股票分析函数
_global_analyzer = NewStockAnalyzer()

def analyze_stock(symbol: str, name: str = None) -> Dict:
    """
    分析单只股票（兼容函数）
    
    Args:
        symbol: 股票代码
        name: 股票名称，如果为None则使用股票代码作为名称
    
    Returns:
        包含分析结果的字典
    """
    warnings.warn("analyze_stock 函数已废弃，请使用 trademind.core.analyzer.StockAnalyzer.analyze_stocks", 
                 DeprecationWarning, stacklevel=2)
    
    # 如果名称为None，使用股票代码作为名称
    if name is None:
        name = symbol
    
    # 使用全局分析器实例分析股票
    results = _global_analyzer.analyze_stocks([symbol], {symbol: name})
    
    # 返回第一个结果（因为只分析了一只股票）
    if results and len(results) > 0:
        result = results[0]
        
        # 确保回测结果中包含所有必要的键
        if 'backtest' in result:
            backtest = result['backtest']
            # 确保trades键存在
            if 'trades' not in backtest:
                backtest['trades'] = []
            # 确保其他必要的键存在
            if 'total_trades' not in backtest:
                backtest['total_trades'] = 0
            if 'win_rate' not in backtest:
                backtest['win_rate'] = 0.0
            if 'avg_profit' not in backtest:
                backtest['avg_profit'] = 0.0
            if 'max_drawdown' not in backtest:
                backtest['max_drawdown'] = 0.0
            if 'performance' not in backtest:
                backtest['performance'] = {'total_return': 0.0}
            elif 'total_return' not in backtest['performance']:
                backtest['performance']['total_return'] = 0.0
            
        return result
    else:
        return {}


class StockAnalyzer:
    """
    旧版StockAnalyzer兼容类
    
    该类提供与旧版StockAnalyzer相同的接口，但内部实现改为调用新模块的功能。
    所有方法都会发出废弃警告，提示用户迁移到新接口。
    """
    
    def __init__(self):
        """初始化兼容层StockAnalyzer"""
        # 发出废弃警告
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        
        # 创建新版StockAnalyzer实例
        self._analyzer = NewStockAnalyzer()
        
        # 从新版实例获取属性
        self.logger = self._analyzer.logger
        self.results_path = self._analyzer.results_path
        self.colors = self._analyzer.colors
    
    def setup_logging(self):
        """设置日志记录（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.setup_logging 已废弃", 
                     DeprecationWarning, stacklevel=2)
        # 新版StockAnalyzer在初始化时已经设置了日志
        pass
    
    def setup_paths(self):
        """设置路径（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.setup_paths 已废弃", 
                     DeprecationWarning, stacklevel=2)
        # 新版StockAnalyzer在初始化时已经设置了路径
        pass
    
    def setup_colors(self):
        """设置颜色方案（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.setup_colors 已废弃", 
                     DeprecationWarning, stacklevel=2)
        # 新版StockAnalyzer在初始化时已经设置了颜色方案
        pass
    
    def identify_candlestick_patterns(self, data: pd.DataFrame) -> List[TechnicalPattern]:
        """识别K线形态（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.identify_candlestick_patterns 已废弃，请使用 trademind.core.patterns.identify_candlestick_patterns", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.patterns import identify_candlestick_patterns
        return identify_candlestick_patterns(data)
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI指标（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.calculate_rsi 已废弃，请使用 trademind.core.indicators.calculate_rsi", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.indicators import calculate_rsi
        return calculate_rsi(prices, period)
    
    def calculate_macd(self, prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[float, float, float]:
        """计算MACD指标（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.calculate_macd 已废弃，请使用 trademind.core.indicators.calculate_macd", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.indicators import calculate_macd
        return calculate_macd(prices, fast_period, slow_period, signal_period)
    
    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[float, float, float]:
        """计算KDJ指标（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.calculate_kdj 已废弃，请使用 trademind.core.indicators.calculate_kdj", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.indicators import calculate_kdj
        return calculate_kdj(high, low, close, n, m1, m2)
    
    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[float, float, float, float, float]:
        """计算布林带指标（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.calculate_bollinger_bands 已废弃，请使用 trademind.core.indicators.calculate_bollinger_bands", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.indicators import calculate_bollinger_bands
        return calculate_bollinger_bands(prices, window, num_std)
    
    def generate_trading_advice(self, indicators: Dict, current_price: float, patterns: Optional[List[TechnicalPattern]] = None) -> Dict:
        """生成交易建议（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.generate_trading_advice 已废弃，请使用 trademind.core.signals.generate_trading_advice", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.signals import generate_trading_advice
        return generate_trading_advice(indicators, current_price, patterns)
    
    def generate_signals(self, data: pd.DataFrame, indicators: Dict) -> pd.DataFrame:
        """生成交易信号（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.generate_signals 已废弃，请使用 trademind.core.signals.generate_signals", 
                     DeprecationWarning, stacklevel=2)
        from trademind.core.signals import generate_signals
        return generate_signals(data, indicators)
    
    def backtest_strategy(self, data: pd.DataFrame, signals: pd.DataFrame, initial_capital: float = 10000.0,
                         risk_per_trade_pct: float = 0.02, stop_loss_pct: float = 0.07,
                         take_profit_pct: float = 0.15, max_hold_days: int = 20) -> Dict:
        """回测策略（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.backtest_strategy 已废弃，请使用 trademind.backtest.engine.run_backtest", 
                     DeprecationWarning, stacklevel=2)
        from trademind.backtest.engine import run_backtest
        return run_backtest(data, signals, initial_capital, risk_per_trade_pct, 
                           stop_loss_pct, take_profit_pct, max_hold_days)
    
    def analyze_stocks(self, symbols: List[str], names: Dict[str, str] = None) -> List[Dict]:
        """分析多只股票（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.analyze_stocks 已废弃，请使用 trademind.core.analyzer.StockAnalyzer.analyze_stocks", 
                     DeprecationWarning, stacklevel=2)
        return self._analyzer.analyze_stocks(symbols, names)
    
    def generate_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        """生成HTML分析报告（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.generate_report 已废弃，请使用 trademind.core.analyzer.StockAnalyzer.generate_report", 
                     DeprecationWarning, stacklevel=2)
        return self._analyzer.generate_report(results, title)
    
    def analyze_and_report(self, symbols: List[str], names: Dict[str, str] = None, title: str = "股票分析报告") -> str:
        """分析股票并生成报告（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.analyze_and_report 已废弃，请使用 trademind.core.analyzer.StockAnalyzer.analyze_and_report", 
                     DeprecationWarning, stacklevel=2)
        return self._analyzer.analyze_and_report(symbols, names, title)
    
    def clean_reports(self, days_threshold: int = 30):
        """清理旧的报告文件（兼容方法）"""
        warnings.warn(f"{self.__class__.__name__}.clean_reports 已废弃，请使用 trademind.core.analyzer.StockAnalyzer.clean_reports", 
                     DeprecationWarning, stacklevel=2)
        return self._analyzer.clean_reports(days_threshold)


# 在模块导入时发出废弃警告
warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2) 