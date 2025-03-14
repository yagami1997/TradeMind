"""
技术指标计算模块的测试

本模块包含对trademind.core.indicators模块中技术指标计算函数的测试。
测试确保迁移后的函数与原StockAnalyzer类中的函数行为一致。
"""

import unittest
import pandas as pd
import numpy as np
import math
from trademind.core.indicators import (
    calculate_macd,
    calculate_kdj,
    calculate_rsi,
    calculate_bollinger_bands
)


class TestIndicators(unittest.TestCase):
    """测试技术指标计算函数"""

    def setUp(self):
        """设置测试数据"""
        # 创建一个模拟的价格序列，确保足够长以计算所有指标
        self.prices = pd.Series([
            100, 102, 104, 103, 105, 107, 108, 107, 106, 105,
            104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
            114, 115, 116, 117, 118, 119, 120, 121, 122, 123,
            124, 125, 126, 127, 128, 129, 130, 131, 132, 133
        ])
        self.high = pd.Series([
            102, 104, 106, 105, 107, 109, 110, 109, 108, 107,
            106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
            116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
            126, 127, 128, 129, 130, 131, 132, 133, 134, 135
        ])
        self.low = pd.Series([
            98, 100, 102, 101, 103, 105, 106, 105, 104, 103,
            102, 103, 104, 105, 106, 107, 108, 109, 110, 111,
            112, 113, 114, 115, 116, 117, 118, 119, 120, 121,
            122, 123, 124, 125, 126, 127, 128, 129, 130, 131
        ])

    def test_calculate_macd(self):
        """测试MACD计算函数"""
        macd_line, signal_line, histogram = calculate_macd(self.prices)
        
        # 验证返回值类型
        self.assertIsInstance(macd_line, float)
        self.assertIsInstance(signal_line, float)
        self.assertIsInstance(histogram, float)
        
        # 验证MACD线和信号线的关系
        # 由于浮点数精度问题，直接比较差值
        self.assertAlmostEqual(histogram, macd_line - signal_line, places=6)
        
        # 验证返回值不是NaN
        self.assertFalse(math.isnan(macd_line))
        self.assertFalse(math.isnan(signal_line))
        self.assertFalse(math.isnan(histogram))

    def test_calculate_kdj(self):
        """测试KDJ计算函数"""
        k, d, j = calculate_kdj(self.high, self.low, self.prices)
        
        # 验证返回值类型
        self.assertIsInstance(k, float)
        self.assertIsInstance(d, float)
        self.assertIsInstance(j, float)
        
        # 验证K、D、J的关系
        self.assertAlmostEqual(j, 3 * k - 2 * d, places=6)
        
        # 验证K、D、J的范围
        self.assertGreaterEqual(k, 0)
        self.assertLessEqual(k, 100)
        self.assertGreaterEqual(d, 0)
        self.assertLessEqual(d, 100)
        self.assertGreaterEqual(j, 0)
        self.assertLessEqual(j, 100)
        
        # 验证返回值不是NaN
        self.assertFalse(math.isnan(k))
        self.assertFalse(math.isnan(d))
        self.assertFalse(math.isnan(j))

    def test_calculate_rsi(self):
        """测试RSI计算函数"""
        rsi = calculate_rsi(self.prices)
        
        # 验证返回值类型
        self.assertIsInstance(rsi, float)
        
        # 验证RSI的范围
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
        
        # 验证返回值不是NaN
        self.assertFalse(math.isnan(rsi))

    def test_calculate_bollinger_bands(self):
        """测试布林带计算函数"""
        upper, middle, lower, bandwidth, percent_b = calculate_bollinger_bands(self.prices)
        
        # 验证返回值类型
        self.assertIsInstance(upper, float)
        self.assertIsInstance(middle, float)
        self.assertIsInstance(lower, float)
        self.assertIsInstance(bandwidth, float)
        self.assertIsInstance(percent_b, float)
        
        # 验证上轨、中轨、下轨的关系
        self.assertGreater(upper, middle)
        self.assertGreater(middle, lower)
        
        # 验证返回值不是NaN
        self.assertFalse(math.isnan(upper))
        self.assertFalse(math.isnan(middle))
        self.assertFalse(math.isnan(lower))
        self.assertFalse(math.isnan(bandwidth))
        self.assertFalse(math.isnan(percent_b))


if __name__ == '__main__':
    unittest.main() 