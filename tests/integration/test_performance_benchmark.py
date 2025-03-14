"""
TradeMind Lite（轻量版）- 性能基准测试

本模块包含TradeMind Lite的性能基准测试，用于测量系统在不同条件下的性能表现。
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
import json
import matplotlib.pyplot as plt
from functools import wraps
import gc

# 导入新版模块
from trademind.core.analyzer import StockAnalyzer
from trademind.core.indicators import calculate_rsi, calculate_macd, calculate_kdj, calculate_bollinger_bands
from trademind.core.patterns import identify_candlestick_patterns
from trademind.core.signals import generate_signals
from trademind.backtest.engine import run_backtest

# 设置matplotlib使用系统默认字体
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 定义辅助函数，用于计算所有指标
def calculate_indicators(data):
    """计算所有技术指标"""
    indicators = {}
    
    # 计算RSI
    indicators['rsi'] = calculate_rsi(data['Close'])
    
    # 计算MACD
    macd_line, signal_line, histogram = calculate_macd(data['Close'])
    indicators['macd'] = {
        'macd': macd_line,
        'signal': signal_line,
        'hist': histogram
    }
    
    # 计算KDJ
    k, d, j = calculate_kdj(data['High'], data['Low'], data['Close'])
    indicators['kdj'] = {
        'k': k,
        'd': d,
        'j': j
    }
    
    # 计算布林带
    upper, middle, lower, bandwidth, percent_b = calculate_bollinger_bands(data['Close'])
    indicators['bollinger'] = {
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'bandwidth': bandwidth,
        'percent_b': percent_b
    }
    
    return indicators

def benchmark(func):
    """性能基准测试装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 强制垃圾回收
        gc.collect()
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        # 打印性能信息
        print(f"{func.__name__} 执行时间: {duration:.4f}秒")
        
        # 返回结果和执行时间
        return result, duration
    
    return wrapper


class TestPerformanceBenchmark(unittest.TestCase):
    """性能基准测试类"""
    
    def setUp(self):
        """设置测试环境"""
        # 忽略警告
        warnings.filterwarnings('ignore', category=Warning)
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        warnings.filterwarnings('ignore', category=UserWarning)  # 忽略matplotlib的字体警告
        
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 创建测试数据
        self.create_test_data()
        
        # 创建分析器实例
        self.analyzer = StockAnalyzer()
        self.analyzer.results_path = Path(self.temp_dir)
        
        # 性能结果存储
        self.performance_results = {
            "data_size": [],
            "indicator_time": [],
            "pattern_time": [],
            "signal_time": [],
            "backtest_time": [],
            "report_time": [],
            "total_time": []
        }
    
    def tearDown(self):
        """清理测试环境"""
        # 保存性能结果
        if hasattr(self, 'performance_results') and self.performance_results["data_size"]:
            self.save_performance_results()
        
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def create_test_data(self):
        """创建测试数据集，包含不同大小的数据"""
        # 创建不同时间跨度的数据
        self.test_datasets = {}
        
        # 定义不同的数据大小
        self.data_sizes = [
            ("1年", 252),
            ("2年", 504),
            ("5年", 1260),
            ("10年", 2520)
        ]
        
        # 为每个数据大小创建测试数据
        for size_name, periods in self.data_sizes:
            # 创建日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=periods)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            dates = dates[dates.dayofweek < 5]  # 只保留工作日
            dates = dates[-periods:]  # 确保长度一致
            
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
            self.test_datasets[size_name] = pd.DataFrame({
                'Open': open_prices,
                'High': high_prices,
                'Low': low_prices,
                'Close': close_prices,
                'Volume': volume
            }, index=dates)
    
    @benchmark
    def run_indicator_calculation(self, data):
        """运行技术指标计算"""
        return calculate_indicators(data)
    
    @benchmark
    def run_pattern_identification(self, data):
        """运行K线形态识别"""
        return identify_candlestick_patterns(data)
    
    @benchmark
    def run_signal_generation(self, data, indicators):
        """运行交易信号生成"""
        return generate_signals(data, indicators)
    
    @benchmark
    def run_backtest_execution(self, data, signals):
        """运行回测执行"""
        return run_backtest(data, signals)
    
    @benchmark
    def run_report_generation(self, results):
        """运行报告生成"""
        return self.analyzer.generate_report([results], "性能测试报告")
    
    def test_performance_scaling(self):
        """测试性能随数据大小的变化"""
        print("\n性能随数据大小的变化测试:")
        
        for size_name, _ in self.data_sizes:
            print(f"\n测试数据大小: {size_name}")
            data = self.test_datasets[size_name]
            
            # 运行各个组件并记录时间
            indicators, indicator_time = self.run_indicator_calculation(data)
            patterns, pattern_time = self.run_pattern_identification(data)
            signals, signal_time = self.run_signal_generation(data, indicators)
            backtest_results, backtest_time = self.run_backtest_execution(data, signals)
            
            # 创建结果对象
            result = {
                'symbol': 'TEST',
                'name': f'测试数据 ({size_name})',
                'price': data['Close'].iloc[-1],
                'change': (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100,
                'indicators': indicators,
                'patterns': patterns,
                'signals': signals,
                'backtest': backtest_results,
                'data': data,
                'advice': {
                    'advice': '观望',
                    'confidence': 50,
                    'signals': ['测试信号'],
                    'color': 'neutral'
                }
            }
            
            # 生成报告
            _, report_time = self.run_report_generation(result)
            
            # 计算总时间
            total_time = indicator_time + pattern_time + signal_time + backtest_time + report_time
            
            # 记录性能结果
            self.performance_results["data_size"].append(size_name)
            self.performance_results["indicator_time"].append(indicator_time)
            self.performance_results["pattern_time"].append(pattern_time)
            self.performance_results["signal_time"].append(signal_time)
            self.performance_results["backtest_time"].append(backtest_time)
            self.performance_results["report_time"].append(report_time)
            self.performance_results["total_time"].append(total_time)
            
            # 输出性能摘要
            print(f"总处理时间: {total_time:.4f}秒")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        import os
        
        print("\n内存使用测试:")
        
        process = psutil.Process(os.getpid())
        
        # 测试不同数据大小的内存使用
        for size_name, _ in self.data_sizes:
            print(f"\n测试数据大小: {size_name}")
            data = self.test_datasets[size_name]
            
            # 记录初始内存使用
            initial_memory = process.memory_info().rss / 1024 / 1024
            print(f"初始内存使用: {initial_memory:.2f} MB")
            
            # 运行完整分析流程
            indicators = calculate_indicators(data)
            patterns = identify_candlestick_patterns(data)
            signals = generate_signals(data, indicators)
            backtest_results = run_backtest(data, signals)
            
            # 记录分析后内存使用
            analysis_memory = process.memory_info().rss / 1024 / 1024
            print(f"分析后内存使用: {analysis_memory:.2f} MB")
            print(f"内存增加: {analysis_memory - initial_memory:.2f} MB")
            
            # 强制垃圾回收
            gc.collect()
            
            # 记录垃圾回收后内存使用
            gc_memory = process.memory_info().rss / 1024 / 1024
            print(f"垃圾回收后内存使用: {gc_memory:.2f} MB")
            print(f"垃圾回收释放: {analysis_memory - gc_memory:.2f} MB")
    
    def save_performance_results(self):
        """保存性能结果到文件并生成图表"""
        # 保存为JSON
        results_file = os.path.join(self.results_dir, "performance_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.performance_results, f, indent=2)
        
        # 生成性能图表
        self.generate_performance_charts()
        
        print(f"\n性能结果已保存到: {results_file}")
    
    def generate_performance_charts(self):
        """生成性能图表"""
        # 创建堆叠条形图
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 准备数据
        data_sizes = self.performance_results["data_size"]
        indicator_times = self.performance_results["indicator_time"]
        pattern_times = self.performance_results["pattern_time"]
        signal_times = self.performance_results["signal_time"]
        backtest_times = self.performance_results["backtest_time"]
        report_times = self.performance_results["report_time"]
        
        # 创建堆叠条形图
        bar_width = 0.6
        x = np.arange(len(data_sizes))
        
        ax.bar(x, indicator_times, bar_width, label='指标计算')
        ax.bar(x, pattern_times, bar_width, bottom=indicator_times, label='形态识别')
        
        bottom = np.array(indicator_times) + np.array(pattern_times)
        ax.bar(x, signal_times, bar_width, bottom=bottom, label='信号生成')
        
        bottom = bottom + np.array(signal_times)
        ax.bar(x, backtest_times, bar_width, bottom=bottom, label='回测执行')
        
        bottom = bottom + np.array(backtest_times)
        ax.bar(x, report_times, bar_width, bottom=bottom, label='报告生成')
        
        # 添加标签和标题
        ax.set_xlabel('数据大小')
        ax.set_ylabel('执行时间 (秒)')
        ax.set_title('TradeMind Lite 性能基准测试')
        ax.set_xticks(x)
        ax.set_xticklabels(data_sizes)
        ax.legend()
        
        # 添加总时间标签
        for i, total in enumerate(self.performance_results["total_time"]):
            ax.text(i, total + 0.1, f'{total:.2f}秒', ha='center')
        
        # 保存图表
        chart_file = os.path.join(self.results_dir, "performance_chart.png")
        plt.tight_layout()
        plt.savefig(chart_file)
        plt.close()
        
        # 创建饼图显示各组件占比
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 计算各组件平均时间
        avg_indicator = np.mean(indicator_times)
        avg_pattern = np.mean(pattern_times)
        avg_signal = np.mean(signal_times)
        avg_backtest = np.mean(backtest_times)
        avg_report = np.mean(report_times)
        
        # 创建饼图
        labels = ['指标计算', '形态识别', '信号生成', '回测执行', '报告生成']
        sizes = [avg_indicator, avg_pattern, avg_signal, avg_backtest, avg_report]
        explode = (0.1, 0, 0, 0, 0)  # 突出显示第一个部分
        
        ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
               shadow=True, startangle=90)
        ax.axis('equal')  # 确保饼图是圆的
        ax.set_title('各组件平均执行时间占比')
        
        # 保存饼图
        pie_file = os.path.join(self.results_dir, "component_time_pie.png")
        plt.tight_layout()
        plt.savefig(pie_file)
        plt.close()


if __name__ == '__main__':
    unittest.main() 