import unittest
import pandas as pd
import numpy as np
from strategies.advanced_analysis import AdvancedAnalysis

class TestAdvancedAnalysis(unittest.TestCase):
    def setUp(self):
        """测试前的初始化工作"""
        self.analysis = AdvancedAnalysis()
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

    def test_volatility_analysis(self):
        """测试波动率分析"""
        volatility = self.analysis.calculate_volatility(self.test_data['close'])
        self.assertIsInstance(volatility, float)
        self.assertGreater(volatility, 0)

    def test_pattern_recognition(self):
        """测试形态识别"""
        patterns = self.analysis.recognize_patterns(self.test_data)
        self.assertIsInstance(patterns, dict)
        self.assertIn('patterns_found', patterns)

    def test_risk_metrics(self):
        """测试风险指标计算"""
        risk_metrics = self.analysis.calculate_risk_metrics(self.test_data)
        self.assertIn('var', risk_metrics)
        self.assertIn('sharpe_ratio', risk_metrics)
        self.assertIn('max_drawdown', risk_metrics)

if __name__ == '__main__':
    unittest.main()
