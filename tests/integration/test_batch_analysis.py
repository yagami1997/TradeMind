"""
TradeMind Lite（轻量版）- 多股票批量分析集成测试

本模块包含TradeMind Lite的多股票批量分析集成测试，验证系统处理大量股票数据的能力。
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


class TestBatchAnalysis(unittest.TestCase):
    """多股票批量分析集成测试类"""
    
    def setUp(self):
        """设置测试环境"""
        # 忽略警告
        warnings.filterwarnings('ignore', category=Warning)
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试数据
        self.create_test_data()
        
        # 创建分析器实例
        self.analyzer = StockAnalyzer()
        self.analyzer.results_path = Path(self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def create_test_data(self):
        """创建大量测试数据"""
        # 创建模拟股票数据
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        self.test_data = {}
        
        # 创建股票代码列表 (50只股票)
        self.symbols = [f'STOCK{i:02d}' for i in range(1, 51)]
        self.names = {symbol: f'测试股票{i:02d}' for i, symbol in enumerate(self.symbols, 1)}
        
        # 创建多只股票的数据
        for symbol in self.symbols:
            # 生成随机价格数据
            seed = sum(ord(c) for c in symbol)  # 使用股票代码生成种子
            np.random.seed(seed)
            
            # 创建基本价格趋势
            base_price = 100 + np.random.normal(0, 10)
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
            self.test_data[symbol] = pd.DataFrame({
                'Open': open_prices,
                'High': high_prices,
                'Low': low_prices,
                'Close': close_prices,
                'Volume': volume
            }, index=dates)
    
    def test_batch_analysis(self):
        """测试批量分析多只股票"""
        # 模拟yfinance.Ticker.history方法
        with mock.patch('yfinance.Ticker') as mock_ticker:
            # 设置模拟对象的行为
            mock_ticker_instances = {}
            for symbol in self.symbols:
                mock_instance = mock.MagicMock()
                mock_instance.history.return_value = self.test_data[symbol]
                mock_ticker_instances[symbol] = mock_instance
            
            mock_ticker.side_effect = lambda s: mock_ticker_instances[s]
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行批量分析
            results = self.analyzer.analyze_stocks(self.symbols, self.names)
            
            # 记录结束时间
            end_time = time.time()
            duration = end_time - start_time
            
            # 验证结果
            self.assertEqual(len(results), len(self.symbols))
            
            # 计算平均处理时间
            avg_time_per_stock = duration / len(self.symbols)
            
            # 输出性能指标
            print(f"\n批量分析性能:")
            print(f"总股票数: {len(self.symbols)}")
            print(f"总处理时间: {duration:.2f}秒")
            print(f"平均每只股票处理时间: {avg_time_per_stock:.3f}秒")
            
            # 验证所有结果都包含必要的字段
            for result in results:
                self.assertIn('symbol', result)
                self.assertIn('name', result)
                self.assertIn('price', result)
                self.assertIn('change', result)
                self.assertIn('indicators', result)
                self.assertIn('patterns', result)
                self.assertIn('advice', result)
                self.assertIn('backtest', result)
                
                # 验证指标数据
                indicators = result['indicators']
                self.assertIn('rsi', indicators)
                self.assertIn('macd', indicators)
                self.assertIn('kdj', indicators)
                self.assertIn('bollinger', indicators)
                
                # 验证交易建议
                advice = result['advice']
                self.assertIn('advice', advice)
                self.assertIn('confidence', advice)
                self.assertIn('signals', advice)
                
                # 验证回测结果
                backtest = result['backtest']
                self.assertIn('total_trades', backtest)
                self.assertIn('win_rate', backtest)
    
    def test_batch_report_generation(self):
        """测试批量生成报告"""
        # 模拟yfinance.Ticker.history方法
        with mock.patch('yfinance.Ticker') as mock_ticker:
            # 设置模拟对象的行为
            mock_ticker_instances = {}
            for symbol in self.symbols[:10]:  # 使用前10只股票
                mock_instance = mock.MagicMock()
                mock_instance.history.return_value = self.test_data[symbol]
                mock_ticker_instances[symbol] = mock_instance
            
            mock_ticker.side_effect = lambda s: mock_ticker_instances[s]
            
            # 执行批量分析
            results = self.analyzer.analyze_stocks(self.symbols[:10], {s: self.names[s] for s in self.symbols[:10]})
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成报告
            report_path = self.analyzer.generate_report(results, "批量分析测试报告")
            
            # 记录结束时间
            end_time = time.time()
            duration = end_time - start_time
            
            # 验证报告生成
            self.assertTrue(os.path.exists(report_path))
            self.assertTrue(os.path.getsize(report_path) > 0)
            
            # 输出性能指标
            print(f"\n报告生成性能:")
            print(f"股票数: {len(results)}")
            print(f"报告生成时间: {duration:.2f}秒")
            print(f"报告文件大小: {os.path.getsize(report_path)/1024:.1f} KB")
    
    def test_parallel_processing_simulation(self):
        """模拟并行处理测试"""
        # 这个测试只是模拟并行处理的潜力，不实际实现并行
        
        # 模拟yfinance.Ticker.history方法
        with mock.patch('yfinance.Ticker') as mock_ticker:
            # 设置模拟对象的行为
            mock_ticker_instances = {}
            for symbol in self.symbols:
                mock_instance = mock.MagicMock()
                mock_instance.history.return_value = self.test_data[symbol]
                mock_ticker_instances[symbol] = mock_instance
            
            mock_ticker.side_effect = lambda s: mock_ticker_instances[s]
            
            # 记录串行处理时间
            start_time = time.time()
            
            # 执行批量分析 (串行)
            results = self.analyzer.analyze_stocks(self.symbols[:10], {s: self.names[s] for s in self.symbols[:10]})
            
            # 记录结束时间
            serial_duration = time.time() - start_time
            
            # 计算理论并行处理时间 (假设完美并行，无开销)
            # 在实际实现中，需要使用multiprocessing或concurrent.futures
            theoretical_parallel_duration = serial_duration / 4  # 假设4核并行
            
            # 输出性能对比
            print(f"\n并行处理潜力分析:")
            print(f"串行处理时间: {serial_duration:.2f}秒")
            print(f"理论4核并行时间: {theoretical_parallel_duration:.2f}秒")
            print(f"理论加速比: {serial_duration/theoretical_parallel_duration:.1f}x")
            
            # 这里不做断言，只是输出信息
            self.assertTrue(True, "并行处理模拟完成")


if __name__ == '__main__':
    unittest.main() 