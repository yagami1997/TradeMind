#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间戳更新脚本
自动更新项目中所有文档的时间戳
"""

import os
import re
import subprocess
import datetime
import pytz
from pathlib import Path

def get_current_timestamp():
    """获取当前的时间戳"""
    result = subprocess.run(['python', 'scripts/generate_timestamp.py', 'full'], 
                           capture_output=True, text=True)
    return result.stdout.strip()

def update_file_timestamp(file_path, timestamp):
    """更新文件中的时间戳"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 标记是否找到并更新了时间戳
    updated = False
    
    # 更新文件顶部的时间戳
    if re.search(r'\*\*最后更新\*\*: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T', content):
        content = re.sub(r'\*\*最后更新\*\*: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T', 
                        f'**最后更新**: {timestamp}', content)
        updated = True
    
    # 更新文件底部的时间戳
    if re.search(r'\*最后更新: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T\*', content):
        content = re.sub(r'\*最后更新: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T\*', 
                        f'*最后更新: {timestamp}*', content)
        updated = True
    elif re.search(r'\*生成时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T\*', content):
        content = re.sub(r'\*生成时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T\*', 
                        f'*生成时间：{timestamp}*', content)
        updated = True
    elif re.search(r'\*发布于: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T\*', content):
        content = re.sub(r'\*发布于: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T\*', 
                        f'*发布于: {timestamp}*', content)
        updated = True
    
    # 更新"最后更新"部分的时间戳
    if re.search(r'## 最后更新\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T', content):
        content = re.sub(r'## 最后更新\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T', 
                        f'## 最后更新\n{timestamp}', content)
        updated = True
    
    # 更新发布日期
    if re.search(r'### 发布日期\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T', content):
        content = re.sub(r'### 发布日期\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T', 
                        f'### 发布日期\n{timestamp}', content)
        updated = True
    
    # 更新README.md特殊格式
    if re.search(r'<span style="font-size: 14px; color: #888;">\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T</span>', content):
        content = re.sub(r'<span style="font-size: 14px; color: #888;">\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[DS]T</span>', 
                        f'<span style="font-size: 14px; color: #888;">{timestamp}</span>', content)
        updated = True
    
    # 如果没有找到任何时间戳格式，在文件末尾添加生成时间
    if not updated and not content.strip().endswith(f'*生成时间：{timestamp}*'):
        if content.endswith('\n'):
            content += f'\n*生成时间：{timestamp}*'
        else:
            content += f'\n\n*生成时间：{timestamp}*'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已更新: {file_path}")

def find_markdown_files(directory):
    """查找目录中的所有Markdown文件"""
    markdown_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    return markdown_files

def main():
    """主函数"""
    # 获取当前时间戳
    timestamp = get_current_timestamp()
    print(f"当前时间戳: {timestamp}")
    
    # 项目根目录
    root_dir = Path(__file__).parent.parent
    
    # 需要更新的目录
    directories = [
        os.path.join(root_dir, 'project_management'),
        os.path.join(root_dir, 'docs'),
    ]
    
    # 需要更新的单独文件
    individual_files = [
        os.path.join(root_dir, 'README.md'),
        os.path.join(root_dir, 'PROJECT_PROGRESS.md'),
        os.path.join(root_dir, 'RELEASE_NOTES.md'),
    ]
    
    # 更新目录中的所有Markdown文件
    for directory in directories:
        if os.path.exists(directory):
            markdown_files = find_markdown_files(directory)
            for file_path in markdown_files:
                update_file_timestamp(file_path, timestamp)
    
    # 更新单独的文件
    for file_path in individual_files:
        if os.path.exists(file_path):
            update_file_timestamp(file_path, timestamp)
    
    print("所有文档的时间戳已更新完成！")

if __name__ == "__main__":
    main() 