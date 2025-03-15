#!/usr/bin/env python3
"""
TradeMind Lite - 主程序

本脚本是TradeMind Lite的主入口点，提供命令行和Web界面的访问。
"""

import argparse
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.box import ROUNDED
from rich import box
from rich.style import Style
from rich.align import Align

from trademind.ui.cli import run_interactive_mode
from trademind.ui.web import run_web_server
from trademind import __version__

# 创建Rich控制台
console = Console()

def print_banner():
    """
    打印TradeMind Lite的ASCII复古风标题
    """
    # 创建单行ASCII风格标题
    banner = """
 _____               _       __  __ _           _   _    _ _      
|_   _|_ __ __ _  __| | ___ |  \/  (_)_ __   __| | | |  (_) |_ ___ 
  | || '__/ _` |/ _` |/ _ \| |\/| | | '_ \ / _` | | |  | | __/ _ \\
  | || | | (_| | (_| |  __/| |  | | | | | | (_| | | |__| | ||  __/
  |_||_|  \__,_|\__,_|\___||_|  |_|_|_| |_|\__,_| |_____/ \__\___|
"""
    
    # 创建面板，使用适当的宽度
    panel = Panel(
        Text(banner, style="bold cyan"),
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
        width=80  # 增加宽度以确保完整显示ASCII艺术
    )
    
    # 打印面板
    console.print(Align.center(panel))
    
    # 打印版本和作者信息
    info_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2), width=80)
    info_table.add_column("Key", style="cyan", width=10)
    info_table.add_column("Value", style="green")
    
    info_table.add_row("版本", f"Beta {__version__}")
    info_table.add_row("作者", "Yagami")
    info_table.add_row("仓库", "https://github.com/yagami1997/TradeMind")
    info_table.add_row("许可证", "GPL-3.0")
    
    console.print(Align.center(info_table))
    console.print()

def show_menu():
    """
    显示主菜单
    """
    # 创建菜单表格
    menu_table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        border_style="cyan",
        width=80,  # 与标题宽度保持一致
        padding=(0, 2)
    )
    
    # 添加列
    menu_table.add_column("选项", style="yellow", width=8, justify="center")
    menu_table.add_column("功能", style="green", width=15)
    menu_table.add_column("描述", style="white", width=47)  # 调整以适应总宽度80
    
    # 添加菜单项
    menu_table.add_row(
        "1", 
        "命令行模式", 
        "交互式命令行界面，适合脚本操作"
    )
    menu_table.add_row(
        "2", 
        "Web模式", 
        "图形化Web界面，提供完整功能"
    )
    menu_table.add_row(
        "q", 
        "退出程序", 
        "结束程序运行"
    )
    
    # 打印菜单
    console.print("\n")
    console.print(Align.center(menu_table))
    console.print("\n")

def run_web_mode(host, port):
    """
    运行Web模式，并在退出时返回主菜单
    """
    try:
        run_web_server(host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n[yellow]Web服务器已停止，返回主菜单...[/yellow]")
        time.sleep(1)  # 给用户一个短暂的提示时间
        return
    except Exception as e:
        console.print(f"\n[red]Web服务器出错: {str(e)}[/red]")
        console.print("[yellow]返回主菜单...[/yellow]")
        time.sleep(1)
        return

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='TradeMind Lite - 股票分析工具')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    parser.add_argument('--cli', action='store_true', help='直接启动命令行模式')
    parser.add_argument('--web', action='store_true', help='直接启动Web模式')
    parser.add_argument('--port', type=int, default=3336, help='Web服务器端口')
    parser.add_argument('--host', default='0.0.0.0', help='Web服务器主机')
    
    args = parser.parse_args()
    
    # 显示版本信息
    if args.version:
        print_banner()
        return
    
    # 直接启动命令行模式
    if args.cli:
        run_interactive_mode()
        return
    
    # 直接启动Web模式
    if args.web:
        run_web_mode(host=args.host, port=args.port)
        return
    
    try:
        while True:
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 打印标题
            print_banner()
            
            # 显示菜单
            show_menu()
            
            # 获取用户选择
            choice = Prompt.ask(
                "[cyan]请选择操作[/cyan]",
                choices=["1", "2", "q"],
                show_choices=True,
                show_default=False
            )
            
            if choice == "1":
                run_interactive_mode()
            elif choice == "2":
                run_web_mode(host=args.host, port=args.port)
            elif choice == "q":
                console.print("\n[bold green]感谢使用 TradeMind Lite！[/bold green]")
                break
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]程序已终止[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]程序运行出错: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 