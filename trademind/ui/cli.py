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
    运行命令行界面
    """
    # 打印标题
    print_banner()
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='TradeMind Lite - 股票技术分析工具')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析股票')
    analyze_parser.add_argument('--symbols', '-s', nargs='+', help='股票代码列表')
    analyze_parser.add_argument('--watchlist', '-w', help='使用观察列表')
    analyze_parser.add_argument('--all', '-a', action='store_true', help='分析所有预设股票')
    analyze_parser.add_argument('--title', '-t', default='股票分析报告', help='报告标题')
    analyze_parser.add_argument('--no-browser', '-n', action='store_true', help='不在浏览器中打开报告')
    
    # 列出观察列表命令
    list_parser = subparsers.add_parser('list', help='列出观察列表')
    
    # 清理报告命令
    clean_parser = subparsers.add_parser('clean', help='清理旧报告')
    clean_parser.add_argument('--days', '-d', type=int, default=30, help='清理多少天前的报告')
    
    # 版本命令
    version_parser = subparsers.add_parser('version', help='显示版本信息')
    
    # 全局选项
    parser.add_argument('--verbose', '-v', action='store_true', help='启用详细日志')
    parser.add_argument('--compat', '-c', action='store_true', help='使用兼容模式')
    parser.add_argument('--interactive', '-i', action='store_true', help='使用交互式模式')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging(args.verbose)
    
    # 如果指定了交互式模式或没有指定命令，进入交互式模式
    if args.interactive or not args.command:
        run_interactive_mode(logger)
        return
    
    # 加载观察列表
    watchlists = load_watchlists()
    
    # 处理命令
    if args.command == 'list':
        list_watchlists(watchlists)
        return
    
    elif args.command == 'version':
        from trademind import __version__
        console.print(f"[bold cyan]TradeMind Lite 版本:[/bold cyan] [bold green]Beta {__version__}[/bold green]")
        return
    
    elif args.command == 'clean':
        with console.status("[bold green]正在清理旧报告...[/bold green]", spinner="dots"):
            analyzer = StockAnalyzer()
            analyzer.clean_reports(days_threshold=args.days)
        console.print(f"[bold green]已清理 {args.days} 天前的报告[/bold green]")
        return
    
    elif args.command == 'analyze':
        # 确定要分析的股票
        symbols_to_analyze = []
        names_dict = {}
        
        if args.symbols:
            symbols_to_analyze = args.symbols
            # 使用股票代码作为名称
            names_dict = {symbol: symbol for symbol in symbols_to_analyze}
            console.print(f"[bold cyan]将分析以下股票:[/bold cyan] [green]{', '.join(symbols_to_analyze)}[/green]")
        
        elif args.watchlist:
            if args.watchlist in watchlists:
                symbols_dict = watchlists[args.watchlist]
                symbols_to_analyze = list(symbols_dict.keys())
                names_dict = symbols_dict
                console.print(f"[bold cyan]将分析观察列表:[/bold cyan] [green]{args.watchlist}[/green] ([cyan]{len(symbols_to_analyze)}[/cyan] 只股票)")
            else:
                logger.error(f"未找到观察列表: {args.watchlist}")
                console.print(f"[bold red]未找到观察列表:[/bold red] [red]{args.watchlist}[/red]")
                console.print("[bold cyan]可用的观察列表:[/bold cyan]")
                for group_name in watchlists.keys():
                    console.print(f"  - [green]{group_name}[/green]")
                return
        
        elif args.all:
            # 收集所有预设股票（去重）
            all_symbols = []
            all_names = {}
            for group_name, group_stocks in watchlists.items():
                for code, name in group_stocks.items():
                    if code not in all_names:  # 避免重复
                        all_symbols.append(code)
                        all_names[code] = name
            
            symbols_to_analyze = all_symbols
            names_dict = all_names
            console.print(f"[bold cyan]将分析所有预设股票:[/bold cyan] [green]{len(symbols_to_analyze)}[/green] 只股票")
        
        else:
            logger.error("未指定股票代码或观察列表")
            console.print("[bold red]错误:[/bold red] 请使用--symbols指定股票代码或使用--watchlist指定观察列表")
            return
        
        # 如果没有股票可分析，退出
        if not symbols_to_analyze:
            logger.error("没有股票可分析")
            console.print("[bold red]错误:[/bold red] 没有股票可分析")
            return
        
        # 创建分析器
        analyzer = StockAnalyzer()
        
        # 分析股票
        try:
            report_path = analyze_stocks(
                symbols_to_analyze, 
                names_dict, 
                analyzer, 
                not args.no_browser,
                args.title
            )
            
            logger.info(f"分析完成，报告已生成: {report_path}")
            
        except Exception as e:
            logger.exception(f"分析过程中发生错误: {str(e)}")
            console.print(f"[bold red]错误:[/bold red] {str(e)}")
            return

def run_interactive_mode(logger=None):
    """
    运行交互式模式
    
    Args:
        logger: 日志记录器
    """
    # 如果没有提供日志记录器，创建一个
    if logger is None:
        logger = setup_logging()
        
    # 创建分析器
    analyzer = StockAnalyzer()
    
    # 加载观察列表
    watchlists = load_watchlists()
    
    while True:
        console.clear()
        print_banner()
        
        # 显示菜单
        menu_table = Table(box=None, padding=(0, 2), width=70)
        menu_table.add_column("选项", style="cyan", width=5)
        menu_table.add_column("描述", style="green")
        
        menu_table.add_row("1", "手动输入股票代码")
        menu_table.add_row("2", "使用预设股票组合")
        menu_table.add_row("3", "清理历史报告文件")
        menu_table.add_row("0", "退出程序")
        
        console.print(Align.center(menu_table))
        console.print()
        
        # 获取用户选择
        choice = Prompt.ask("请选择", choices=["0", "1", "2", "3"], default="1")
        
        if choice == "0":
            console.print("[bold cyan]正在退出程序...[/bold cyan]")
            break
        
        elif choice == "3":
            # 清理报告
            days = input("\n请输入要清理多少天前的报告 (默认30天): ").strip()
            if not days:
                days = 30
            else:
                try:
                    days = int(days)
                except ValueError:
                    console.print("[bold red]错误:[/bold red] 请输入有效的天数")
                    input("\n按回车键继续...")
                    continue
            
            with console.status("[bold green]正在清理旧报告...[/bold green]", spinner="dots"):
                analyzer.clean_reports(days_threshold=days)
            console.print(f"[bold green]已清理 {days} 天前的报告[/bold green]")
            input("\n按回车键继续...")
            continue
        
        symbols = []
        names = {}
        title = "股票分析报告"
        
        if choice == "1":
            # 手动输入股票代码
            console.print("\n[bold cyan]请输入股票代码[/bold cyan]（最多20个，每行一个，支持自定义名称，格式：代码=名称）")
            console.print("示例：")
            console.print("AAPL=苹果")
            console.print("MSFT=微软")
            console.print("输入空行结束\n")
            
            count = 0
            while count < 20:
                line = input().strip()
                if not line:
                    break
                
                if "=" in line:
                    symbol, name = line.split("=", 1)
                    symbol = symbol.strip().upper()
                    name = name.strip()
                    symbols.append(symbol)
                    names[symbol] = name
                else:
                    symbol = line.strip().upper()
                    symbols.append(symbol)
                    names[symbol] = symbol
                
                count += 1
            
            if not symbols:
                console.print("[bold red]错误:[/bold red] 未输入任何股票代码")
                input("\n按回车键继续...")
                continue
            
            title = input("\n请输入报告标题 (默认为'股票分析报告'): ").strip()
            if not title:
                title = "股票分析报告"
        
        elif choice == "2":
            # 使用预设股票组合
            if not watchlists:
                console.print("[bold red]错误:[/bold red] 未找到任何预设股票组合")
                input("\n按回车键继续...")
                continue
            
            console.print("\n[bold cyan]可用的预设股票组合:[/bold cyan]")
            for i, group_name in enumerate(watchlists.keys(), 1):
                console.print(f"{i}. {group_name} ({len(watchlists[group_name])}只股票)")
            
            # 添加"分析所有股票"选项
            console.print(f"{len(watchlists) + 1}. [bold green]分析所有股票[/bold green] (所有预设列表)")
            
            group_choice = input("\n请选择股票组合编号: ").strip()
            try:
                group_index = int(group_choice) - 1
                
                # 处理"分析所有股票"选项
                if group_index == len(watchlists):
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
                    title = "全市场分析报告（预置股票列表）"
                    
                    console.print(f"[bold cyan]将分析所有预设股票:[/bold cyan] [green]{len(symbols)}[/green] 只股票")
                
                elif group_index < 0 or group_index >= len(watchlists):
                    raise ValueError()
                
                else:
                    group_name = list(watchlists.keys())[group_index]
                    symbols_dict = watchlists[group_name]
                    symbols = list(symbols_dict.keys())
                    names = symbols_dict
                    
                    title = input(f"\n请输入报告标题 (默认为'{group_name}分析报告'): ").strip()
                    if not title:
                        title = f"{group_name}分析报告"
            
            except (ValueError, IndexError):
                console.print("[bold red]错误:[/bold red] 无效的选择")
                input("\n按回车键继续...")
                continue
        
        else:
            console.print("[bold red]错误:[/bold red] 无效的选择")
            input("\n按回车键继续...")
            continue
        
        # 分析股票
        try:
            console.print(f"\n[bold cyan]正在分析 {len(symbols)} 只股票...[/bold cyan]")
            
            # 显示进度信息
            with console.status(f"[bold green]正在分析 {len(symbols)} 只股票...[/bold green]", spinner="dots"):
                # 分析股票
                results = analyzer.analyze_stocks(symbols, names)
            
            # 显示进度信息
            with console.status("[bold green]正在生成报告...[/bold green]", spinner="dots"):
                # 生成报告
                report_path = analyzer.generate_report(results, title)
            
            # 询问是否在浏览器中打开报告
            open_browser = input("\n是否在浏览器中打开报告? (y/n): ").strip().lower() == 'y'
            
            if open_browser and report_path:
                webbrowser.open(f'file://{os.path.abspath(report_path)}')
                console.print(f"[bold green]报告已在浏览器中打开: [link=file://{os.path.abspath(report_path)}]{os.path.basename(report_path)}[/link][/bold green]")
            else:
                console.print(f"[bold green]报告已生成: [link=file://{os.path.abspath(report_path)}]{os.path.basename(report_path)}[/link][/bold green]")
            
            input("\n按回车键继续...")
            
        except Exception as e:
            logger.exception(f"分析过程中发生错误: {str(e)}")
            console.print(f"[bold red]错误:[/bold red] {str(e)}")
            input("\n按回车键继续...")

if __name__ == "__main__":
    run_cli() 