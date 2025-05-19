"""
TradeMind Lite - 股票技术分析工具

TradeMind Lite是一个轻量级的股票技术分析工具，可以帮助用户分析股票的技术指标、
K线形态，并生成交易建议。
"""

__version__ = "0.3.3"

# 导入子模块
from . import core
from . import backtest
from . import reports
from . import compat
from . import ui

__all__ = ["core", "backtest", "reports", "compat", "ui", "__version__"] 