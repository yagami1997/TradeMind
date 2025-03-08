# TradeMind 主控制文档

## 时间戳规范
- 所有时间戳格式：[PST:YYYY-MM-DD HH:mm:ss]
- 使用 PST（美国太平洋时间）作为标准时区
- 自动化时间检查：time_check.sh
- NTP 服务器同步：pool.ntp.org

## 文档信息
- 创建时间：[PST:2025-02-28 20:15:11]
- 最后更新：[PST:2025-03-04 21:57:55]
- 文档状态：活跃
- 版本控制：Git
- 分支策略：dev（开发分支，后续合并至main）

## 时间管理原则
1. 所有时间记录必须包含时区信息
2. 定期与 NTP 服务器同步
3. 提交前强制时间检查
4. 保持时间戳的一致性和准确性

> 注意：详细的日常开发记录请查看reports目录下的日报文件（DAILY_LOG_YYYY-MM-DD.md），周度总结请查看reports目录下的周报文件（WEEKLY_LOG_YYYY-MM-DD.md）

## 月度工作总结

### 2025年3月总结
#### 1. 重大进展
- 优化了回测系统的滑点模型
- 实现了并行处理框架
- 重构了回测主流程
- 提高了代码质量和系统性能

#### 2. 技术改进
- 实现了基于成交量的动态滑点计算
- 添加了线程池管理类和并行数据处理方法
- 优化了回测流程和错误处理机制
- 完善了系统集成和兼容性

#### 3. 架构优化
- 添加了`SlippageConfig`数据类
- 实现了`ThreadPoolManager`类
- 优化了模块间的接口和数据交换
- 保持了系统的稳定性和一致性

#### 4. 质量保证
- 全面的错误捕获和处理
- 详细的日志记录
- 优雅的恢复机制
- 完善的类型注解

#### 5. 遗留任务
- 滑点模型参数校准
- 并行处理在极端数据量下的稳定性测试
- 线程池资源管理优化
- 性能瓶颈分析

### 2025年2月总结
#### 1. 重大进展
- 完成了Alpha 0.3.0版本的核心功能开发
- 建立了完整的项目文档体系
- 实现了关键模块的错误处理机制

#### 2. 技术改进
- 实施了基于NTP的时间同步系统
- 优化了数据缓存架构
- 改进了回测报告生成系统

#### 3. 架构优化
- 确定了核心模块的最终结构
- 优化了模块间的依赖关系
- 建立了清晰的分层架构

#### 4. 质量保证
- 完善了异常处理机制
- 建立了完整的日志系统
- 优化了代码结构和导入关系

#### 5. 遗留任务
- 缓存生命周期管理
- 并发处理优化
- 性能瓶颈评估

#### 6. 下月计划
- 完成Alpha 0.4.0版本开发
- 实现所有核心模块功能
- 建立完整的模块测试体系
- 优化模块间的集成
- 完善错误处理机制
- 实现基础性能优化

## 项目基本信息
- 项目名称：TradeMind Dev重构版
- 当前版本：Alpha 0.3.0
- 开发阶段：优化重构期
- 计划发布：2025-05-27（PST）

## 核心架构定义（锁定）
### 1. 目录结构
```
core/                           # 核心功能模块
├── __init__.py               # 模块初始化
├── technical_analyzer.py      # [锁定] 技术分析核心
├── market_types.py           # [锁定] 基础类型定义
├── exceptions.py             # [锁定] 异常处理体系
├── data_source.py           # [锁定] 数据源抽象接口
├── market_sources.py         # [优化] 市场数据源实现
├── backtest_manager.py       # [优化] 回测系统管理
├── strategy_manager.py       # [优化] 策略管理系统
├── data_source_factory.py    # [优化] 数据源工厂
├── data_manager.py          # [优化] 数据管理系统
├── market_calendar.py        # [锁定] 市场日历
└── config.py                # [锁定] 核心配置

strategies/                    # 策略相关模块
├── __init__.py              # 模块初始化
├── backtester.py            # 回测器实现
├── tech_indicator_calculator.py # 技术指标计算器
├── advanced_analysis.py     # 高级分析工具
├── enhanced_trading_advisor.py # 增强型交易顾问
└── stock_analyzer.py        # 股票分析器

data/                        # 数据管理模块
├── __init__.py             # 模块初始化
├── README.md               # 数据说明文档
├── data_manager_ibkr.py    # IBKR数据管理器
├── data_manager_yf.py      # YFinance数据管理器
├── cache/                  # 缓存数据
│   ├── fundamental/        # 基本面数据缓存
│   └── technical/         # 技术面数据缓存
├── downloads/             # 下载文件
└── market_data/          # 市场数据
    ├── indices/          # 指数数据
    └── stocks/          # 股票数据
        ├── daily/      # 日线数据
        └── minute/    # 分钟数据

config/                     # 配置文件目录
├── config.ini             # 主配置文件
├── config.ini.example     # 配置文件示例
├── analysis_config.ini    # 分析配置
├── logging.ini           # 日志配置
├── report_templates.json # 报告模板配置
└── watchlists.json      # 监视列表配置

logs/                      # 日志目录
├── README.md             # 日志说明文档
├── system/              # 系统日志
│   ├── info/           # 信息日志
│   └── error/         # 错误日志
├── trading/            # 交易日志
│   ├── info/          # 信息日志
│   └── error/        # 错误日志
└── backtest/          # 回测日志
    ├── info/         # 信息日志
    └── error/       # 错误日志

reports/                 # 报告目录
├── templates/          # 报告模板
│   ├── html/         # HTML模板
│   │   ├── base.html           # 基础模板
│   │   ├── analysis_report.html # 分析报告模板
│   │   └── backtest_report.html # 回测报告模板
│   └── css/          # 样式表
│       ├── main.css  # 主样式表
│       └── charts.css # 图表样式表
└── output/           # 输出报告
    ├── analysis/    # 分析报告
    └── backtest/   # 回测报告

results/              # 结果目录
├── analysis/        # 分析结果
│   ├── signals/    # 信号结果
│   └── technical/ # 技术分析结果
├── backtest/       # 回测结果
│   ├── metrics/   # 指标结果
│   └── trades/   # 交易记录
└── trading/       # 交易结果

tests/              # 测试目录
├── unit/          # 单元测试
│   ├── analysis/  # 分析模块测试
│   │   ├── __init__.py
│   │   └── test_analysis.py
│   └── strategies/ # 策略模块测试
│       ├── __init__.py
│       ├── test_analyzer.py
│       └── test_backtester.py
└── integration/   # 集成测试
    ├── analysis/  # 分析模块测试
    └── strategies/ # 策略模块测试

utils/             # 工具目录
├── __init__.py   # 模块初始化
├── formatters.py # 格式化工具
├── helpers.py    # 辅助函数
└── validators.py # 验证工具

watchlist/         # 监视列表目录
└── watchlist_manager.py # 监视列表管理器

# 核心文件
main.py           # 主程序入口
requirements.txt  # 依赖管理
setup.py         # 安装配置
.env.example     # 环境变量示例
time_check.sh    # 时间检查脚本
```

### 2. 系统架构
1. **数据流向**：
   ```
   market_sources → data_manager → technical_analyzer → strategy_manager → backtest_manager
   ```

2. **模块职责**：
   - 数据层：data_source, market_sources, data_manager
   - 分析层：technical_analyzer, tech_indicator_calculator
   - 策略层：strategy_manager
   - 执行层：backtest_manager

## 重大技术决策记录

### 1. 架构决策
#### [PST:2025-02-28] 技术分析模块分离
- 决策：保持tech_indicator_calculator.py在strategies/目录
- 原因：
  * 职责分离：基础分析与策略分析分开
  * 维持现有架构：避免不必要的重构
  * 扩展性考虑：便于后续添加新策略
- 状态：永久性决策

### 2. 性能优化决策
#### [PST:2025-02-28] 缓存系统架构
- 决策：采用文件缓存系统
- 原因：
  * 持久化需求
  * 内存效率
  * 系统可靠性
- 影响：需要缓存生命周期管理机制
- 状态：已实施

### 3. 开发流程决策
#### [PST:2025-02-28] 时间同步管理
- 决策：实现自动化时间检查系统
- 机制：Git pre-commit hook + NTP检查
- 状态：已完成并采用

## 架构评估备忘录

### 1. 模块耦合度评估
- 评估日期：[PST:2025-02-28]
- 结论：保持现有耦合度
- 理由：
  * 当前耦合度适中
  * 变更成本高于收益
  * 现有结构满足扩展需求
- 后续：持续监控模块间依赖

## 关键里程碑
1. Alpha 0.3.0 [当前]
   - 核心功能完成
   - 基础架构稳定
   - 开发流程规范化

2. Beta 0.1.0 [计划]
   - 回测系统完善
   - 性能优化完成
   - 并发处理优化

## 架构原则（固定）
1. **模块化原则**
   - 高内聚，低耦合
   - 接口优先设计
   - 依赖注入模式

2. **扩展性原则**
   - 开放封闭原则
   - 策略模式应用
   - 工厂模式封装

3. **可维护性原则**
   - 代码结构稳定
   - 接口向后兼容
   - 充分的异常处理

## 系统风险追踪
1. **架构风险**
   - 模块耦合度控制
   - 扩展性保证
   - 性能瓶颈

2. **技术债务**
   - 缓存优化需求
   - 并发处理优化
   - 错误处理完善

## 最后更新
- 日期：[PST:2025-03-04 21:57:55]
- 更新内容：完善目录结构，更新所有模块说明
- 下次评估：系统扩展性评估