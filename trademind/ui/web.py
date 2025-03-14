"""
TradeMind Lite - Web界面

本模块提供TradeMind Lite的Web界面，允许用户通过浏览器执行股票分析和报告生成。
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta
import pytz
import webbrowser
import threading
import time
from urllib.parse import quote
import socket
import psutil
import subprocess
import requests

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np

from trademind.core.analyzer import StockAnalyzer
from trademind.core.indicators import (
    calculate_rsi, 
    calculate_macd, 
    calculate_kdj, 
    calculate_bollinger_bands
)
from trademind.core.patterns import identify_candlestick_patterns
from trademind.core.signals import generate_trading_advice, generate_signals
from trademind.backtest.engine import run_backtest
from trademind import compat
from trademind import __version__

# 创建Flask应用
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)  # 启用CORS支持

# 全局变量
analyzer = None
watchlists = {}
logger = None
analysis_progress = {
    "in_progress": False,
    "percent": 0,
    "current_index": 0,
    "total": 0,
    "current_symbol": "",
    "start_time": None,
    "last_report_path": None
}

@app.route('/')
def index():
    """
    主页路由
    """
    return render_template('index.html', version=__version__, watchlists=watchlists)

@app.route('/api/analyze', methods=['POST'])
def analyze_stocks():
    """
    分析股票API
    """
    global analysis_progress
    
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        names = data.get('names', {})
        title = data.get('title', '美股技术面分析报告')
        analyze_all = data.get('analyze_all', False)
        
        if not symbols and not analyze_all:
            return jsonify({'error': '未提供股票代码'}), 400
        
        # 如果选择分析所有股票
        if analyze_all:
            # 收集所有预设股票（去重但保持原始顺序）
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
        
        # 初始化进度信息
        analysis_progress["in_progress"] = True
        analysis_progress["percent"] = 0
        analysis_progress["current_index"] = 0
        analysis_progress["total"] = len(symbols)
        analysis_progress["current_symbol"] = ""
        analysis_progress["start_time"] = datetime.now()
        analysis_progress["last_report_path"] = None
        
        # 创建一个线程来执行分析，以便不阻塞响应
        def run_analysis():
            global analysis_progress
            try:
                # 重写analyze_stocks方法，添加进度跟踪
                results = []
                total = len(symbols)
                
                for index, symbol in enumerate(symbols, 1):
                    try:
                        # 更新进度信息
                        analysis_progress["current_index"] = index
                        analysis_progress["current_symbol"] = f"{names.get(symbol, symbol)} ({symbol})"
                        analysis_progress["percent"] = index / total
                        
                        print(f"\n[{index}/{total} - {index/total*100:.1f}%] 分析: {names.get(symbol, symbol)} ({symbol})")
                        stock = yf.Ticker(symbol)
                        hist = stock.history(period="1y")
                        
                        if hist.empty:
                            print(f"⚠️ 无法获取 {symbol} 的数据，跳过")
                            continue
                        
                        # 确保有足够的数据计算价格变化
                        if len(hist) >= 2:
                            current_price = hist['Close'].iloc[-1]
                            prev_price = hist['Close'].iloc[-2]
                            price_change = current_price - prev_price
                            # 确保除数不为零
                            if prev_price > 0:
                                price_change_pct = (price_change / prev_price) * 100
                            else:
                                price_change_pct = 0.0
                        else:
                            # 如果只有一天数据，无法计算变化
                            current_price = hist['Close'].iloc[-1] if not hist.empty else 0.0
                            prev_price = hist['Open'].iloc[-1] if not hist.empty else 0.0
                            price_change = current_price - prev_price
                            # 确保除数不为零
                            if prev_price > 0:
                                price_change_pct = (price_change / prev_price) * 100
                            else:
                                price_change_pct = 0.0
                        
                        # 确保价格变化百分比不是NaN或无穷大
                        if pd.isna(price_change_pct) or np.isinf(price_change_pct):
                            price_change_pct = 0.0
                        
                        # 打印调试信息
                        print(f"当前价格: {current_price:.2f}, 前一价格: {prev_price:.2f}")
                        print(f"价格变化: {price_change:.2f}, 变化百分比: {price_change_pct:.2f}%")
                        
                        print("计算技术指标...")
                        # 调用技术指标模块
                        rsi = calculate_rsi(hist['Close'])
                        macd, signal, hist_macd = calculate_macd(hist['Close'])
                        k, d, j = calculate_kdj(hist['High'], hist['Low'], hist['Close'])
                        bb_upper, bb_middle, bb_lower, bb_width, bb_percent = calculate_bollinger_bands(hist['Close'])
                        
                        indicators = {
                            'rsi': rsi,
                            'macd': {'macd': macd, 'signal': signal, 'hist': hist_macd},
                            'kdj': {'k': k, 'd': d, 'j': j},
                            'bollinger': {
                                'upper': bb_upper, 
                                'middle': bb_middle, 
                                'lower': bb_lower,
                                'bandwidth': bb_width,
                                'percent_b': bb_percent
                            }
                        }
                        
                        print("分析K线形态...")
                        # 调用形态识别模块
                        patterns = identify_candlestick_patterns(hist.tail(5))
                        
                        print("生成交易建议...")
                        # 调用信号生成模块
                        advice = generate_trading_advice(indicators, current_price, patterns)
                        
                        print("执行策略回测...")
                        # 生成交易信号
                        signals = generate_signals(hist, indicators)
                        
                        # 调用回测模块
                        backtest_results = run_backtest(hist, signals)
                        
                        results.append({
                            'symbol': symbol,
                            'name': names.get(symbol, symbol),
                            'price': current_price,
                            'price_change': price_change,
                            'price_change_pct': price_change_pct,
                            'prev_close': prev_price,
                            'indicators': indicators,
                            'patterns': patterns,
                            'advice': advice,
                            'backtest': backtest_results
                        })
                        
                        print(f"✅ {symbol} 分析完成")
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"分析 {symbol} 时出错", exc_info=True)
                        print(f"❌ {symbol} 分析失败: {str(e)}")
                        continue
                
                # 生成报告
                report_path = analyzer.generate_report(results, title)
                analysis_progress["last_report_path"] = report_path
                analysis_progress["in_progress"] = False
                analysis_progress["percent"] = 1.0
                
            except Exception as e:
                logger.exception(f"分析过程中发生错误: {str(e)}")
                analysis_progress["in_progress"] = False
        
        # 启动分析线程
        threading.Thread(target=run_analysis).start()
        
        # 立即返回响应，不等待分析完成
        return jsonify({
            'success': True,
            'message': '分析已开始，请等待完成',
            'status': 'processing'
        })
        
    except Exception as e:
        logger.exception(f"启动分析过程中发生错误: {str(e)}")
        analysis_progress["in_progress"] = False
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress')
def get_progress():
    """
    获取分析进度
    """
    global analysis_progress
    
    if analysis_progress["in_progress"]:
        # 计算已用时间
        elapsed = None
        if analysis_progress["start_time"]:
            elapsed = (datetime.now() - analysis_progress["start_time"]).total_seconds()
        
        # 计算预计剩余时间
        remaining = None
        if elapsed and analysis_progress["percent"] > 0:
            remaining = elapsed / analysis_progress["percent"] - elapsed
        
        return jsonify({
            'progress': {
                'in_progress': True,
                'percent': analysis_progress["percent"],
                'current_index': analysis_progress["current_index"],
                'total': analysis_progress["total"],
                'current_symbol': analysis_progress["current_symbol"],
                'elapsed_seconds': elapsed,
                'remaining_seconds': remaining
            }
        })
    elif analysis_progress["last_report_path"]:
        # 分析已完成，返回报告路径
        report_path = analysis_progress["last_report_path"]
        report_filename = os.path.basename(report_path)
        # 使用URL编码处理文件名，确保特殊字符和空格被正确编码
        encoded_filename = quote(report_filename)
        report_url = f'/reports/{encoded_filename}'
        
        # 获取美国洛杉矶时间
        la_time = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'progress': {
                'in_progress': False,
                'percent': 1.0,
                'report_path': report_path,
                'report_url': report_url,
                'timestamp': f"{la_time} (PST/PDT Time)"
            }
        })
    else:
        # 没有正在进行的分析
        return jsonify({
            'progress': None
        })

@app.route('/reports/<path:filename>')
def serve_report(filename):
    """
    提供报告文件访问
    """
    try:
        # 打印调试信息
        print(f"请求访问报告: {filename}")
        print(f"分析器报告目录: {analyzer.results_path}")
        
        # 确保报告目录存在
        if not os.path.exists(analyzer.results_path):
            print(f"报告目录不存在: {analyzer.results_path}")
            return jsonify({'error': f'报告目录不存在: {analyzer.results_path}'}), 404
            
        # 处理文件名中可能的URL编码问题
        filename = os.path.basename(filename)
        print(f"处理后的文件名: {filename}")
        
        # 检查文件是否存在
        report_path = os.path.join(analyzer.results_path, filename)
        print(f"尝试访问报告路径: {report_path}")
        
        if not os.path.exists(report_path):
            print(f"报告文件不存在: {report_path}")
            
            # 列出目录中的所有文件
            print("目录中的文件:")
            for file in os.listdir(analyzer.results_path):
                print(f" - {file}")
            
            # 尝试查找匹配的文件（忽略空格问题）
            for file in os.listdir(analyzer.results_path):
                if file.replace(" ", "") == filename.replace(" ", ""):
                    report_path = os.path.join(analyzer.results_path, file)
                    filename = file
                    print(f"找到匹配的文件: {filename}")
                    break
            else:
                return jsonify({'error': f'报告文件不存在: {filename}'}), 404
        
        print(f"准备发送文件: {filename}")
        # 使用绝对路径
        abs_path = os.path.abspath(analyzer.results_path)
        print(f"绝对路径: {abs_path}")
        
        return send_from_directory(
            abs_path,
            filename,
            as_attachment=False
        )
    except Exception as e:
        logger.exception(f"访问报告文件时发生错误: {str(e)}")
        return jsonify({'error': f'访问报告文件时发生错误: {str(e)}'}), 500

@app.route('/api/reports')
def list_reports():
    """
    列出所有报告
    """
    try:
        reports = []
        if not os.path.exists(analyzer.results_path):
            return jsonify({
                'success': True,
                'reports': []
            })
            
        for filename in os.listdir(analyzer.results_path):
            if filename.endswith('.html'):
                filepath = os.path.join(analyzer.results_path, filename)
                # 使用美国洛杉矶时间
                created_timestamp = os.path.getctime(filepath)
                created_time = datetime.fromtimestamp(
                    created_timestamp, 
                    pytz.timezone('America/Los_Angeles')
                )
                # 判断是否为夏令时
                is_dst = created_time.dst() != timedelta(0)
                tz_suffix = "PDT" if is_dst else "PST"
                
                # 使用URL编码处理文件名
                encoded_filename = quote(filename)
                
                reports.append({
                    'name': filename,
                    'url': f'/reports/{encoded_filename}',
                    'created': created_time.strftime(f'%Y-%m-%d %H:%M:%S ({tz_suffix} Time)')
                })
        
        return jsonify({
            'success': True,
            'reports': sorted(reports, key=lambda x: x['created'], reverse=True)
        })
        
    except Exception as e:
        logger.exception(f"列出报告时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/watchlists')
def list_watchlists():
    """列出所有观察列表"""
    return jsonify(watchlists)

@app.route('/clean', methods=['POST'])
def clean_reports():
    """清理旧报告"""
    days = request.form.get('days', 30, type=int)
    force_all = request.form.get('force_all', 'false') == 'true'
    
    try:
        print(f"开始清理报告，阈值: {days}天, 强制删除所有: {force_all}")
        
        # 直接调用analyzer的clean_reports方法
        # 如果force_all为True，则传入days_threshold=None，表示删除所有报告
        count = analyzer.clean_reports(days_threshold=None if force_all else days)
        
        # 返回结果
        result_msg = f"已删除 {count} 个{'所有' if force_all else f'超过 {days} 天的旧'}报告"
        print(result_msg)
        
        return jsonify({
            'success': True, 
            'message': result_msg,
            'count': count
        })
    except Exception as e:
        print(f"清理报告时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def refresh_reports_cache():
    """强制刷新报告列表缓存"""
    try:
        # 这里可以添加任何需要的缓存刷新逻辑
        logger.info("刷新报告列表缓存")
    except Exception as e:
        logger.error(f"刷新报告列表缓存失败: {str(e)}")

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

def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    设置日志记录
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 设置基础日志级别
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/trademind_web.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 设置各个模块的日志级别
    logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 只显示错误
    logging.getLogger('urllib3').setLevel(logging.WARNING)  # 减少HTTP请求日志
    logging.getLogger('yfinance').setLevel(logging.WARNING)  # 减少yfinance的日志
    logging.getLogger('flask').setLevel(logging.WARNING)  # 减少Flask框架日志
    
    # 获取应用日志记录器并设置级别
    app_logger = logging.getLogger("trademind_web")
    app_logger.setLevel(logging.INFO)  # 保持应用日志为INFO级别
    
    # 设置日志格式，突出显示错误和警告
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    for handler in app_logger.handlers:
        handler.setFormatter(formatter)
    
    return app_logger

def open_browser(port: int) -> None:
    """
    在浏览器中打开Web界面
    
    Args:
        port: Web服务器端口
    """
    # 等待服务器启动
    time.sleep(1.5)
    
    # 打开浏览器
    webbrowser.open(f'http://localhost:{port}')

def check_port(port):
    """检查端口是否被占用，只返回占用该端口的Python进程"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            s.close()
            return None
        except socket.error:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # 只检查Python进程
                    if proc.name().lower() not in ['python', 'python3', 'pythonw']:
                        continue
                        
                    connections = proc.connections()
                    for conn in connections:
                        if hasattr(conn, 'laddr') and hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                            # 确认是我们的应用进程
                            cmdline = proc.cmdline()
                            if any('trademind_web.py' in cmd for cmd in cmdline):
                                return proc.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return None

def cleanup_port(port):
    """安全地清理占用端口的进程，只处理TradeMind的Python进程"""
    pid = check_port(port)
    if pid:
        try:
            proc = psutil.Process(pid)
            # 再次确认是Python进程且运行的是我们的应用
            if (proc.name().lower() in ['python', 'python3', 'pythonw'] and
                any('trademind_web.py' in cmd for cmd in proc.cmdline())):
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/PID', str(pid)], check=True)
                else:
                    proc.terminate()  # 使用更温和的终止方式
                    try:
                        proc.wait(timeout=3)  # 等待进程终止
                    except psutil.TimeoutExpired:
                        proc.kill()  # 如果等待超时，才强制结束
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, subprocess.CalledProcessError):
            return False
    return True

def start_server(host, port):
    """启动服务器并处理用户输入"""
    print("\n正在启动服务器...")
    print(f"访问地址: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print("\n可用命令：")
    print("1 或 help     - 显示帮助信息")
    print("2 或 stop     - 停止服务器")
    print("3 或 restart  - 重启服务器")
    print("4 或 status   - 显示服务器状态")
    print("5 或 clear    - 清屏")
    print("\n" + "="*50 + "\n")
    
    # 创建一个事件来控制服务器
    server_running = threading.Event()
    server_running.set()
    
    def run_flask():
        """在单独的线程中运行Flask服务器"""
        try:
            app.run(host=host, port=port, debug=False, threaded=True)
        except Exception as e:
            logger.exception("Flask服务器运行出错")
            server_running.clear()
    
    def handle_commands():
        """处理用户输入的命令"""
        while server_running.is_set():
            try:
                command = input("\n输入命令或数字（1-5）: ").strip().lower()
                
                # 支持数字输入
                command_map = {
                    '1': 'help',
                    '2': 'stop',
                    '3': 'restart',
                    '4': 'status',
                    '5': 'clear'
                }
                
                # 如果输入的是数字，转换为对应的命令
                if command in command_map:
                    command = command_map[command]
                
                if command == 'help':
                    print("\n可用命令：")
                    print("1 或 help     - 显示本帮助信息")
                    print("2 或 stop     - 停止服务器")
                    print("3 或 restart  - 重启服务器")
                    print("4 或 status   - 显示当前服务器状态")
                    print("5 或 clear    - 清屏")
                    
                elif command == 'stop':
                    print("\n正在停止服务器...")
                    server_running.clear()
                    # 不再使用sys.exit()，而是返回
                    return False
                    
                elif command == 'restart':
                    print("\n正在重启服务器...")
                    server_running.clear()
                    time.sleep(1)
                    return True  # 表示需要重启
                    
                elif command == 'status':
                    if server_running.is_set():
                        print(f"\n服务器正在运行")
                        print(f"地址: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
                        print(f"PID: {os.getpid()}")
                    else:
                        print("\n服务器已停止")
                        
                elif command == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"\n服务器正在运行: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
                    print("\n输入命令或数字（1-5）")
                    
                else:
                    print("\n未知命令。输入 1 或 help 查看可用命令。")
                    
            except (EOFError, KeyboardInterrupt):
                print("\n使用 2 或 stop 命令来停止服务器")
                continue
        
        return False  # 默认不重启
    
    try:
        # 在新线程中启动浏览器
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()
        
        # 在新线程中启动Flask服务器
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # 在主线程中处理命令
        should_restart = handle_commands()
        
        # 如果需要重启，返回True
        return should_restart
        
    except Exception as e:
        logger.exception(f"服务器运行出错: {str(e)}")
        return False

def run_web_server(host='0.0.0.0', port=5000):
    """
    运行Web服务器
    """
    global analyzer, watchlists, logger
    
    # 设置日志
    logger = setup_logging(False)
    
    # 创建分析器
    analyzer = StockAnalyzer()
    
    # 加载观察列表
    watchlists = load_watchlists()
    
    def handle_port_conflict(port):
        """处理端口冲突"""
        pid = check_port(port)
        if pid:
            while True:
                print(f"\n发现端口 {port} 被占用")
                print(f"占用进程 PID: {pid}")
                print("\n请选择操作：")
                print("1. 关闭旧实例并启动新服务器")
                print("2. 使用其他端口")
                print("3. 退出程序")
                
                choice = input("\n请输入选项（1-3）: ").strip()
                
                if choice == '1':
                    if cleanup_port(port):
                        print(f"\n成功关闭旧实例")
                        time.sleep(1)  # 等待端口完全释放
                        return port
                    else:
                        print(f"\n无法自动关闭旧实例")
                        continue
                elif choice == '2':
                    while True:
                        try:
                            new_port = input("\n请输入新端口号（1024-65535）: ").strip()
                            new_port = int(new_port)
                            if 1024 <= new_port <= 65535:
                                if check_port(new_port):
                                    print(f"\n端口 {new_port} 也被占用，请选择其他端口")
                                    continue
                                return new_port
                            else:
                                print("\n端口号必须在1024-65535之间")
                        except ValueError:
                            print("\n请输入有效的端口号")
                elif choice == '3':
                    print("\n程序已退出")
                    sys.exit(0)
                else:
                    print("\n无效的选项，请重新选择")
        return port
    
    try:
        while True:
            # 检查端口占用并处理
            final_port = handle_port_conflict(port)
            if final_port != port:
                print(f"\n将使用端口 {final_port} 启动服务器")
            
            # 启动服务器
            should_restart = start_server(host, final_port)
            
            # 如果不需要重启，直接返回
            if not should_restart:
                return
            
            # 如果需要重启，继续循环
            print("\n正在重启服务器...")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        return
    except Exception as e:
        logger.exception(f"启动Web服务器时发生错误: {str(e)}")
        return

if __name__ == "__main__":
    try:
        run_web_server(port=3336)
    except KeyboardInterrupt:
        print("\n\n程序已终止")
        sys.exit(0) 