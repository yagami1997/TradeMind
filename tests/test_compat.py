"""
TradeMind Lite（轻量版）- 兼容层测试
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
import os
import warnings

# 导入兼容层
from trademind.compat import StockAnalyzer, TechnicalPattern


class TestCompat(unittest.TestCase):
    """测试兼容层"""
    
    def setUp(self):
        """设置测试环境"""
        # 忽略废弃警告，以便测试可以正常进行
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        
        # 模拟股票数据
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        self.mock_data = pd.DataFrame({
            'Open': np.random.normal(100, 5, len(dates)),
            'High': np.random.normal(105, 5, len(dates)),
            'Low': np.random.normal(95, 5, len(dates)),
            'Close': np.random.normal(100, 5, len(dates)),
            'Volume': np.random.normal(1000000, 200000, len(dates))
        }, index=dates)
        
        # 确保High总是大于等于Open和Close
        self.mock_data['High'] = self.mock_data[['Open', 'Close', 'High']].max(axis=1)
        
        # 确保Low总是小于等于Open和Close
        self.mock_data['Low'] = self.mock_data[['Open', 'Close', 'Low']].min(axis=1)
        
        # 创建分析器实例
        self.analyzer = StockAnalyzer()
        
        # 修改结果路径为临时目录
        self.analyzer.results_path = Path(self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_technical_pattern_class(self):
        """测试TechnicalPattern类兼容性"""
        # 创建一个TechnicalPattern实例
        pattern = TechnicalPattern(name="看涨吞没", confidence=80.0, description="看涨吞没形态")
        
        # 验证属性
        self.assertEqual(pattern.name, "看涨吞没")
        self.assertEqual(pattern.confidence, 80.0)
        self.assertEqual(pattern.description, "看涨吞没形态")
    
    @patch('trademind.core.patterns.identify_candlestick_patterns')
    def test_identify_candlestick_patterns(self, mock_identify):
        """测试identify_candlestick_patterns方法兼容性"""
        # 模拟返回值
        mock_patterns = [
            TechnicalPattern(name="看涨吞没", confidence=80.0, description="看涨吞没形态")
        ]
        mock_identify.return_value = mock_patterns
        
        # 调用兼容层方法
        patterns = self.analyzer.identify_candlestick_patterns(self.mock_data)
        
        # 验证结果
        self.assertEqual(patterns, mock_patterns)
        mock_identify.assert_called_once_with(self.mock_data)
    
    @patch('trademind.core.indicators.calculate_rsi')
    def test_calculate_rsi(self, mock_calculate_rsi):
        """测试calculate_rsi方法兼容性"""
        # 模拟返回值
        mock_calculate_rsi.return_value = 65.5
        
        # 调用兼容层方法
        rsi = self.analyzer.calculate_rsi(self.mock_data['Close'])
        
        # 验证结果
        self.assertEqual(rsi, 65.5)
        mock_calculate_rsi.assert_called_once_with(self.mock_data['Close'], 14)
    
    @patch('trademind.core.indicators.calculate_macd')
    def test_calculate_macd(self, mock_calculate_macd):
        """测试calculate_macd方法兼容性"""
        # 模拟返回值
        mock_calculate_macd.return_value = (0.5, 0.3, 0.2)
        
        # 调用兼容层方法
        macd, signal, hist = self.analyzer.calculate_macd(self.mock_data['Close'])
        
        # 验证结果
        self.assertEqual(macd, 0.5)
        self.assertEqual(signal, 0.3)
        self.assertEqual(hist, 0.2)
        mock_calculate_macd.assert_called_once_with(self.mock_data['Close'], 12, 26, 9)
    
    @patch('trademind.core.indicators.calculate_kdj')
    def test_calculate_kdj(self, mock_calculate_kdj):
        """测试calculate_kdj方法兼容性"""
        # 模拟返回值
        mock_calculate_kdj.return_value = (70.0, 60.0, 80.0)
        
        # 调用兼容层方法
        k, d, j = self.analyzer.calculate_kdj(
            self.mock_data['High'], 
            self.mock_data['Low'], 
            self.mock_data['Close']
        )
        
        # 验证结果
        self.assertEqual(k, 70.0)
        self.assertEqual(d, 60.0)
        self.assertEqual(j, 80.0)
        mock_calculate_kdj.assert_called_once_with(
            self.mock_data['High'], 
            self.mock_data['Low'], 
            self.mock_data['Close'],
            9, 3, 3
        )
    
    @patch('trademind.core.indicators.calculate_bollinger_bands')
    def test_calculate_bollinger_bands(self, mock_calculate_bb):
        """测试calculate_bollinger_bands方法兼容性"""
        # 模拟返回值
        mock_calculate_bb.return_value = (110.0, 100.0, 90.0, 0.2, 0.5)
        
        # 调用兼容层方法
        upper, middle, lower, width, percent = self.analyzer.calculate_bollinger_bands(
            self.mock_data['Close']
        )
        
        # 验证结果
        self.assertEqual(upper, 110.0)
        self.assertEqual(middle, 100.0)
        self.assertEqual(lower, 90.0)
        self.assertEqual(width, 0.2)
        self.assertEqual(percent, 0.5)
        mock_calculate_bb.assert_called_once_with(self.mock_data['Close'], 20, 2.0)
    
    @patch('trademind.core.signals.generate_trading_advice')
    def test_generate_trading_advice(self, mock_generate_advice):
        """测试generate_trading_advice方法兼容性"""
        # 模拟返回值
        mock_advice = {
            'advice': '买入',
            'confidence': 75.0,
            'signals': ['MACD金叉', 'RSI超卖'],
            'color': 'buy'
        }
        mock_generate_advice.return_value = mock_advice
        
        # 模拟输入
        indicators = {
            'rsi': 30.0,
            'macd': {'macd': 0.5, 'signal': 0.3, 'hist': 0.2}
        }
        patterns = [
            TechnicalPattern(name="看涨吞没", confidence=80.0, description="看涨吞没形态")
        ]
        
        # 调用兼容层方法
        advice = self.analyzer.generate_trading_advice(indicators, 100.0, patterns)
        
        # 验证结果
        self.assertEqual(advice, mock_advice)
        mock_generate_advice.assert_called_once_with(indicators, 100.0, patterns)
    
    @patch('trademind.core.signals.generate_signals')
    def test_generate_signals(self, mock_generate_signals):
        """测试generate_signals方法兼容性"""
        # 模拟返回值
        mock_signals = pd.DataFrame({
            'signal': [0, 0, 1, 0, -1],
            'position': [0, 0, 1, 1, 0]
        })
        mock_generate_signals.return_value = mock_signals
        
        # 模拟输入
        indicators = {
            'rsi': 30.0,
            'macd': {'macd': 0.5, 'signal': 0.3, 'hist': 0.2}
        }
        
        # 调用兼容层方法
        signals = self.analyzer.generate_signals(self.mock_data, indicators)
        
        # 验证结果
        pd.testing.assert_frame_equal(signals, mock_signals)
        mock_generate_signals.assert_called_once_with(self.mock_data, indicators)
    
    @patch('trademind.backtest.engine.run_backtest')
    def test_backtest_strategy(self, mock_run_backtest):
        """测试backtest_strategy方法兼容性"""
        # 模拟返回值
        mock_results = {
            'total_trades': 10,
            'win_rate': 60.0,
            'avg_profit': 2.5,
            'max_profit': 8.0,
            'max_loss': -3.0,
            'profit_factor': 2.0,
            'max_drawdown': 12.0
        }
        mock_run_backtest.return_value = mock_results
        
        # 模拟输入
        signals = pd.DataFrame({
            'signal': [0, 0, 1, 0, -1],
            'position': [0, 0, 1, 1, 0]
        })
        
        # 调用兼容层方法
        results = self.analyzer.backtest_strategy(
            self.mock_data, 
            signals,
            initial_capital=10000.0,
            risk_per_trade_pct=0.02,
            stop_loss_pct=0.07,
            take_profit_pct=0.15,
            max_hold_days=20
        )
        
        # 验证结果
        self.assertEqual(results, mock_results)
        mock_run_backtest.assert_called_once_with(
            self.mock_data, 
            signals,
            10000.0,
            0.02,
            0.07,
            0.15,
            20
        )
    
    @patch('yfinance.Ticker')
    @patch('trademind.core.analyzer.StockAnalyzer.analyze_stocks')
    def test_analyze_stocks(self, mock_analyze_stocks, mock_ticker):
        """测试analyze_stocks方法兼容性"""
        # 模拟返回值
        mock_results = [
            {
                'symbol': 'AAPL',
                'name': '苹果公司',
                'price': 150.0,
                'change': 2.5,
                'indicators': {'rsi': 65.0},
                'patterns': [],
                'advice': {'advice': '买入', 'confidence': 75.0},
                'backtest': {'total_trades': 10, 'win_rate': 60.0}
            }
        ]
        mock_analyze_stocks.return_value = mock_results
        
        # 调用兼容层方法
        symbols = ['AAPL']
        names = {'AAPL': '苹果公司'}
        results = self.analyzer.analyze_stocks(symbols, names)
        
        # 验证结果
        self.assertEqual(results, mock_results)
        mock_analyze_stocks.assert_called_once_with(symbols, names)
    
    @patch('trademind.core.analyzer.StockAnalyzer.generate_report')
    def test_generate_report(self, mock_generate_report):
        """测试generate_report方法兼容性"""
        # 模拟返回值
        mock_report_path = os.path.join(self.temp_dir, 'test_report.html')
        mock_generate_report.return_value = mock_report_path
        
        # 模拟输入
        results = [
            {
                'symbol': 'AAPL',
                'name': '苹果公司',
                'price': 150.0,
                'change': 2.5,
                'indicators': {'rsi': 65.0},
                'patterns': [],
                'advice': {'advice': '买入', 'confidence': 75.0},
                'backtest': {'total_trades': 10, 'win_rate': 60.0}
            }
        ]
        
        # 调用兼容层方法
        report_path = self.analyzer.generate_report(results, "测试报告")
        
        # 验证结果
        self.assertEqual(report_path, mock_report_path)
        mock_generate_report.assert_called_once_with(results, "测试报告")
    
    @patch('trademind.core.analyzer.StockAnalyzer.analyze_and_report')
    def test_analyze_and_report(self, mock_analyze_and_report):
        """测试analyze_and_report方法兼容性"""
        # 模拟返回值
        mock_report_path = os.path.join(self.temp_dir, 'test_report.html')
        mock_analyze_and_report.return_value = mock_report_path
        
        # 调用兼容层方法
        symbols = ['AAPL']
        names = {'AAPL': '苹果公司'}
        report_path = self.analyzer.analyze_and_report(symbols, names, "测试报告")
        
        # 验证结果
        self.assertEqual(report_path, mock_report_path)
        mock_analyze_and_report.assert_called_once_with(symbols, names, "测试报告")
    
    @patch('trademind.core.analyzer.StockAnalyzer.clean_reports')
    def test_clean_reports(self, mock_clean_reports):
        """测试clean_reports方法兼容性"""
        # 调用兼容层方法
        self.analyzer.clean_reports(days_threshold=30)
        
        # 验证结果
        mock_clean_reports.assert_called_once_with(30)


if __name__ == '__main__':
    unittest.main() 