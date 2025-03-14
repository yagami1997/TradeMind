"""
TradeMind Lite（轻量版）- 信号生成模块测试

本模块测试交易信号生成相关的函数。
"""

import unittest
import pandas as pd
import numpy as np
from trademind.core.signals import (
    generate_signals, 
    generate_buy_signals, 
    generate_sell_signals,
    generate_trading_advice
)
from trademind.core.patterns import TechnicalPattern


class TestSignalGeneration(unittest.TestCase):
    """测试信号生成函数"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建一个基本的DataFrame用于测试
        self.dates = pd.date_range(start='2023-01-01', periods=100)
        self.data = pd.DataFrame({
            'Open': np.random.normal(100, 5, 100),
            'High': np.random.normal(105, 5, 100),
            'Low': np.random.normal(95, 5, 100),
            'Close': np.random.normal(100, 5, 100),
            'Volume': np.random.normal(1000000, 200000, 100)
        }, index=self.dates)
        
        # 确保High始终大于等于Open和Close
        self.data['High'] = self.data[['Open', 'Close', 'High']].max(axis=1)
        
        # 确保Low始终小于等于Open和Close
        self.data['Low'] = self.data[['Open', 'Close', 'Low']].min(axis=1)
        
        # 创建技术指标
        self.indicators = {
            'rsi': pd.Series(np.random.normal(50, 15, 100), index=self.dates),
            'macd': {
                'macd': pd.Series(np.random.normal(0, 1, 100), index=self.dates),
                'signal': pd.Series(np.random.normal(0, 1, 100), index=self.dates),
                'hist': pd.Series(np.random.normal(0, 0.5, 100), index=self.dates)
            },
            'bollinger': {
                'upper': self.data['Close'] + 2,
                'middle': self.data['Close'],
                'lower': self.data['Close'] - 2,
                'bandwidth': pd.Series(np.random.normal(0.2, 0.05, 100), index=self.dates),
                'percent_b': pd.Series(np.random.normal(0.5, 0.2, 100), index=self.dates)
            },
            'sma': {
                'short': 105,
                'medium': 100,
                'long': 95
            },
            'sma5': self.data['Close'].rolling(window=5).mean(),
            'sma10': self.data['Close'].rolling(window=10).mean(),
            'sma50': self.data['Close'].rolling(window=50).mean(),
            'kdj': {
                'k': pd.Series(np.random.normal(50, 15, 100), index=self.dates),
                'd': pd.Series(np.random.normal(50, 10, 100), index=self.dates),
                'j': pd.Series(np.random.normal(50, 25, 100), index=self.dates)
            }
        }
        
        # 创建买入信号场景
        self.buy_scenario_data = self.data.copy()
        self.buy_indicators = self.indicators.copy()
        self.buy_indicators['rsi'] = pd.Series(np.random.normal(25, 5, 100), index=self.dates)  # RSI低于30
        self.buy_indicators['macd']['macd'] = pd.Series(np.linspace(-1, 1, 100), index=self.dates)  # MACD上穿信号线
        self.buy_indicators['macd']['signal'] = pd.Series(np.linspace(-0.5, 0.5, 100), index=self.dates)
        
        # 创建卖出信号场景
        self.sell_scenario_data = self.data.copy()
        self.sell_indicators = self.indicators.copy()
        self.sell_indicators['rsi'] = pd.Series(np.random.normal(75, 5, 100), index=self.dates)  # RSI高于70
        self.sell_indicators['macd']['macd'] = pd.Series(np.linspace(1, -1, 100), index=self.dates)  # MACD下穿信号线
        self.sell_indicators['macd']['signal'] = pd.Series(np.linspace(0.5, -0.5, 100), index=self.dates)
    
    def test_empty_data(self):
        """测试空数据处理"""
        empty_data = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'])
        signals = generate_signals(empty_data, {})
        self.assertTrue(signals.empty)
    
    def test_insufficient_data(self):
        """测试数据不足的情况"""
        insufficient_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [102, 103, 104]
        })
        signals = generate_signals(insufficient_data, {})
        self.assertTrue(signals.empty)
    
    def test_generate_signals(self):
        """测试信号生成函数"""
        signals = generate_signals(self.data, self.indicators)
        self.assertFalse(signals.empty)
        self.assertIn('buy_signal', signals.columns)
        self.assertIn('sell_signal', signals.columns)
        
        # 验证信号是0或1
        self.assertTrue(all((signals['buy_signal'] == 0) | (signals['buy_signal'] == 1)))
        self.assertTrue(all((signals['sell_signal'] == 0) | (signals['sell_signal'] == 1)))
    
    def test_generate_buy_signals(self):
        """测试买入信号生成函数"""
        signals_df = pd.DataFrame({
            'close': self.data['Close'],
            'rsi': pd.Series(np.ones(100) * 25, index=self.dates),  # RSI低于30
            'macd_line': pd.Series(np.ones(100) * 0.5, index=self.dates),
            'signal_line': pd.Series(np.ones(100) * 0.3, index=self.dates),  # MACD > Signal
            'lower_band': self.data['Close'] + 10,  # 价格低于下轨
            'sma5': self.data['Close'] - 5,
            'sma10': self.data['Close'] - 10
        })
        
        # 前一天的MACD < Signal，形成金叉
        signals_df['macd_line'].iloc[:-1] = 0.2
        signals_df['signal_line'].iloc[:-1] = 0.4
        
        buy_signals = generate_buy_signals(signals_df)
        
        # 验证最后一天应该有买入信号
        self.assertEqual(buy_signals.iloc[-1], 1)
    
    def test_generate_sell_signals(self):
        """测试卖出信号生成函数"""
        signals_df = pd.DataFrame({
            'close': self.data['Close'],
            'rsi': pd.Series(np.ones(100) * 75, index=self.dates),  # RSI高于70
            'macd_line': pd.Series(np.ones(100) * 0.3, index=self.dates),
            'signal_line': pd.Series(np.ones(100) * 0.5, index=self.dates),  # MACD < Signal
            'upper_band': self.data['Close'] - 10,  # 价格高于上轨
            'sma5': self.data['Close'] + 5,
            'sma10': self.data['Close'] + 10
        })
        
        # 前一天的MACD > Signal，形成死叉
        signals_df['macd_line'].iloc[:-1] = 0.6
        signals_df['signal_line'].iloc[:-1] = 0.4
        
        sell_signals = generate_sell_signals(signals_df)
        
        # 验证最后一天应该有卖出信号
        self.assertEqual(sell_signals.iloc[-1], 1)
    
    def test_generate_trading_advice(self):
        """测试交易建议生成函数"""
        # 创建一个看涨场景
        bullish_indicators = {
            'macd': {
                'macd': 0.5,
                'signal': 0.3,
                'hist': 0.2
            },
            'rsi': 40,
            'bollinger': {
                'upper': 110,
                'middle': 100,
                'lower': 90,
                'bandwidth': 0.2,
                'percent_b': 0.6
            },
            'sma': {
                'short': 105,
                'medium': 100,
                'long': 95
            }
        }
        
        patterns = [
            TechnicalPattern(name="看涨吞没", confidence=80, description="看涨形态")
        ]
        
        advice = generate_trading_advice(bullish_indicators, 100, patterns)
        
        self.assertIsNotNone(advice)
        self.assertIn('advice', advice)
        self.assertIn('confidence', advice)
        self.assertIn('signals', advice)
        self.assertIn('color', advice)
        self.assertIn('system_scores', advice)
        self.assertIn('total_score', advice)
        
        # 验证系统得分
        self.assertIn('trend', advice['system_scores'])
        self.assertIn('momentum', advice['system_scores'])
        self.assertIn('volatility', advice['system_scores'])
        
        # 验证信号列表
        self.assertTrue(len(advice['signals']) > 0)
        
        # 验证看涨形态被包含在信号中
        pattern_signals = [s for s in advice['signals'] if "看涨吞没" in s]
        self.assertTrue(len(pattern_signals) > 0)
    
    def test_trading_advice_bearish(self):
        """测试看跌场景的交易建议"""
        # 创建一个看跌场景
        bearish_indicators = {
            'macd': {
                'macd': -0.5,
                'signal': -0.3,
                'hist': -0.2
            },
            'rsi': 75,
            'bollinger': {
                'upper': 110,
                'middle': 100,
                'lower': 90,
                'bandwidth': 0.2,
                'percent_b': 0.9
            },
            'sma': {
                'short': 95,
                'medium': 100,
                'long': 105
            }
        }
        
        patterns = [
            TechnicalPattern(name="看跌吞没", confidence=80, description="看跌形态")
        ]
        
        advice = generate_trading_advice(bearish_indicators, 108, patterns)
        
        self.assertIsNotNone(advice)
        
        # 验证看跌建议
        self.assertIn(advice['advice'], ["卖出", "强烈卖出", "观望偏空"])
        
        # 验证看跌形态被包含在信号中
        pattern_signals = [s for s in advice['signals'] if "看跌吞没" in s]
        self.assertTrue(len(pattern_signals) > 0)
    
    def test_trading_advice_neutral(self):
        """测试中性场景的交易建议"""
        # 创建一个中性场景
        neutral_indicators = {
            'macd': {
                'macd': 0.1,
                'signal': 0.1,
                'hist': 0
            },
            'rsi': 50,
            'bollinger': {
                'upper': 110,
                'middle': 100,
                'lower': 90,
                'bandwidth': 0.1,
                'percent_b': 0.5
            },
            'sma': {
                'short': 100,
                'medium': 100,
                'long': 100
            }
        }
        
        patterns = [
            TechnicalPattern(name="十字星", confidence=70, description="中性形态")
        ]
        
        advice = generate_trading_advice(neutral_indicators, 100, patterns)
        
        self.assertIsNotNone(advice)
        
        # 验证中性建议
        self.assertIn(advice['advice'], ["观望", "观望偏多", "观望偏空"])
        
        # 验证中性形态被包含在信号中
        pattern_signals = [s for s in advice['signals'] if "十字星" in s]
        self.assertTrue(len(pattern_signals) > 0)


if __name__ == '__main__':
    unittest.main() 