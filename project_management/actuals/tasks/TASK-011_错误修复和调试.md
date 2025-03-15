# 任务：错误修复和调试

## 基本信息
- **任务ID**: TASK-011
- **任务名称**: 错误修复和调试
- **创建日期**: 2025-03-14
- **截止日期**: 2025-03-14
- **优先级**: 高
- **状态**: ✅ 已完成
- **负责人**: 开发团队
- **时间戳**: 2025-03-14 22:30:15 PDT

## 任务描述
对系统中发现的多个错误进行修复和调试，确保系统稳定性和用户体验。

## 详细需求

### 1. 报告生成器KeyError修复
- 修复报告生成器中的KeyError: 'explanation'问题
- 在`generate_stock_card_html`函数中添加对'explanation'键的检查
- 如果键不存在，使用默认值'无详细解释'
- 确保报告生成过程不会因为数据结构不完整而中断

### 2. K线形态指标显示修复
- 修复命令行模式下K线形态指标不显示的问题
- 统一命令行和Web模式的K线形态数据处理路径
- 修改`trademind/core/analyzer.py`中的`analyze_stocks`方法
- 修改`trademind/core/signals.py`中的`generate_trading_advice`函数
- 确保两种模式下都能正确显示K线形态

### 3. Sortino比率显示优化
- 修复Sortino比率显示异常的问题
- 在`trademind/backtest/engine.py`中修改Sortino比率的计算逻辑
- 使用对数缩放处理异常大的值
- 添加对NaN和无穷大值的检查
- 优化无下行风险情况下的处理逻辑

### 4. 项目结构优化
- 清理项目结构，移除根目录下的多余文件
- 确保`MAIN_CONTROL.md`和`REQUIREMENTS.md`文件只存在于`project_management/control`目录下
- 从Git仓库中移除根目录下的这些文件

### 5. Web界面删除报告功能修复
- 修复Web界面的删除所有报告功能
- 修改`clean_reports`函数，使其清理`analyzer.results_path`目录
- 确保正确清理`reports/stocks`目录而不是根目录下的`reports`文件夹

### 6. 浏览器关闭事件检测问题修复
- 修复浏览器关闭事件检测不可靠的问题
- 使用`beforeunload`事件结合`navigator.sendBeacon()`方法
- 确保在浏览器关闭过程中能够可靠地发送请求

### 7. 命令处理阻塞问题修复
- 修复命令处理阻塞问题
- 将阻塞式输入修改为使用`select`模块实现非阻塞式输入检查
- 每秒检查一次输入和服务器状态

## 验收标准
1. 报告生成器能够正确处理缺少'explanation'键的情况
2. 命令行模式下能够正确显示K线形态指标
3. Sortino比率显示合理的数值，不再出现异常大的值
4. 项目结构清晰，根目录下没有多余文件
5. Web界面的删除报告功能能够正确清理报告目录
6. 浏览器关闭事件能够可靠地被检测到
7. 命令处理不再阻塞，能够及时响应服务器停止事件

## 相关文件
- `trademind/reports/generator.py`
- `trademind/core/analyzer.py`
- `trademind/core/signals.py`
- `trademind/backtest/engine.py`
- `trademind/ui/web.py`
- `trademind/ui/static/js/main.js`

## 依赖任务
- TASK-006_报告生成迁移
- TASK-003_形态识别迁移
- TASK-005_回测系统迁移
- TASK-009_主程序和用户界面开发

## 子任务
1. [x] 分析报告生成器KeyError问题
2. [x] 修复报告生成器KeyError问题
3. [x] 分析K线形态指标显示问题
4. [x] 修复K线形态指标显示问题
5. [x] 分析Sortino比率显示异常问题
6. [x] 修复Sortino比率显示异常问题
7. [x] 清理项目结构
8. [x] 修复Web界面删除报告功能
9. [x] 修复浏览器关闭事件检测问题
10. [x] 修复命令处理阻塞问题
11. [x] 测试所有修复
12. [x] 更新文档

## 备注
所有错误修复和调试工作已在2025-03-14完成，系统稳定性和用户体验得到显著提升。这些修复解决了在Beta 0.3.0版本测试中发现的所有关键问题。

## 变更记录
- 2025-03-14 22:30:15 PDT - 创建任务
- 2025-03-14 22:30:15 PDT - 标记任务为已完成 