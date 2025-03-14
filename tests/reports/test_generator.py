"""
报告生成模块的单元测试
"""

import unittest
import os
import shutil
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from trademind.reports.generator import (
    generate_html_report,
    generate_performance_charts
)
from trademind.core.patterns import TechnicalPattern


class TestReportGenerator(unittest.TestCase):
    """报告生成模块的单元测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建临时目录用于输出
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试结果
        self.test_results = [
            {
                'symbol': 'AAPL',
                'name': '苹果公司',
                'price': 150.25,
                'change': 2.5,
                'indicators': {
                    'rsi': 65.5,
                    'kdj': {'k': 75.2, 'd': 65.8, 'j': 84.6},
                    'macd': {'macd': 0.125, 'signal': 0.089, 'hist': 0.036},
                    'bollinger': {'upper': 155.25, 'middle': 148.75, 'lower': 142.25}
                },
                'patterns': [
                    TechnicalPattern(name="看涨吞没形态", confidence=0.85, description="看涨信号"),
                    TechnicalPattern(name="锤子线", confidence=0.75, description="潜在反转信号")
                ],
                'advice': {
                    'signal': '买入',
                    'reason': '技术指标显示强势上涨趋势'
                },
                'backtest': {
                    'total_trades': 24,
                    'win_rate': 68.5,
                    'avg_profit': 1.25,
                    'profit_factor': 2.1,
                    'max_profit': 5.75,
                    'max_loss': -2.35,
                    'max_drawdown': 12.5,
                    'consecutive_losses': 3,
                    'avg_hold_days': 8.5,
                    'final_return': 32.5,
                    'sharpe_ratio': 1.85,
                    'sortino_ratio': 2.15
                }
            },
            {
                'symbol': 'MSFT',
                'name': '微软公司',
                'price': 290.75,
                'change': -1.2,
                'indicators': {
                    'rsi': 42.5,
                    'kdj': {'k': 35.2, 'd': 45.8, 'j': 24.6},
                    'macd': {'macd': -0.225, 'signal': -0.089, 'hist': -0.136},
                    'bollinger': {'upper': 305.25, 'middle': 295.75, 'lower': 286.25}
                },
                'patterns': [
                    TechnicalPattern(name="看跌吞没形态", confidence=0.82, description="看跌信号")
                ],
                'advice': {
                    'signal': '卖出',
                    'reason': '技术指标显示下跌趋势'
                },
                'backtest': {
                    'total_trades': 18,
                    'win_rate': 55.5,
                    'avg_profit': 0.85,
                    'profit_factor': 1.5,
                    'max_profit': 4.25,
                    'max_loss': -3.15,
                    'max_drawdown': 18.5,
                    'consecutive_losses': 4,
                    'avg_hold_days': 6.5,
                    'final_return': 22.5,
                    'sharpe_ratio': 1.35,
                    'sortino_ratio': 1.65
                }
            }
        ]
        
        # 创建测试交易记录
        self.test_trades = [
            {
                'symbol': 'AAPL',
                'entry_date': datetime.now() - timedelta(days=30),
                'exit_date': datetime.now() - timedelta(days=25),
                'entry_price': 145.50,
                'exit_price': 150.25,
                'shares': 10,
                'profit': 47.5,
                'exit_reason': '止盈'
            },
            {
                'symbol': 'MSFT',
                'entry_date': datetime.now() - timedelta(days=20),
                'exit_date': datetime.now() - timedelta(days=15),
                'entry_price': 295.50,
                'exit_price': 290.75,
                'shares': 5,
                'profit': -23.75,
                'exit_reason': '止损'
            },
            {
                'symbol': 'AAPL',
                'entry_date': datetime.now() - timedelta(days=10),
                'exit_date': datetime.now() - timedelta(days=5),
                'entry_price': 148.75,
                'exit_price': 152.50,
                'shares': 8,
                'profit': 30.0,
                'exit_reason': '技术指标'
            }
        ]
        
        # 创建测试权益曲线
        self.test_equity = [10000, 10047.5, 10023.75, 10053.75]
        
        # 创建日期索引
        self.date_index = pd.date_range(
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            freq='D'
        )
    
    def tearDown(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_html_report(self):
        """测试生成HTML报告"""
        # 生成报告
        report_path = generate_html_report(
            results=self.test_results,
            title="测试报告",
            output_dir=self.temp_dir
        )
        
        # 检查报告文件是否存在
        self.assertTrue(os.path.exists(report_path))
        
        # 检查报告内容
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查标题
            self.assertIn("测试报告", content)
            
            # 检查股票信息
            self.assertIn("AAPL", content)
            self.assertIn("苹果公司", content)
            self.assertIn("MSFT", content)
            self.assertIn("微软公司", content)
            
            # 检查技术指标
            self.assertIn("RSI", content)
            self.assertIn("KDJ", content)
            self.assertIn("MACD", content)
            self.assertIn("BB上轨", content)
            
            # 检查K线形态
            self.assertIn("看涨吞没形态", content)
            self.assertIn("看跌吞没形态", content)
            
            # 检查交易建议
            self.assertIn("买入", content)
            self.assertIn("卖出", content)
            
            # 检查回测结果
            self.assertIn("总交易次数", content)
            self.assertIn("胜率", content)
            self.assertIn("最大回撤", content)
    
    def test_generate_performance_charts(self):
        """测试生成性能图表"""
        # 生成图表
        chart_paths = generate_performance_charts(
            trades=self.test_trades,
            equity=self.test_equity,
            dates=self.date_index,
            output_dir=self.temp_dir
        )
        
        # 检查图表文件是否存在
        self.assertIn('equity_curve', chart_paths)
        self.assertTrue(os.path.exists(chart_paths['equity_curve']))
        
        self.assertIn('monthly_returns', chart_paths)
        self.assertTrue(os.path.exists(chart_paths['monthly_returns']))
        
        self.assertIn('exit_reasons', chart_paths)
        self.assertTrue(os.path.exists(chart_paths['exit_reasons']))
        
        self.assertIn('profit_distribution', chart_paths)
        self.assertTrue(os.path.exists(chart_paths['profit_distribution']))
    
    def test_generate_html_report_with_empty_results(self):
        """测试生成空结果的HTML报告"""
        # 生成报告
        report_path = generate_html_report(
            results=[],
            title="空报告测试",
            output_dir=self.temp_dir
        )
        
        # 检查报告文件是否存在
        self.assertTrue(os.path.exists(report_path))
        
        # 检查报告内容
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查标题
            self.assertIn("空报告测试", content)
            
            # 检查空数据提示
            self.assertIn("没有可用的分析数据", content)
            
            # 确保没有股票卡片内容（而不是检查CSS类名）
            self.assertNotIn("<div class=\"stock-card\">", content)
    
    def test_generate_performance_charts_with_empty_trades(self):
        """测试生成空交易记录的性能图表"""
        # 生成图表
        chart_paths = generate_performance_charts(
            trades=[],
            equity=[10000],
            dates=self.date_index,
            output_dir=self.temp_dir
        )
        
        # 检查结果应该是空字典
        self.assertEqual(len(chart_paths), 0)


if __name__ == '__main__':
    unittest.main() 