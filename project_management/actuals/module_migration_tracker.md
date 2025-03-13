# 模块迁移跟踪表

## 概述
本文档用于跟踪TradeMind轻量版重构过程中各个函数/方法的迁移状态。

## 时间戳
<!-- 使用generate_timestamp.py生成 -->
2025-03-13 06:20:00 PDT

## 迁移状态说明
- **未开始**: 尚未开始迁移
- **进行中**: 正在进行代码迁移
- **已迁移**: 代码已迁移到新位置
- **已测试**: 迁移后的代码已通过测试
- **已验证**: 迁移后的功能与原系统一致

## 技术指标模块 (TASK-002)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| calculate_rsi | stock_analyzer.py:267 | core/indicators.py | 未开始 | 未测试 | |
| calculate_macd | stock_analyzer.py:198 | core/indicators.py | 未开始 | 未测试 | |
| calculate_kdj | stock_analyzer.py:227 | core/indicators.py | 未开始 | 未测试 | |
| calculate_bollinger_bands | stock_analyzer.py:311 | core/indicators.py | 未开始 | 未测试 | |

## 形态识别模块 (TASK-003)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| identify_candlestick_patterns | stock_analyzer.py:71 | core/patterns.py | 未开始 | 未测试 | |
| TechnicalPattern类 | stock_analyzer.py:21 | core/patterns.py | 未开始 | 未测试 | |

## 信号生成模块 (TASK-004)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| generate_trading_advice | stock_analyzer.py:352 | strategies/signals.py | 未开始 | 未测试 | |
| get_confidence_explanation | stock_analyzer.py:655 | strategies/signals.py | 未开始 | 未测试 | |

## 回测系统模块 (TASK-005)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| backtest_strategy | stock_analyzer.py:737 | strategies/backtest.py | 未开始 | 未测试 | |

## 报告生成模块 (TASK-006)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| generate_html_report | stock_analyzer.py:1215 | reports/html_generator.py | 未开始 | 未测试 | |

## 主类重构 (TASK-007)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| __init__ | stock_analyzer.py:28 | core/analyzer.py | 未开始 | 未测试 | |
| setup_logging | stock_analyzer.py:33 | core/analyzer.py | 未开始 | 未测试 | |
| setup_paths | stock_analyzer.py:46 | core/analyzer.py | 未开始 | 未测试 | |
| setup_colors | stock_analyzer.py:50 | core/analyzer.py | 未开始 | 未测试 | |
| analyze_stocks | stock_analyzer.py:1147 | core/analyzer.py | 未开始 | 未测试 | |
| clean_reports | stock_analyzer.py:1816 | core/analyzer.py | 未开始 | 未测试 | |
| show_clean_menu | stock_analyzer.py:1872 | core/analyzer.py | 未开始 | 未测试 | |

## 兼容层实现 (TASK-008)

| 函数/方法 | 源文件位置 | 目标位置 | 状态 | 测试状态 | 备注 |
|----------|-----------|---------|------|---------|------|
| StockAnalyzer类 | - | stock_analyzer.py | 未开始 | 未测试 | 作为兼容层封装新架构 |

## 总体进度
- 总函数/方法数: 16
- 已迁移数: 0
- 已测试数: 0
- 已验证数: 0
- 完成百分比: 0%

---
*最后更新: 2025-03-13 06:20:00 PDT* 