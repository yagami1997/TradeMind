import unittest
import pandas as pd
import numpy as np
from strategies.stock_analyzer import StockAnalyzer
from strategies.tech_indicator_calculator import TechnicalIndicator

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        """测试前的初始化工作"""
        self.analyzer = StockAnalyzer()
        self.test_data = self._generate_test_data()
        self.tech_indicator = TechnicalIndicator()

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

    def test_technical_indicators(self):
        """测试技术指标计算"""
        # 测试MA计算
        ma = self.tech_indicator.calculate_ma(self.test_data['close'], 20)
        self.assertEqual(len(ma), len(self.test_data))
        
        # 测试MACD计算
        macd = self.tech_indicator.calculate_macd(self.test_data['close'])
        self.assertEqual(len(macd), len(self.test_data))

    def test_trend_analysis(self):
        """测试趋势分析"""
        trend = self.analyzer.analyze_trend(self.test_data)
        self.assertIn('trend_direction', trend)
        self.assertIn('trend_strength', trend)

    def test_signal_generation(self):
        """测试信号生成"""
        signals = self.analyzer.generate_signals(self.test_data)
        self.assertIn('buy_signals', signals)
        self.assertIn('sell_signals', signals)

if __name__ == '__main__':
    unittest.main()
