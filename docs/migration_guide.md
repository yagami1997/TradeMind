# TradeMind Lite 迁移指南

本指南将帮助您将代码从旧版 TradeMind Lite 迁移到新的模块化结构。

## 迁移概述

TradeMind Lite v2.0 进行了重大架构改进，将原来的单一 `StockAnalyzer` 类拆分为多个专门的模块。这种模块化结构带来了以下好处：

- 更好的代码组织和可维护性
- 更灵活的功能组合
- 更容易进行单元测试
- 更清晰的依赖关系

为了确保平滑迁移，我们提供了兼容层，允许现有代码继续使用旧版接口。但是，我们建议您尽快迁移到新的模块化接口，因为兼容层将在未来版本中移除。

## 导入变更

### 旧版导入

```python
from stock_analyzer import StockAnalyzer, TechnicalPattern
```

### 兼容层导入（临时过渡）

```python
from trademind.compat import StockAnalyzer, TechnicalPattern
```

### 新版导入（推荐）

```python
from trademind.core.analyzer import StockAnalyzer
from trademind.core.patterns import TechnicalPattern
from trademind.core.indicators import calculate_rsi, calculate_macd, calculate_kdj, calculate_bollinger_bands
from trademind.core.signals import generate_trading_advice, generate_signals
from trademind.backtest.engine import run_backtest
from trademind.reports.generator import generate_html_report, generate_performance_charts
```

## 方法映射

下表显示了旧版方法与新版方法的对应关系：

| 旧版方法 | 新版方法 |
|---------|---------|
| `StockAnalyzer.identify_candlestick_patterns()` | `trademind.core.patterns.identify_candlestick_patterns()` |
| `StockAnalyzer.calculate_rsi()` | `trademind.core.indicators.calculate_rsi()` |
| `StockAnalyzer.calculate_macd()` | `trademind.core.indicators.calculate_macd()` |
| `StockAnalyzer.calculate_kdj()` | `trademind.core.indicators.calculate_kdj()` |
| `StockAnalyzer.calculate_bollinger_bands()` | `trademind.core.indicators.calculate_bollinger_bands()` |
| `StockAnalyzer.generate_trading_advice()` | `trademind.core.signals.generate_trading_advice()` |
| `StockAnalyzer.generate_signals()` | `trademind.core.signals.generate_signals()` |
| `StockAnalyzer.backtest_strategy()` | `trademind.backtest.engine.run_backtest()` |
| `StockAnalyzer.analyze_stocks()` | `StockAnalyzer.analyze_stocks()` |
| `StockAnalyzer.generate_report()` | `StockAnalyzer.generate_report()` |
| `StockAnalyzer.analyze_and_report()` | `StockAnalyzer.analyze_and_report()` |
| `StockAnalyzer.clean_reports()` | `StockAnalyzer.clean_reports()` |

## 代码示例

### 旧版代码

```python
from stock_analyzer import StockAnalyzer

# 创建分析器实例
analyzer = StockAnalyzer()

# 分析股票
symbols = ['AAPL', 'MSFT', 'GOOGL']
names = {'AAPL': '苹果公司', 'MSFT': '微软公司', 'GOOGL': '谷歌公司'}
results = analyzer.analyze_stocks(symbols, names)

# 生成报告
report_path = analyzer.generate_report(results, "股票分析报告")
```

### 新版代码

```python
from trademind.core.analyzer import StockAnalyzer

# 创建分析器实例
analyzer = StockAnalyzer()

# 分析股票
symbols = ['AAPL', 'MSFT', 'GOOGL']
names = {'AAPL': '苹果公司', 'MSFT': '微软公司', 'GOOGL': '谷歌公司'}
results = analyzer.analyze_stocks(symbols, names)

# 生成报告
report_path = analyzer.generate_report(results, "股票分析报告")
```

### 使用单独模块的新版代码

```python
import yfinance as yf
import pandas as pd
from trademind.core.indicators import calculate_rsi, calculate_macd, calculate_kdj, calculate_bollinger_bands
from trademind.core.patterns import identify_candlestick_patterns
from trademind.core.signals import generate_trading_advice, generate_signals
from trademind.backtest.engine import run_backtest
from trademind.reports.generator import generate_html_report

# 获取股票数据
symbol = 'AAPL'
stock = yf.Ticker(symbol)
hist = stock.history(period="1y")

# 计算技术指标
rsi = calculate_rsi(hist['Close'])
macd, signal, hist_macd = calculate_macd(hist['Close'])
k, d, j = calculate_kdj(hist['High'], hist['Low'], hist['Close'])
bb_upper, bb_middle, bb_lower, bb_width, bb_percent = calculate_bollinger_bands(hist['Close'])

# 识别K线形态
patterns = identify_candlestick_patterns(hist.tail(5))

# 整合指标
indicators = {
    'rsi': rsi,
    'macd': {'macd': macd, 'signal': signal, 'hist': hist_macd},
    'kdj': {'k': k, 'd': d, 'j': j},
    'bollinger': {
        'upper': bb_upper, 
        'middle': bb_middle, 
        'lower': bb_lower,
        'bandwidth': bb_width,
        'percent_b': bb_percent
    }
}

# 生成交易建议
advice = generate_trading_advice(indicators, hist['Close'].iloc[-1], patterns)

# 生成交易信号
signals = generate_signals(hist, indicators)

# 回测策略
backtest_results = run_backtest(hist, signals)

# 整合结果
result = {
    'symbol': symbol,
    'name': '苹果公司',
    'price': hist['Close'].iloc[-1],
    'change': ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100,
    'indicators': indicators,
    'patterns': patterns,
    'advice': advice,
    'backtest': backtest_results
}

# 生成报告
report_path = generate_html_report([result], "苹果公司分析报告")
```

## 常见问题

### 我需要立即迁移吗？

不需要立即迁移。兼容层允许您继续使用旧版接口，但会发出废弃警告。我们建议您在方便时逐步迁移到新的模块化接口。

### 如何处理废弃警告？

如果您暂时不想看到废弃警告，可以使用以下代码禁用它们：

```python
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
```

但是，我们建议您不要忽略这些警告，而是尽快迁移到新的模块化接口。

### 新版接口与旧版接口有什么不同？

新版接口在功能上与旧版接口相同，但是组织结构更加模块化。主要区别在于：

- 技术指标计算、形态识别、信号生成等功能被拆分到专门的模块中
- 函数签名和返回值保持不变，确保兼容性
- 新增了更多的文档和类型提示，提高了代码可读性

### 迁移后性能会有变化吗？

迁移到新的模块化接口不会对性能产生显著影响。事实上，由于代码组织更加清晰，某些情况下可能会有轻微的性能改进。

## 获取帮助

如果您在迁移过程中遇到任何问题，请通过以下方式获取帮助：

- 查阅[完整文档](https://trademind-lite.docs/)
- 提交[GitHub Issue](https://github.com/trademind/trademind-lite/issues)
- 发送邮件至 support@trademind-lite.com

---

*最后更新: 2025-03-14* 

*生成时间：2025-03-19 18:46:03 PDT*