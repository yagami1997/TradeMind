"""
回测系统模块的单元测试
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trademind.backtest.engine import (
    run_backtest,
    simulate_trades,
    calculate_performance_metrics,
    generate_trade_summary
)


class TestBacktestEngine(unittest.TestCase):
    """测试回测引擎功能"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用的价格数据
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        
        # 创建一个上涨趋势的价格序列
        close_prices = np.linspace(100, 150, 100) + np.random.normal(0, 1, 100)
        high_prices = close_prices + np.random.uniform(0, 2, 100)
        low_prices = close_prices - np.random.uniform(0, 2, 100)
        open_prices = close_prices - np.random.normal(0, 1, 100)
        volume = np.random.uniform(1000, 5000, 100)
        
        self.data = pd.DataFrame({
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volume
        }, index=dates)
        
        # 创建测试用的信号数据
        buy_signals = np.zeros(100)
        sell_signals = np.zeros(100)
        
        # 设置一些买入和卖出信号
        buy_signals[10] = 1  # 第10天买入
        buy_signals[40] = 1  # 第40天买入
        buy_signals[70] = 1  # 第70天买入
        
        sell_signals[30] = 1  # 第30天卖出
        sell_signals[60] = 1  # 第60天卖出
        sell_signals[90] = 1  # 第90天卖出
        
        self.signals = pd.DataFrame({
            'buy_signal': buy_signals,
            'sell_signal': sell_signals
        }, index=dates)
    
    def test_run_backtest_with_valid_data(self):
        """测试使用有效数据运行回测"""
        result = run_backtest(self.data, self.signals)
        
        # 验证结果包含预期的键
        expected_keys = [
            'total_trades', 'win_rate', 'avg_profit', 'max_profit',
            'max_loss', 'profit_factor', 'max_drawdown', 'consecutive_losses',
            'avg_hold_days', 'final_return', 'sharpe_ratio', 'sortino_ratio',
            'net_profit', 'annualized_return'
        ]
        
        for key in expected_keys:
            self.assertIn(key, result)
        
        # 验证交易次数
        self.assertGreaterEqual(result['total_trades'], 1)
    
    def test_run_backtest_with_insufficient_data(self):
        """测试使用不足的数据运行回测"""
        # 创建一个只有10天数据的小数据集
        small_data = self.data.iloc[:10]
        small_signals = self.signals.iloc[:10]
        
        result = run_backtest(small_data, small_signals)
        
        # 验证结果是默认值
        self.assertEqual(result['total_trades'], 0)
        self.assertEqual(result['win_rate'], 0)
    
    def test_run_backtest_with_no_signals(self):
        """测试没有交易信号的情况"""
        # 创建一个没有信号的数据集
        no_signals = pd.DataFrame({
            'buy_signal': np.zeros(100),
            'sell_signal': np.zeros(100)
        }, index=self.data.index)
        
        result = run_backtest(self.data, no_signals)
        
        # 验证没有交易发生
        self.assertEqual(result['total_trades'], 0)
    
    def test_simulate_trades(self):
        """测试交易模拟功能"""
        trades, equity = simulate_trades(self.data, self.signals)
        
        # 验证交易记录和权益曲线
        self.assertIsInstance(trades, list)
        self.assertIsInstance(equity, list)
        
        # 验证权益曲线长度
        # 权益曲线应该比数据长度多1（初始资金）
        self.assertEqual(len(equity), len(self.data) - 49)  # 考虑到从第50个数据点开始
        
        # 如果有交易，验证交易记录格式
        if trades:
            first_trade = trades[0]
            expected_trade_keys = [
                'entry_date', 'entry_price', 'exit_date', 'exit_price',
                'position', 'shares', 'profit', 'profit_pct',
                'exit_reason', 'hold_days'
            ]
            
            for key in expected_trade_keys:
                self.assertIn(key, first_trade)
    
    def test_calculate_performance_metrics(self):
        """测试性能指标计算功能"""
        # 创建一些模拟的交易记录
        trades = [
            {
                'entry_date': datetime(2020, 1, 10),
                'entry_price': 100.0,
                'exit_date': datetime(2020, 1, 20),
                'exit_price': 110.0,
                'position': 'long',
                'shares': 100,
                'profit': 1000.0,
                'profit_pct': 10.0,
                'exit_reason': '止盈',
                'hold_days': 10
            },
            {
                'entry_date': datetime(2020, 2, 10),
                'entry_price': 120.0,
                'exit_date': datetime(2020, 2, 15),
                'exit_price': 115.0,
                'position': 'long',
                'shares': 100,
                'profit': -500.0,
                'profit_pct': -4.17,
                'exit_reason': '止损',
                'hold_days': 5
            }
        ]
        
        # 创建模拟的权益曲线
        equity = [10000.0, 10500.0, 11000.0, 10500.0, 10000.0]
        
        # 计算性能指标
        metrics = calculate_performance_metrics(
            trades, equity, 10000.0, self.data.index
        )
        
        # 验证指标计算
        self.assertEqual(metrics['total_trades'], 2)
        self.assertEqual(metrics['win_rate'], 50.0)  # 50% 胜率
        self.assertEqual(metrics['avg_profit'], 250.0)  # (1000 - 500) / 2
        self.assertEqual(metrics['max_profit'], 1000.0)
        self.assertEqual(metrics['max_loss'], -500.0)
    
    def test_generate_trade_summary(self):
        """测试交易摘要生成功能"""
        # 创建一些模拟的交易记录
        trades = [
            {
                'entry_date': datetime(2020, 1, 10),
                'entry_price': 100.0,
                'exit_date': datetime(2020, 1, 20),
                'exit_price': 110.0,
                'position': 'long',
                'shares': 100,
                'profit': 1000.0,
                'profit_pct': 10.0,
                'exit_reason': '止盈',
                'hold_days': 10
            },
            {
                'entry_date': datetime(2020, 1, 25),
                'entry_price': 120.0,
                'exit_date': datetime(2020, 1, 30),
                'exit_price': 115.0,
                'position': 'long',
                'shares': 100,
                'profit': -500.0,
                'profit_pct': -4.17,
                'exit_reason': '止损',
                'hold_days': 5
            },
            {
                'entry_date': datetime(2020, 2, 10),
                'entry_price': 130.0,
                'exit_date': datetime(2020, 2, 20),
                'exit_price': 120.0,
                'position': 'short',
                'shares': 100,
                'profit': 1000.0,
                'profit_pct': 7.69,
                'exit_reason': '止盈',
                'hold_days': 10
            }
        ]
        
        # 生成交易摘要
        summary = generate_trade_summary(trades)
        
        # 验证摘要包含预期的键
        self.assertIn('monthly_performance', summary)
        self.assertIn('exit_reason_stats', summary)
        self.assertIn('position_stats', summary)
        
        # 验证月度统计
        monthly = summary['monthly_performance']
        self.assertIn('2020-01', monthly)
        self.assertIn('2020-02', monthly)
        
        # 验证平仓原因统计
        exit_reasons = summary['exit_reason_stats']
        self.assertIn('止盈', exit_reasons)
        self.assertIn('止损', exit_reasons)
        
        # 验证持仓方向统计
        positions = summary['position_stats']
        self.assertIn('long', positions)
        self.assertIn('short', positions)
        
        # 验证具体数值
        self.assertEqual(positions['long']['count'], 2)
        self.assertEqual(positions['short']['count'], 1)
        self.assertEqual(exit_reasons['止盈']['count'], 2)
        self.assertEqual(exit_reasons['止损']['count'], 1)


if __name__ == '__main__':
    unittest.main() 