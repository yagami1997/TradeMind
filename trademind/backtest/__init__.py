"""
TradeMind Lite（轻量版）- 回测系统模块

本模块包含交易策略回测相关的功能，用于评估交易策略的性能。
"""

from trademind.backtest.engine import (
    run_backtest,
    simulate_trades,
    calculate_performance_metrics,
    generate_trade_summary
)

__all__ = [
    'run_backtest',
    'simulate_trades',
    'calculate_performance_metrics',
    'generate_trade_summary'
] 