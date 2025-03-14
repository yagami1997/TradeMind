#!/usr/bin/env python3
"""
TradeMind Lite - Web入口点

本脚本是TradeMind Lite的Web入口点，用于启动Web界面。
"""

import argparse
import sys
import os
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED
from rich import box
from rich.style import Style
from rich.align import Align

from trademind.ui.web import run_web_server
from trademind import __version__

# 创建Rich控制台
console = Console()

def setup_logging():
    """设置日志记录"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "trademind_web.log"), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("trademind_web")

def print_banner():
    """
    打印TradeMind Lite的ASCII复古风标题
    """
    # 创建单行ASCII风格标题
    banner = r"""
 _____           _      __  __ _           _   _     _ _       
|_   _|_ _ _ __ | | ___|  \/  (_)_ __   __| | | |   (_) |_ ___ 
  | |/ _` | '_ \| |/ _ \ |\/| | | '_ \ / _` | | |   | | __/ _ \
  | | (_| | | | | |  __/ |  | | | | | | (_| | | |___| | ||  __/
  |_|\__,_|_| |_|_|\___|_|  |_|_|_| |_|\__,_| |_____|_|\__\___|
"""
    
    # 创建面板，使用适当的宽度
    panel = Panel(
        Text(banner, style="bold cyan"),
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
        width=70
    )
    
    # 打印面板
    console.print(Align.center(panel))
    
    # 打印版本和作者信息
    info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2), width=70)
    info_table.add_column("Key", style="cyan", width=10)
    info_table.add_column("Value", style="green")
    
    info_table.add_row("版本", f"Beta {__version__}")
    info_table.add_row("作者", "Yagami")
    info_table.add_row("仓库", "https://github.com/yagami1997/TradeMind")
    info_table.add_row("许可证", "GPL-3.0")
    info_table.add_row("Web模式", "启动中...")
    
    console.print(Align.center(info_table))
    console.print()

def show_main_menu():
    """显示主菜单"""
    # 创建菜单表格
    menu_table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        border_style="cyan",
        width=70,
        padding=(0, 2)
    )
    
    # 添加列
    menu_table.add_column("选项", style="yellow", width=6)
    menu_table.add_column("功能", style="green", width=15)
    menu_table.add_column("描述", style="white")
    
    # 添加菜单项
    menu_table.add_row("1", "命令行模式", "交互式命令行界面，适合脚本操作")
    menu_table.add_row("2", "Web模式", "图形化Web界面，提供完整功能")
    menu_table.add_row("q", "退出程序", "结束程序运行")
    
    # 打印标题
    console.print("\n")
    console.print(Panel(
        Text("TradeMind Lite 主菜单", style="bold cyan", justify="center"),
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2),
        width=70
    ))
    console.print("\n")
    
    # 打印菜单表格
    console.print(Align.center(menu_table))
    console.print("\n")
    
    while True:
        choice = console.input("[cyan]请选择操作[/cyan] [[yellow]1[/yellow]/[yellow]2[/yellow]/[yellow]q[/yellow]]: ").strip().lower()
        if choice in ['1', '2', 'q']:
            return choice
        console.print("[red]无效的选择，请重试[/red]")

def main():
    """主函数"""
    try:
        while True:
            choice = show_main_menu()
            
            if choice == 'q':
                console.print("\n[green]感谢使用 TradeMind Lite！[/green]")
                break
            elif choice == '1':
                # 命令行模式
                from trademind.cli import run_cli
                run_cli()
            elif choice == '2':
                # Web模式
                from trademind.ui.web import run_web_server
                run_web_server(port=3336)
                
    except KeyboardInterrupt:
        console.print("\n\n[yellow]程序已终止[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]程序运行出错: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 