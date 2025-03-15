"""
trademind.core 包

这个包包含了交易系统的核心功能模块，包括技术指标、信号生成和分析工具。
"""

from trademind.core import indicators
from trademind.core import signals
from trademind.core import patterns
from trademind.core import analyzer
from trademind.core import dynamic_rsi_strategy

# 导出常用函数，方便直接导入
from trademind.core.indicators import (
    calculate_macd,
    calculate_rsi,
    calculate_kdj,
    calculate_bollinger_bands,
    calculate_dynamic_rsi_thresholds
)

from trademind.core.dynamic_rsi_strategy import (
    dynamic_atr_rsi,
    generate_signals,
    backtest_dynamic_rsi
)
