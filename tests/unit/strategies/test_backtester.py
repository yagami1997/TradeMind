import unittest
import pandas as pd
import numpy as np
from strategies.backtester import Backtester, Portfolio, RiskManager

class TestBacktester(unittest.TestCase):
    def setUp(self):
        """测试前的初始化工作"""
        self.backtester = Backtester()
        self.test_data = self._generate_test_data()

    def _generate_test_data(self):
        """生成测试用的市场数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        data = pd.DataFrame({
            'open': np.random.randn(len(dates)) + 100,
            'high': np.random.randn(len(dates)) + 101,
            'low': np.random.randn(len(dates)) + 99,
            'close': np.random.randn(len(dates)) + 100,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        return data

    def test_portfolio_initialization(self):
        """测试投资组合初始化"""
        portfolio = Portfolio(initial_capital=100000.0)
        self.assertEqual(portfolio.initial_capital, 100000.0)
        self.assertEqual(portfolio.current_capital, 100000.0)
        self.assertEqual(len(portfolio.positions), 0)

    def test_risk_manager(self):
        """测试风险管理器"""
        risk_manager = RiskManager()
        position_size = risk_manager.calculate_position_size(
            capital=100000.0,
            price=100.0,
            volatility=0.2
        )
        self.assertGreater(position_size, 0)
        self.assertLess(position_size, 100000.0/100.0)

    def test_data_loading(self):
        """测试数据加载"""
        self.backtester.load_data('TEST', self.test_data)
        self.assertIn('TEST', self.backtester.data)
        self.assertEqual(len(self.backtester.data['TEST']), len(self.test_data))

if __name__ == '__main__':
    unittest.main()
