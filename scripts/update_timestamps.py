#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TradeMind Lite 文档时间戳更新脚本
自动更新项目文档中的时间戳
"""

import os
import re
import sys
import subprocess
from datetime import datetime

# 需要更新时间戳的文档目录
DOC_DIRECTORIES = [
    "project_management",
    "project_management/actuals",
    "project_management/actuals/tasks",
]

# 需要更新的文件类型
FILE_EXTENSIONS = [".md"]

# 时间戳正则表达式模式
TIMESTAMP_PATTERNS = [
    r"## 时间\n.*\n",  # 匹配文档顶部的时间字段
    r"\*最后更新: .*\*"  # 匹配文档底部的最后更新字段
]


def get_current_timestamp():
    """获取当前时间戳，使用generate_timestamp.py脚本"""
    try:
        result = subprocess.run(
            ["python", "scripts/generate_timestamp.py"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"错误: 无法生成时间戳: {e}")
        sys.exit(1)


def update_file_timestamps(file_path, timestamp):
    """更新文件中的时间戳"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 更新顶部时间字段
        content = re.sub(
            r"## 时间\n.*\n",
            f"## 时间\n{timestamp}\n",
            content
        )
        
        # 更新底部最后更新字段
        content = re.sub(
            r"\*最后更新: .*\*",
            f"*最后更新: {timestamp}*",
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return True
    except Exception as e:
        print(f"错误: 更新文件 {file_path} 时出错: {e}")
        return False


def find_and_update_docs(root_dir, timestamp):
    """查找并更新所有文档中的时间戳"""
    updated_files = []
    failed_files = []
    
    for doc_dir in DOC_DIRECTORIES:
        dir_path = os.path.join(root_dir, doc_dir)
        if not os.path.exists(dir_path):
            print(f"警告: 目录不存在: {dir_path}")
            continue
        
        for file_name in os.listdir(dir_path):
            if any(file_name.endswith(ext) for ext in FILE_EXTENSIONS):
                file_path = os.path.join(dir_path, file_name)
                print(f"更新文件: {file_path}")
                
                if update_file_timestamps(file_path, timestamp):
                    updated_files.append(file_path)
                else:
                    failed_files.append(file_path)
    
    return updated_files, failed_files


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    # 获取当前时间戳
    timestamp = get_current_timestamp()
    print(f"当前时间戳: {timestamp}")
    
    # 更新文档时间戳
    updated_files, failed_files = find_and_update_docs(root_dir, timestamp)
    
    # 打印结果
    print("\n更新结果:")
    print(f"成功更新: {len(updated_files)} 个文件")
    if failed_files:
        print(f"更新失败: {len(failed_files)} 个文件")
        for file in failed_files:
            print(f"  - {file}")
    
    print("\n完成!")


if __name__ == "__main__":
    main() 