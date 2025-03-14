"""
TradeMind Lite（轻量版）- 报告生成模块

本模块包含生成分析报告和性能图表的功能。
"""

from trademind.reports.generator import (
    generate_html_report,
    generate_performance_charts
)

__all__ = [
    'generate_html_report',
    'generate_performance_charts'
] 