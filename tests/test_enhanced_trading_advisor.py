import unittest
from unittest.mock import Mock, patch
from strategies.enhanced_trading_advisor import EnhancedTradingAdvisor
import pandas as pd

class TestEnhancedTradingAdvisor(unittest.TestCase):
    def setUp(self):
        self.advisor = EnhancedTradingAdvisor()
        
    @patch('strategies.enhanced_trading_advisor.YahooFinanceManager')
    def test_analyze_stock(self, mock_yf):
        # 设置模拟数据
        mock_data = pd.DataFrame({
            'close': [100, 101, 102],
            'volume': [1000, 1100, 1200]
        })
        mock_yf.return_value.get_stock_data.return_value = mock_data
        
        # 测试分析
        result = self.advisor.analyze_stock('AAPL')
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        
    def test_generate_portfolio_report(self):
        # 测试组合报告生成
        mock_results = [
            {'metrics': {'total_returns': 0.1, 'sharpe_ratio': 1.5, 'max_drawdown': -0.05}},
            {'metrics': {'total_returns': 0.2, 'sharpe_ratio': 2.0, 'max_drawdown': -0.03}}
        ]
        
        with patch.object(self.advisor, 'analyze_watchlist', return_value=mock_results):
            report = self.advisor.generate_portfolio_report('test_list')
            self.assertIsNotNone(report)
            self.assertIn('portfolio_metrics', report) 