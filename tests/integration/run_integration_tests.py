#!/usr/bin/env python
"""
TradeMind Lite（轻量版）- 集成测试运行器

本脚本用于运行TradeMind Lite的所有集成测试，并生成测试报告。
"""

import os
import sys
import unittest
import time
import argparse
from datetime import datetime
import json
from pathlib import Path
import importlib
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def discover_tests(test_dir, pattern='test_*.py'):
    """发现指定目录下的所有测试文件"""
    test_loader = unittest.TestLoader()
    return test_loader.discover(test_dir, pattern=pattern)


def run_tests(test_suite, verbosity=2):
    """运行测试套件并返回结果"""
    test_runner = unittest.TextTestRunner(verbosity=verbosity)
    return test_runner.run(test_suite)


def generate_report(result, start_time, end_time, output_dir):
    """生成测试报告"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 收集测试结果
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    success = tests_run - failures - errors - skipped
    
    # 计算测试时间
    duration = end_time - start_time
    
    # 创建报告数据
    report_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": f"{duration:.2f}秒",
        "tests_run": tests_run,
        "success": success,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "success_rate": f"{(success / tests_run * 100):.2f}%" if tests_run > 0 else "0%",
        "details": {
            "failures": [
                {
                    "test": f"{failure[0]}",
                    "message": str(failure[1])
                }
                for failure in result.failures
            ],
            "errors": [
                {
                    "test": f"{error[0]}",
                    "message": str(error[1])
                }
                for error in result.errors
            ],
            "skipped": [
                {
                    "test": f"{skip[0]}",
                    "reason": str(skip[1])
                }
                for skip in result.skipped
            ]
        }
    }
    
    # 保存报告为JSON
    report_file = os.path.join(output_dir, "integration_test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    # 生成HTML报告
    html_report = generate_html_report(report_data)
    html_file = os.path.join(output_dir, "integration_test_report.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    return report_file, html_file


def generate_html_report(report_data):
    """生成HTML格式的测试报告"""
    # 定义HTML模板
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradeMind Lite 集成测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .header {{
            background-color: #3498db;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .summary {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background-color: white;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 200px;
            margin: 10px;
            text-align: center;
        }}
        .success {{ background-color: #2ecc71; color: white; }}
        .failure {{ background-color: #e74c3c; color: white; }}
        .error {{ background-color: #f39c12; color: white; }}
        .skipped {{ background-color: #95a5a6; color: white; }}
        
        .details {{
            background-color: white;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .test-item {{
            border-left: 4px solid #3498db;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }}
        .test-item.failure {{
            border-left-color: #e74c3c;
        }}
        .test-item.error {{
            border-left-color: #f39c12;
        }}
        .test-item.skipped {{
            border-left-color: #95a5a6;
        }}
        pre {{
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .progress-bar {{
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            margin: 20px 0;
            overflow: hidden;
        }}
        .progress {{
            height: 100%;
            background-color: #2ecc71;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TradeMind Lite 集成测试报告</h1>
        <p>生成时间: {timestamp}</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <h3>测试总数</h3>
            <p style="font-size: 24px;">{tests_run}</p>
        </div>
        <div class="summary-card success">
            <h3>成功</h3>
            <p style="font-size: 24px;">{success}</p>
        </div>
        <div class="summary-card failure">
            <h3>失败</h3>
            <p style="font-size: 24px;">{failures}</p>
        </div>
        <div class="summary-card error">
            <h3>错误</h3>
            <p style="font-size: 24px;">{errors}</p>
        </div>
        <div class="summary-card skipped">
            <h3>跳过</h3>
            <p style="font-size: 24px;">{skipped}</p>
        </div>
    </div>
    
    <div class="details">
        <h2>测试结果摘要</h2>
        <p>测试执行时间: {duration}</p>
        <p>成功率: {success_rate}</p>
        
        <div class="progress-bar">
            <div class="progress" style="width: {success_rate};">{success_rate}</div>
        </div>
        
        <h3>失败的测试 ({failures})</h3>
        {failures_details}
        
        <h3>错误的测试 ({errors})</h3>
        {errors_details}
        
        <h3>跳过的测试 ({skipped})</h3>
        {skipped_details}
    </div>
    
    <div class="footer">
        <p>TradeMind Lite 集成测试系统 &copy; 2025</p>
    </div>
</body>
</html>
"""
    
    # 生成失败测试详情
    failures_details = ""
    for failure in report_data["details"]["failures"]:
        failures_details += f"""
        <div class="test-item failure">
            <h4>{failure["test"]}</h4>
            <pre>{failure["message"]}</pre>
        </div>
        """
    if not failures_details:
        failures_details = "<p>没有失败的测试</p>"
    
    # 生成错误测试详情
    errors_details = ""
    for error in report_data["details"]["errors"]:
        errors_details += f"""
        <div class="test-item error">
            <h4>{error["test"]}</h4>
            <pre>{error["message"]}</pre>
        </div>
        """
    if not errors_details:
        errors_details = "<p>没有错误的测试</p>"
    
    # 生成跳过测试详情
    skipped_details = ""
    for skip in report_data["details"]["skipped"]:
        skipped_details += f"""
        <div class="test-item skipped">
            <h4>{skip["test"]}</h4>
            <p>原因: {skip["reason"]}</p>
        </div>
        """
    if not skipped_details:
        skipped_details = "<p>没有跳过的测试</p>"
    
    # 填充模板
    html_report = html_template.format(
        timestamp=report_data["timestamp"],
        tests_run=report_data["tests_run"],
        success=report_data["success"],
        failures=report_data["failures"],
        errors=report_data["errors"],
        skipped=report_data["skipped"],
        success_rate=report_data["success_rate"],
        duration=report_data["duration"],
        failures_details=failures_details,
        errors_details=errors_details,
        skipped_details=skipped_details
    )
    
    return html_report


def run_specific_test(test_name):
    """运行指定的测试模块"""
    try:
        # 尝试导入测试模块
        module_name = f"tests.integration.{test_name}"
        test_module = importlib.import_module(module_name)
        
        # 加载测试
        test_loader = unittest.TestLoader()
        test_suite = test_loader.loadTestsFromModule(test_module)
        
        # 运行测试
        print(f"运行测试: {test_name}")
        return run_tests(test_suite)
    except ImportError:
        print(f"错误: 无法导入测试模块 {test_name}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"错误: 运行测试 {test_name} 时发生异常")
        traceback.print_exc()
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradeMind Lite 集成测试运行器")
    parser.add_argument("--test", help="指定要运行的测试模块名称（不含.py扩展名）")
    parser.add_argument("--output", default="test_results", help="测试报告输出目录")
    parser.add_argument("--verbosity", type=int, default=2, help="测试输出详细程度 (1-3)")
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = time.time()
    
    # 确定测试目录
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 运行测试
    if args.test:
        # 运行指定的测试
        result = run_specific_test(args.test)
        if result is None:
            return 1
    else:
        # 运行所有集成测试
        print("发现集成测试...")
        test_suite = discover_tests(test_dir)
        print(f"发现 {test_suite.countTestCases()} 个测试用例")
        
        print("\n开始运行集成测试...")
        result = run_tests(test_suite, verbosity=args.verbosity)
    
    # 记录结束时间
    end_time = time.time()
    
    # 生成报告
    output_dir = os.path.join(os.path.dirname(test_dir), "..", args.output)
    report_file, html_file = generate_report(result, start_time, end_time, output_dir)
    
    # 输出结果摘要
    print("\n测试完成!")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    print(f"总耗时: {end_time - start_time:.2f}秒")
    print(f"\n测试报告已保存到:")
    print(f"- JSON: {report_file}")
    print(f"- HTML: {html_file}")
    
    # 返回状态码
    return 0 if len(result.failures) == 0 and len(result.errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main()) 