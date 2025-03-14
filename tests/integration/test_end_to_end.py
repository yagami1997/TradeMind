"""
TradeMind Lite（轻量版）- 端到端集成测试

本模块包含TradeMind Lite的端到端集成测试，验证完整的分析流程。
"""

import unittest
from unittest import mock
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings

# 导入新版模块
from trademind.core.analyzer import StockAnalyzer
from trademind.core.indicators import calculate_rsi, calculate_macd, calculate_kdj, calculate_bollinger_bands
from trademind.core.patterns import identify_candlestick_patterns, TechnicalPattern
from trademind.core.signals import generate_trading_advice, generate_signals
from trademind.backtest.engine import run_backtest
from trademind.reports.generator import generate_html_report

# 导入兼容层
from trademind.compat import StockAnalyzer as OldStockAnalyzer


class TestEndToEnd(unittest.TestCase):
    """端到端集成测试类"""
    
    def setUp(self):
        """设置测试环境"""
        # 忽略警告
        warnings.filterwarnings('ignore', category=Warning)
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试数据
        self.create_test_data()
        
        # 创建新版分析器实例
        self.analyzer = StockAnalyzer()
        self.analyzer.results_path = Path(self.temp_dir)
        
        # 创建兼容层分析器实例
        self.old_analyzer = OldStockAnalyzer()
        self.old_analyzer.results_path = Path(self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def create_test_data(self):
        """创建测试数据"""
        # 创建模拟股票数据
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        
        # 生成随机价格数据
        np.random.seed(42)  # 固定种子以确保可重复性
        
        # 创建基本价格趋势
        base_price = 100
        trend = np.cumsum(np.random.normal(0.05, 1, len(dates)))
        
        # 添加季节性和周期性
        seasonality = 5 * np.sin(np.arange(len(dates)) * (2 * np.pi / 63))
        cycles = 3 * np.cos(np.arange(len(dates)) * (2 * np.pi / 21))
        
        # 组合所有成分
        close_prices = base_price + trend + seasonality + cycles
        
        # 确保价格为正
        close_prices = np.maximum(close_prices, 1)
        
        # 生成其他价格数据
        daily_volatility = np.random.uniform(0.01, 0.03, len(dates))
        high_prices = close_prices * (1 + daily_volatility)
        low_prices = close_prices * (1 - daily_volatility)
        open_prices = low_prices + np.random.uniform(0, 1, len(dates)) * (high_prices - low_prices)
        
        # 生成成交量数据
        volume = np.random.normal(1000000, 200000, len(dates))
        volume = np.maximum(volume, 100000)  # 确保成交量为正
        
        # 创建DataFrame
        self.test_data = pd.DataFrame({
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volume
        }, index=dates)
        
        # 设置股票信息
        self.symbol = 'AAPL'
        self.name = '苹果公司'
    
    def test_end_to_end_analysis(self):
        """测试端到端分析流程"""
        # 模拟yfinance.Ticker.history方法
        with mock.patch('yfinance.Ticker') as mock_ticker:
            # 设置模拟对象的行为
            mock_instance = mock.MagicMock()
            mock_instance.history.return_value = self.test_data
            mock_ticker.return_value = mock_instance
            
            # 执行分析
            results = self.analyzer.analyze_stocks([self.symbol], {self.symbol: self.name})
            
            # 验证结果
            self.assertEqual(len(results), 1)
            result = results[0]
            
            # 验证基本信息
            self.assertEqual(result['symbol'], self.symbol)
            self.assertEqual(result['name'], self.name)
            self.assertIsNotNone(result['price'])
            self.assertIsNotNone(result['change'])
            
            # 验证技术指标
            self.assertIn('indicators', result)
            indicators = result['indicators']
            self.assertIn('rsi', indicators)
            self.assertIn('macd', indicators)
            self.assertIn('kdj', indicators)
            self.assertIn('bollinger', indicators)
            
            # 验证K线形态
            self.assertIn('patterns', result)
            
            # 验证交易建议
            self.assertIn('advice', result)
            self.assertIn('signals', result['advice'])
            
            # 验证回测结果
            self.assertIn('backtest', result)
            backtest = result['backtest']
            self.assertIn('total_trades', backtest)
            self.assertIn('win_rate', backtest)
            self.assertIn('avg_profit', backtest)
            self.assertIn('max_drawdown', backtest)
            
            # 生成报告
            report_path = self.analyzer.generate_report(results, "端到端测试报告")
            
            # 验证报告生成
            self.assertTrue(os.path.exists(report_path))
            self.assertTrue(os.path.getsize(report_path) > 0)
    
    def test_compatibility_layer(self):
        """测试兼容层与新版接口的一致性"""
        # 模拟yfinance.Ticker.history方法
        with mock.patch('yfinance.Ticker') as mock_ticker:
            # 设置模拟对象的行为
            mock_instance = mock.MagicMock()
            mock_instance.history.return_value = self.test_data
            mock_ticker.return_value = mock_instance
            
            # 使用新版接口
            new_results = self.analyzer.analyze_stocks([self.symbol], {self.symbol: self.name})
            
            # 使用兼容层接口 (假设存在)
            try:
                from trademind.compat import analyze_stock
                compat_result = analyze_stock(self.symbol, self.name)
                
                # 验证结果一致性
                self.assertEqual(new_results[0]['symbol'], compat_result['symbol'])
                self.assertEqual(new_results[0]['name'], compat_result['name'])
                self.assertAlmostEqual(new_results[0]['price'], compat_result['price'], places=2)
                
                # 验证技术指标一致性
                new_indicators = new_results[0]['indicators']
                compat_indicators = compat_result['indicators']
                for key in new_indicators:
                    if isinstance(new_indicators[key], (int, float)):
                        self.assertAlmostEqual(new_indicators[key], compat_indicators[key], places=2)
                
                # 验证回测结果一致性
                new_backtest = new_results[0]['backtest']
                compat_backtest = compat_result['backtest']
                
                # 检查trades键是否存在，如果不存在则跳过这个断言
                if 'trades' in new_backtest and 'trades' in compat_backtest:
                    self.assertEqual(len(new_backtest['trades']), len(compat_backtest['trades']))
                
                # 检查performance键是否存在，如果不存在则跳过这个断言
                if 'performance' in new_backtest and 'performance' in compat_backtest:
                    if 'total_return' in new_backtest['performance'] and 'total_return' in compat_backtest['performance']:
                        self.assertAlmostEqual(
                            new_backtest['performance']['total_return'], 
                            compat_backtest['performance']['total_return'], 
                            places=2
                        )
            except ImportError:
                # 如果兼容层不存在，跳过测试
                self.skipTest("兼容层模块不存在")
    
    def test_performance_benchmark(self):
        """测试性能基准测试"""
        # 模拟yfinance.Ticker.history方法
        with mock.patch('yfinance.Ticker') as mock_ticker:
            # 设置模拟对象的行为
            mock_instance = mock.MagicMock()
            mock_instance.history.return_value = self.test_data
            mock_ticker.return_value = mock_instance
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行分析
            results = self.analyzer.analyze_stocks([self.symbol], {self.symbol: self.name})
            
            # 记录分析完成时间
            analysis_time = time.time()
            
            # 生成报告
            report_path = self.analyzer.generate_report(results, "性能测试报告")
            
            # 记录结束时间
            end_time = time.time()
            
            # 计算各阶段耗时
            analysis_duration = analysis_time - start_time
            report_duration = end_time - analysis_time
            total_duration = end_time - start_time
            
            # 输出性能指标
            print(f"\n性能基准测试:")
            print(f"分析阶段耗时: {analysis_duration:.4f}秒")
            print(f"报告生成耗时: {report_duration:.4f}秒")
            print(f"总耗时: {total_duration:.4f}秒")
            
            # 验证性能在可接受范围内 (这里只是示例，实际阈值需要根据实际情况调整)
            self.assertLess(total_duration, 10.0, "总处理时间超过阈值")


if __name__ == '__main__':
    unittest.main() 