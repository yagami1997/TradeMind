"""
TradeMind Lite - 命令行界面

本模块提供TradeMind Lite的命令行界面，允许用户通过命令行执行股票分析和报告生成。
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
import webbrowser
from datetime import datetime
import pytz

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED
from rich import box
from rich.style import Style
from rich.align import Align
from rich.prompt import Prompt

from trademind.core.analyzer import StockAnalyzer
from trademind import compat
from trademind import __version__

# 创建Rich控制台
console = Console()

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
    
    console.print(Align.center(info_table))
    console.print()

def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    设置日志记录
    
    Args:
        verbose: 是否启用详细日志
        
    Returns:
        配置好的日志记录器
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/trademind_cli.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("trademind_cli")

def load_watchlists() -> Dict[str, Dict[str, str]]:
    """
    加载观察列表
    
    Returns:
        观察列表字典，格式为 {group_name: {symbol: name}}
    """
    try:
        config_path = Path('config') / 'watchlists.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载观察列表失败: {str(e)}")
        return {}

def list_watchlists(watchlists: Dict[str, Dict[str, str]]) -> None:
    """
    列出所有观察列表
    
    Args:
        watchlists: 观察列表字典
    """
    if not watchlists:
        console.print("[bold red]未找到观察列表。[/bold red]请在config/watchlists.json中创建观察列表。")
        return
    
    console.print("\n[bold cyan]可用的观察列表:[/bold cyan]")
    
    # 创建表格
    table = Table(show_header=True, box=ROUNDED, border_style="blue")
    table.add_column("观察列表", style="cyan")
    table.add_column("股票数量", style="green")
    table.add_column("示例股票", style="yellow")
    
    for group_name, symbols_dict in watchlists.items():
        # 获取前5个股票作为示例
        sample = list(symbols_dict.items())[:5]
        sample_text = ", ".join([f"{symbol}: {name}" for symbol, name in sample])
        
        if len(symbols_dict) > 5:
            sample_text += f"... 以及{len(symbols_dict) - 5}个其他股票"
        
        table.add_row(group_name, str(len(symbols_dict)), sample_text)
    
    console.print(table)

def analyze_stocks(symbols: List[str], names: Dict[str, str], analyzer: StockAnalyzer, 
                  open_browser: bool = True, report_title: str = "股票分析报告") -> str:
    """
    分析股票并生成报告
    
    Args:
        symbols: 股票代码列表
        names: 股票名称字典
        analyzer: 股票分析器实例
        open_browser: 是否在浏览器中打开报告
        report_title: 报告标题
        
    Returns:
        报告文件路径
    """
    # 显示进度信息
    with console.status(f"[bold green]正在分析 {len(symbols)} 只股票...[/bold green]", spinner="dots"):
        # 分析股票
        results = analyzer.analyze_stocks(symbols, names)
    
    # 显示进度信息
    with console.status("[bold green]正在生成报告...[/bold green]", spinner="dots"):
        # 生成报告
        report_path = analyzer.generate_report(results, report_title)
    
    # 如果需要，在浏览器中打开报告
    if open_browser and report_path:
        webbrowser.open(f'file://{os.path.abspath(report_path)}')
        console.print(f"[bold green]报告已在浏览器中打开: [link=file://{os.path.abspath(report_path)}]{os.path.basename(report_path)}[/link][/bold green]")
    else:
        console.print(f"[bold green]报告已生成: [link=file://{os.path.abspath(report_path)}]{os.path.basename(report_path)}[/link][/bold green]")
    
    return report_path

def run_cli() -> None:
    """
    运行简洁版命令行界面
    
    这个函数提供了一个简洁的命令行界面，用于执行股票分析和报告生成。
    """
    # 设置日志
    logger = setup_logging(False)
    
    # 创建分析器
    analyzer = StockAnalyzer()
    
    # 加载观察列表
    watchlists = load_watchlists()
    
    def show_menu():
        """显示命令行菜单"""
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 打印简洁的标题
        title = Text("TradeMind Lite\n", style="bold cyan")
        title.append(Text(f"轻量版美股技术分析工具 Beta {__version__}", style="cyan"))
        
        # 创建面板
        panel = Panel(
            Align.center(title),
            box=box.ROUNDED,
            border_style="cyan",
            padding=(1, 2),
            width=60
        )
        
        # 打印面板
        console.print("\n")
        console.print(Align.center(panel))
        console.print("\n")
        
        # 显示菜单
        menu_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE_HEAD,
            border_style="cyan",
            width=60,
            padding=(0, 2)
        )
        
        # 添加列
        menu_table.add_column("选项", style="yellow", width=6, justify="center")
        menu_table.add_column("功能", style="green", width=44)
        
        # 添加菜单项
        menu_table.add_row("1", "分析单个股票")
        menu_table.add_row("2", "批量分析多个股票")
        menu_table.add_row("3", "查看观察列表")
        menu_table.add_row("4", "查看历史报告")
        menu_table.add_row("5", "设置分析参数")
        menu_table.add_row("q", "返回主菜单")
        
        # 打印菜单
        console.print(Align.center(menu_table))
        console.print("\n")
    
    # 首次显示菜单
    show_menu()
    
    while True:
        try:
            # 获取用户选择
            choice = Prompt.ask(
                "[cyan]请选择操作[/cyan]",
                choices=["1", "2", "3", "4", "5", "q"],
                show_choices=True,
                default="1"
            )
            
            if choice == "1":
                # 分析单个股票
                console.print("[bold cyan]分析单个股票[/bold cyan]\n")
                symbol = Prompt.ask("[cyan]请输入股票代码[/cyan] (例如: AAPL)")
                if not symbol:
                    console.print("[yellow]未输入股票代码，返回主菜单[/yellow]\n")
                    show_menu()
                    continue
                
                symbols = [symbol.strip().upper()]
                names = {}
                
                # 执行分析
                report_path = analyze_stocks(symbols, names, analyzer, True)
                
                # 显示结果
                if report_path:
                    console.print(f"[green]分析完成！报告已保存至: {report_path}[/green]\n")
                else:
                    console.print("[red]分析失败，请检查股票代码是否正确[/red]\n")
                
                # 等待用户按任意键继续
                Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                show_menu()
                
            elif choice == "2":
                # 批量分析多个股票
                console.print("[bold cyan]批量分析多个股票[/bold cyan]\n")
                symbols_input = Prompt.ask("[cyan]请输入多个股票代码[/cyan] (用空格分隔，例如: AAPL MSFT GOOGL)")
                if not symbols_input:
                    console.print("[yellow]未输入股票代码，返回主菜单[/yellow]\n")
                    show_menu()
                    continue
                
                symbols = [s.strip().upper() for s in symbols_input.split()]
                names = {}
                
                # 执行分析
                report_path = analyze_stocks(symbols, names, analyzer, True, "批量股票分析报告")
                
                # 显示结果
                if report_path:
                    console.print(f"[green]分析完成！报告已保存至: {report_path}[/green]\n")
                else:
                    console.print("[red]分析失败，请检查股票代码是否正确[/red]\n")
                
                # 等待用户按任意键继续
                Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                show_menu()
                
            elif choice == "3":
                # 查看观察列表
                console.print("[bold cyan]查看观察列表[/bold cyan]\n")
                
                if not watchlists:
                    console.print("[yellow]没有可用的观察列表[/yellow]\n")
                    Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                    show_menu()
                    continue
                
                # 显示观察列表
                watchlist_table = Table(
                    show_header=True,
                    header_style="bold cyan",
                    box=box.SIMPLE_HEAD,
                    border_style="cyan",
                    width=80
                )
                watchlist_table.add_column("序号", style="yellow", width=6, justify="center")
                watchlist_table.add_column("观察列表", style="green")
                watchlist_table.add_column("股票数量", style="cyan", width=10, justify="center")
                
                # 添加观察列表
                watchlist_names = list(watchlists.keys())
                for i, group_name in enumerate(watchlist_names, 1):
                    watchlist_table.add_row(
                        str(i),
                        group_name,
                        str(len(watchlists[group_name]))
                    )
                
                # 添加"查询全部股票"选项
                # 计算所有股票的总数（去重）
                all_symbols = set()
                for group_stocks in watchlists.values():
                    all_symbols.update(group_stocks.keys())
                
                watchlist_table.add_row(
                    str(len(watchlist_names) + 1),
                    "[bold green]查询全部股票[/bold green]",
                    str(len(all_symbols))
                )
                
                console.print(watchlist_table)
                console.print()
                
                # 选择观察列表
                watchlist_choices = [str(i) for i in range(1, len(watchlist_names) + 2)]  # +1 for all stocks option
                watchlist_choice = Prompt.ask(
                    "[cyan]请选择观察列表[/cyan]",
                    choices=watchlist_choices + ["q"],
                    show_choices=True,
                    default="1"
                )
                
                if watchlist_choice == "q":
                    show_menu()
                    continue
                
                # 处理"查询全部股票"选项
                if int(watchlist_choice) == len(watchlist_names) + 1:
                    # 收集所有预设股票（去重）
                    all_symbols = []
                    all_names = {}
                    for group_name, group_stocks in watchlists.items():
                        for code, name in group_stocks.items():
                            if code not in all_names:  # 避免重复
                                all_symbols.append(code)
                                all_names[code] = name
                    
                    symbols = all_symbols
                    names = all_names
                    report_title = "全市场分析报告（所有预设股票）"
                    
                    console.print(f"[bold cyan]将分析所有预设股票:[/bold cyan] [green]{len(symbols)}[/green] 只股票")
                else:
                    # 处理普通观察列表
                    selected_watchlist = watchlist_names[int(watchlist_choice) - 1]
                    symbols = list(watchlists[selected_watchlist].keys())
                    names = watchlists[selected_watchlist]
                    report_title = f"{selected_watchlist}分析报告"
                
                # 执行分析
                report_path = analyze_stocks(symbols, names, analyzer, True, report_title)
                
                # 显示结果
                if report_path:
                    console.print(f"[green]分析完成！报告已保存至: {report_path}[/green]\n")
                else:
                    console.print("[red]分析失败，请检查股票代码是否正确[/red]\n")
                
                # 等待用户按任意键继续
                Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                show_menu()
                
            elif choice == "4":
                # 查看历史报告
                console.print("[bold cyan]查看历史报告[/bold cyan]\n")
                
                # 获取报告目录
                reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reports')
                if not os.path.exists(reports_dir):
                    console.print("[yellow]没有可用的历史报告[/yellow]\n")
                    Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                    show_menu()
                    continue
                
                # 获取所有HTML报告
                reports = []
                for root, _, files in os.walk(reports_dir):
                    for file in files:
                        if file.endswith('.html'):
                            file_path = os.path.join(root, file)
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            reports.append((file, file_path, file_time))
                
                # 按时间排序，最新的在前
                reports.sort(key=lambda x: x[2], reverse=True)
                
                if not reports:
                    console.print("[yellow]没有可用的历史报告[/yellow]\n")
                    Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                    show_menu()
                    continue
                
                # 显示报告列表和操作选项
                console.print("[bold cyan]历史报告列表[/bold cyan]")
                report_table = Table(
                    show_header=True,
                    header_style="bold cyan",
                    box=box.SIMPLE_HEAD,
                    border_style="cyan",
                    width=80
                )
                report_table.add_column("序号", style="yellow", width=6, justify="center")
                report_table.add_column("报告名称", style="green")
                report_table.add_column("生成时间", style="cyan", width=20)
                
                # 最多显示10个最新的报告
                for i, (file, _, file_time) in enumerate(reports[:10]):
                    report_table.add_row(
                        str(i+1),
                        file,
                        file_time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                
                console.print(report_table)
                console.print()
                
                # 显示操作选项
                options_table = Table(
                    show_header=True,
                    header_style="bold cyan",
                    box=box.SIMPLE_HEAD,
                    border_style="cyan",
                    width=80
                )
                options_table.add_column("选项", style="yellow", width=6, justify="center")
                options_table.add_column("操作", style="green")
                
                options_table.add_row("1-10", "查看对应序号的报告")
                options_table.add_row("c", "清理报告")
                options_table.add_row("q", "返回主菜单")
                
                console.print(options_table)
                console.print()
                
                # 选择操作
                report_choices = [str(i+1) for i in range(min(10, len(reports)))]
                operation_choice = Prompt.ask(
                    "[cyan]请选择操作[/cyan]",
                    choices=report_choices + ["c", "q"],
                    show_choices=True,
                    default="1"
                )
                
                if operation_choice == "q":
                    show_menu()
                    continue
                elif operation_choice == "c":
                    # 清理报告子菜单
                    console.print("[bold cyan]清理历史报告[/bold cyan]\n")
                    
                    clean_table = Table(
                        show_header=True,
                        header_style="bold cyan",
                        box=box.SIMPLE_HEAD,
                        border_style="cyan",
                        width=80
                    )
                    clean_table.add_column("选项", style="yellow", width=6, justify="center")
                    clean_table.add_column("操作", style="green")
                    
                    clean_table.add_row("1", "清理7天前的报告")
                    clean_table.add_row("2", "清理30天前的报告")
                    clean_table.add_row("3", "清理所有报告")
                    clean_table.add_row("4", "自定义天数")
                    clean_table.add_row("q", "返回上级菜单")
                    
                    console.print(clean_table)
                    console.print()
                    
                    clean_choice = Prompt.ask(
                        "[cyan]请选择清理选项[/cyan]",
                        choices=["1", "2", "3", "4", "q"],
                        show_choices=True,
                        default="2"
                    )
                    
                    if clean_choice == "q":
                        # 重新显示报告列表
                        choice = "4"  # 重新进入查看历史报告功能
                        continue
                    
                    days_threshold = None
                    force_all = False
                    
                    if clean_choice == "1":
                        days_threshold = 7
                    elif clean_choice == "2":
                        days_threshold = 30
                    elif clean_choice == "3":
                        days_threshold = None
                        force_all = True
                    elif clean_choice == "4":
                        # 自定义天数
                        days_input = Prompt.ask(
                            "[cyan]请输入要清理多少天前的报告[/cyan]",
                            default="30"
                        )
                        try:
                            days_threshold = int(days_input)
                        except ValueError:
                            console.print("[red]输入无效，使用默认值30天[/red]")
                            days_threshold = 30
                    
                    # 确认操作
                    if force_all:
                        confirm = Prompt.ask(
                            "[bold red]警告：此操作将删除所有报告文件，无法恢复！确认继续？(y/n)[/bold red]",
                            choices=["y", "n"],
                            default="n"
                        )
                    else:
                        confirm = Prompt.ask(
                            f"[yellow]确认清理{days_threshold if days_threshold else '所有'}天前的报告？(y/n)[/yellow]",
                            choices=["y", "n"],
                            default="y"
                        )
                    
                    if confirm.lower() == "y":
                        # 执行清理操作
                        with console.status(f"[bold green]正在清理报告...[/bold green]", spinner="dots"):
                            deleted_count = analyzer.clean_reports(days_threshold if not force_all else None)
                        
                        console.print(f"[green]成功清理 {deleted_count} 个报告文件[/green]")
                    else:
                        console.print("[yellow]已取消清理操作[/yellow]")
                    
                    # 等待用户按任意键继续
                    Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                    show_menu()
                    continue
                else:
                    # 查看选择的报告
                    selected_report = reports[int(operation_choice) - 1]
                    webbrowser.open(f"file://{selected_report[1]}")
                    
                    # 等待用户按任意键继续
                    Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                    show_menu()
                
            elif choice == "5":
                # 设置分析参数
                console.print("[bold cyan]设置分析参数[/bold cyan]\n")
                console.print("[yellow]此功能尚未实现，敬请期待[/yellow]\n")
                Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
                show_menu()
                
            elif choice == "q":
                # 返回主菜单
                break
                
        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消，返回主菜单[/yellow]\n")
            show_menu()
            continue
        except Exception as e:
            console.print(f"\n[red]发生错误: {str(e)}[/red]\n")
            logger.exception("命令行界面出错")
            Prompt.ask("[cyan]按Enter键返回主菜单[/cyan]")
            show_menu()
            continue

if __name__ == "__main__":
    run_cli() 