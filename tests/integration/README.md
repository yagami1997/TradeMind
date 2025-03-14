# TradeMind Lite 集成测试

本目录包含TradeMind Lite（轻量版）的集成测试，用于验证系统各组件的协同工作能力。

## 测试文件说明

- `test_end_to_end.py`: 端到端集成测试，验证完整的分析流程
- `test_batch_analysis.py`: 多股票批量分析测试，验证系统处理大量股票数据的能力
- `test_performance_benchmark.py`: 性能基准测试，测量系统在不同条件下的性能表现
- `run_integration_tests.py`: 集成测试运行器，用于执行所有集成测试并生成报告

## 运行测试

### 运行所有集成测试

```bash
python tests/integration/run_integration_tests.py
```

### 运行特定测试

```bash
python tests/integration/run_integration_tests.py --test test_end_to_end
```

### 指定输出目录

```bash
python tests/integration/run_integration_tests.py --output custom_results
```

## 测试报告

测试完成后，会在指定的输出目录（默认为`test_results`）生成以下报告：

- `integration_test_report.json`: JSON格式的测试结果
- `integration_test_report.html`: HTML格式的测试报告，包含可视化的测试结果

## 性能测试结果

性能测试会在`test_results/results`目录下生成以下文件：

- `performance_results.json`: 性能测试结果数据
- `performance_chart.png`: 性能测试结果图表
- `component_time_pie.png`: 各组件执行时间占比饼图

## 注意事项

1. 运行集成测试前，请确保已安装所有依赖包
2. 性能测试可能需要较长时间，请耐心等待
3. 如果测试失败，请查看测试报告中的详细错误信息
 