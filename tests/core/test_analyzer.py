"""
TradeMind Lite（轻量版）- 分析器模块测试
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
import os

from trademind.core.analyzer import StockAnalyzer


class TestStockAnalyzer(unittest.TestCase):
    """测试StockAnalyzer类"""
    
    def setUp(self):
        """设置测试环境"""
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
    
    @patch('yfinance.Ticker')
    @patch('trademind.core.analyzer.generate_signals')
    @patch('trademind.core.analyzer.run_backtest')
    def test_analyze_stocks(self, mock_run_backtest, mock_generate_signals, mock_ticker):
        """测试股票分析功能"""
        # 模拟yfinance.Ticker返回的对象
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = self.mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        # 模拟generate_signals返回的信号
        mock_signals = pd.DataFrame({
            'signal': [0] * len(self.mock_data),
            'position': [0] * len(self.mock_data)
        }, index=self.mock_data.index)
        mock_generate_signals.return_value = mock_signals
        
        # 模拟run_backtest返回的结果
        mock_backtest_results = {
            'total_trades': 10,
            'win_rate': 60.0,
            'avg_profit': 2.5,
            'max_profit': 8.0,
            'max_loss': -3.0,
            'profit_factor': 2.0,
            'max_drawdown': 12.0,
            'consecutive_losses': 2,
            'avg_hold_days': 5.0,
            'final_return': 25.0,
            'sharpe_ratio': 1.5,
            'sortino_ratio': 2.0,
            'net_profit': 2500.0,
            'annualized_return': 15.0
        }
        mock_run_backtest.return_value = mock_backtest_results
        
        # 测试分析单只股票
        symbols = ['AAPL']
        names = {'AAPL': '苹果公司'}
        
        results = self.analyzer.analyze_stocks(symbols, names)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['symbol'], 'AAPL')
        self.assertEqual(results[0]['name'], '苹果公司')
        
        # 验证结果包含所有必要的字段
        self.assertIn('price', results[0])
        self.assertIn('change', results[0])
        self.assertIn('indicators', results[0])
        self.assertIn('patterns', results[0])
        self.assertIn('advice', results[0])
        self.assertIn('backtest', results[0])
        
        # 验证指标数据
        indicators = results[0]['indicators']
        self.assertIn('rsi', indicators)
        self.assertIn('macd', indicators)
        self.assertIn('kdj', indicators)
        self.assertIn('bollinger', indicators)
        
        # 验证回测结果与模拟结果相同
        self.assertEqual(results[0]['backtest'], mock_backtest_results)
        
        # 验证generate_signals被调用
        self.assertTrue(mock_generate_signals.called)
        
        # 验证run_backtest被调用
        self.assertTrue(mock_run_backtest.called)
    
    @patch('yfinance.Ticker')
    def test_analyze_stocks_empty_data(self, mock_ticker):
        """测试分析空数据的情况"""
        # 模拟yfinance.Ticker返回空数据
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        # 测试分析单只股票
        symbols = ['INVALID']
        
        results = self.analyzer.analyze_stocks(symbols)
        
        # 验证结果为空列表
        self.assertEqual(len(results), 0)
    
    @patch('yfinance.Ticker')
    @patch('trademind.core.analyzer.generate_signals')
    @patch('trademind.core.analyzer.run_backtest')
    @patch('trademind.core.analyzer.generate_html_report')
    def test_analyze_and_report(self, mock_generate_html_report, mock_run_backtest, mock_generate_signals, mock_ticker):
        """测试分析并生成报告功能"""
        # 模拟yfinance.Ticker返回的对象
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = self.mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        # 模拟generate_signals返回的信号
        mock_signals = pd.DataFrame({
            'signal': [0] * len(self.mock_data),
            'position': [0] * len(self.mock_data)
        }, index=self.mock_data.index)
        mock_generate_signals.return_value = mock_signals
        
        # 模拟run_backtest返回的结果
        mock_backtest_results = {
            'total_trades': 10,
            'win_rate': 60.0,
            'avg_profit': 2.5,
            'max_profit': 8.0,
            'max_loss': -3.0,
            'profit_factor': 2.0,
            'max_drawdown': 12.0,
            'consecutive_losses': 2,
            'avg_hold_days': 5.0,
            'final_return': 25.0,
            'sharpe_ratio': 1.5,
            'sortino_ratio': 2.0,
            'net_profit': 2500.0,
            'annualized_return': 15.0
        }
        mock_run_backtest.return_value = mock_backtest_results
        
        # 模拟generate_html_report返回报告路径
        mock_report_path = os.path.join(self.temp_dir, 'test_report.html')
        mock_generate_html_report.return_value = mock_report_path
        
        # 测试分析并生成报告
        symbols = ['AAPL']
        names = {'AAPL': '苹果公司'}
        
        report_path = self.analyzer.analyze_and_report(symbols, names, "测试报告")
        
        # 验证结果
        self.assertEqual(report_path, mock_report_path)
        
        # 验证generate_signals被调用
        self.assertTrue(mock_generate_signals.called)
        
        # 验证run_backtest被调用
        self.assertTrue(mock_run_backtest.called)
        
        # 验证generate_html_report被调用
        self.assertTrue(mock_generate_html_report.called)
    
    def test_clean_reports(self):
        """测试清理报告功能"""
        # 创建一些测试报告文件
        now = datetime.now()
        
        # 创建一个新的报告文件
        new_report = os.path.join(self.temp_dir, 'new_report.html')
        with open(new_report, 'w') as f:
            f.write('<html><body>New Report</body></html>')
        
        # 修改文件的修改时间为当前时间
        os.utime(new_report, (now.timestamp(), now.timestamp()))
        
        # 创建一个旧的报告文件
        old_report = os.path.join(self.temp_dir, 'old_report.html')
        with open(old_report, 'w') as f:
            f.write('<html><body>Old Report</body></html>')
        
        # 修改文件的修改时间为31天前
        old_time = now - timedelta(days=31)
        os.utime(old_report, (old_time.timestamp(), old_time.timestamp()))
        
        # 测试清理报告
        self.analyzer.clean_reports(days_threshold=30)
        
        # 验证结果
        self.assertTrue(os.path.exists(new_report))
        self.assertFalse(os.path.exists(old_report))


if __name__ == '__main__':
    unittest.main() 