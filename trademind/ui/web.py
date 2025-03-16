"""
TradeMind Lite - Web界面

本模块提供TradeMind Lite的Web界面，允许用户通过浏览器执行股票分析和报告生成。
"""

import sys
import os
import time
import threading
import socket
import signal
import webbrowser
import json
import logging
import subprocess
import platform
import re
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote
import psutil
import requests

import pandas as pd
import numpy as np
import warnings
import pytz
import yfinance as yf

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
from flask_cors import CORS

from trademind.core.indicators import calculate_rsi, calculate_macd, calculate_kdj, calculate_bollinger_bands
from trademind.core.signals import generate_signals
from trademind.backtest import run_backtest
from trademind.core.patterns import identify_candlestick_patterns
from trademind.core.analyzer import StockAnalyzer
from trademind.reports.generator import generate_html_report as generate_report
from trademind.data.loader import get_stock_data, get_stock_info, validate_stock_code, batch_validate_stock_codes, update_watchlists_file, get_user_watchlists, save_user_watchlists, import_stocks_to_watchlist
from trademind import compat
from trademind import __version__

# 创建Flask应用
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)  # 启用CORS支持
app.secret_key = 'trademind_lite_secret_key'  # 设置session密钥

# 全局变量
watchlists = {}  # 自选股列表
reports_cache = []  # 报告缓存
last_refresh_time = 0  # 上次刷新报告缓存的时间

# 分析进度信息
analysis_progress = {
    "in_progress": False,
    "percent": 0,
    "current_symbol": None,
    "current_index": 0,
    "total": 0,
    "remaining_seconds": None,
    "report_url": None,
    "report_path": None,
    "timestamp": None,
    "last_report_path": None
}

# 自动整理进度信息
organize_progress = {
    'in_progress': False,
    'percent': 0,
    'status': '准备中...',
    'completed': False
}

logger = None
server_running = None

@app.route('/')
def index():
    """渲染主页"""
    # 设置默认用户ID
    if 'user_id' not in session:
        session['user_id'] = 'default'
        
    # 加载自选股列表
    load_watchlists()
    
    # 渲染模板
    return render_template('index.html', watchlists=watchlists)

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
            global analysis_progress, analyzer
            try:
                # 确保analyzer已初始化
                if analyzer is None:
                    analyzer = StockAnalyzer()
                
                # 重写analyze_stocks方法，添加进度跟踪
                results = []
                total = len(symbols)
                
                for index, symbol in enumerate(symbols, 1):
                    # 检查服务器是否已停止
                    if not server_running.is_set():
                        print("\n检测到服务器停止信号，正在安全终止分析...")
                        break
                        
                    try:
                        # 更新进度信息
                        analysis_progress["current_index"] = index
                        analysis_progress["current_symbol"] = f"{names.get(symbol, symbol)} ({symbol})"
                        analysis_progress["percent"] = index / total
                        
                        # 修复显示问题，确保正确显示股票名称和代码
                        stock_name = names.get(symbol, symbol)
                        if isinstance(stock_name, dict) and 'name' in stock_name:
                            # 如果名称是一个字典，提取实际名称
                            display_name = stock_name['name']
                            display_code = stock_name.get('yf_code', symbol)
                            print(f"\n[{index}/{total} - {index/total*100:.1f}%] 分析: {display_name} ({display_code})")
                        else:
                            # 正常显示名称和代码
                            print(f"\n[{index}/{total} - {index/total*100:.1f}%] 分析: {stock_name} ({symbol})")
                        
                        # 使用正确的代码获取股票数据
                        yf_code = symbol
                        if isinstance(stock_name, dict) and stock_name.get('yf_code'):
                            yf_code = stock_name['yf_code']
                        
                        stock = yf.Ticker(yf_code)
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
                        # 创建StockAnalyzer实例并调用形态识别方法
                        patterns = analyzer.identify_patterns(hist.tail(5))
                        
                        print("生成交易建议...")
                        # 调用StockAnalyzer的交易建议生成方法
                        advice = analyzer.generate_trading_advice(indicators, current_price, patterns)
                        
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
                if results and server_running.is_set():  # 只有在服务器仍在运行且有结果时才生成报告
                    report_path = analyzer.generate_report(results, title)
                    analysis_progress["last_report_path"] = report_path
                
                # 更新分析状态
                analysis_progress["in_progress"] = False
                analysis_progress["percent"] = 1.0
                
                # 检查服务器是否已停止
                if not server_running.is_set():
                    print("\n分析已完成，但服务器已停止，不生成报告")
                
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
    """列出所有自选股列表"""
    try:
        # 获取当前用户ID
        user_id = session.get('user_id', 'default')
        
        # 获取用户的自选股列表
        user_watchlists = get_user_watchlists(user_id)
        
        # 更新全局变量
        global watchlists
        watchlists = user_watchlists
        
        return jsonify({
            'success': True,
            'watchlists': watchlists
        })
    except Exception as e:
        logger.exception(f"列出自选股列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate-stock', methods=['POST'])
def validate_stock():
    """验证单个股票代码"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        translate = data.get('translate', True)
        
        if not code:
            return jsonify({'error': '股票代码不能为空'}), 400
            
        result = validate_stock_code(code, translate=translate)
        return jsonify(result)
    except Exception as e:
        logger.exception(f"验证股票代码时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-stocks', methods=['POST'])
def validate_stocks():
    """批量验证股票代码"""
    try:
        data = request.get_json()
        codes = data.get('codes', [])
        market = data.get('market', 'US')
        translate = data.get('translate', True)  # 默认启用翻译
        
        if not codes:
            return jsonify({'error': '股票代码列表不能为空'}), 400
            
        # 限制一次验证的数量
        if len(codes) > 100:
            return jsonify({'error': '一次最多验证100个股票代码'}), 400
            
        results = batch_validate_stock_codes(codes, market, translate=translate)
        
        # 统计验证结果
        valid_count = sum(1 for r in results if r.get('valid', False))
        invalid_count = len(results) - valid_count
        
        return jsonify({
            'results': results,
            'summary': {
                'total': len(results),
                'valid': valid_count,
                'invalid': invalid_count
            }
        })
    except Exception as e:
        logger.exception(f"批量验证股票代码时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-watchlist', methods=['POST'])
def import_watchlist():
    """导入自选股列表"""
    try:
        data = request.get_json()
        stocks = data.get('stocks', [])
        group_name = data.get('groupName', '')
        auto_categories = data.get('autoCategories', False)
        
        if not stocks:
            return jsonify({'success': False, 'error': '没有有效的股票可导入'}), 400
            
        # 验证分组信息
        if not auto_categories and not group_name:
            return jsonify({'success': False, 'error': '请选择自动分类或者指定分组名称'}), 400
            
        # 获取当前用户
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '用户未登录'}), 401
            
        # 导入股票
        result = import_stocks_to_watchlist(
            user_id=user_id,
            stocks=stocks,
            group_name=group_name,
            auto_categories=auto_categories
        )
        
        if result['success']:
            # 获取更新后的自选股列表
            watchlists = get_user_watchlists(user_id)
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {result["imported_count"]} 个股票到自选股列表',
                'watchlists': watchlists
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.exception(f"导入自选股列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/parse-stock-text', methods=['POST'])
def parse_stock_text():
    """解析股票文本"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
            
        # 解析文本，提取股票代码
        codes = parse_stock_text_content(text)
        
        if not codes:
            return jsonify({'error': '未能解析出有效的股票代码'}), 400
            
        return jsonify({
            'success': True,
            'codes': codes
        })
    except Exception as e:
        logger.exception(f"解析股票文本时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

def parse_stock_text_content(text):
    """
    解析股票文本内容，提取股票代码
    
    参数:
        text: 包含股票代码的文本
        
    返回:
        list: 提取的股票代码列表
    """
    codes = []
    
    # 替换所有分隔符为空格
    text = re.sub(r'[,\t\n;|]+', ' ', text)
    
    # 分割并过滤空字符串
    for item in text.split():
        # 提取可能的股票代码（去除非字母数字字符）
        code = re.sub(r'[^A-Za-z0-9\.\^]', '', item)
        if code:
            codes.append(code)
    
    return codes

@app.route('/api/auto-organize-watchlist', methods=['POST'])
def auto_organize_watchlist():
    """自动整理自选股列表"""
    try:
        # 重置进度信息
        global organize_progress
        organize_progress = {
            'in_progress': True,
            'percent': 5,
            'status': '正在初始化整理过程...',
            'completed': False
        }
        
        # 读取现有的watchlists.json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'watchlists.json')
        
        # 更新进度
        organize_progress['percent'] = 8
        organize_progress['status'] = '正在读取自选股列表...'
        
        with open(config_path, 'r', encoding='utf-8') as f:
            watchlists_data = json.load(f)
        
        # 更新进度
        organize_progress['percent'] = 12
        organize_progress['status'] = '正在备份原文件...'
        
        # 备份原文件
        backup_path = config_path + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(watchlists_data, f, ensure_ascii=False, indent=4)
        
        # 统计信息
        stats = {
            'groups': 0,
            'stocks': 0,
            'translated': 0,
            'fixed': 0
        }
        
        # 更新进度
        organize_progress['percent'] = 15
        organize_progress['status'] = '正在收集股票代码...'
        
        # 收集所有股票代码
        all_stocks = []
        for group, stocks in watchlists_data.items():
            for symbol, name in stocks.items():
                all_stocks.append({
                    'symbol': symbol,
                    'name': name,
                    'group': group
                })
                stats['stocks'] += 1
        
        # 更新进度
        organize_progress['percent'] = 20
        organize_progress['status'] = f'准备验证{stats["stocks"]}个股票代码...'
        
        # 批量验证所有股票
        validated_stocks = []
        batch_size = 20
        total_batches = (len(all_stocks) + batch_size - 1) // batch_size
        
        for i in range(0, len(all_stocks), batch_size):
            batch_index = i // batch_size
            batch = all_stocks[i:i+batch_size]
            symbols = [stock['symbol'] for stock in batch]
            
            # 更新进度 - 验证阶段占40%的进度(20%-60%)
            progress_percent = 20 + (batch_index / total_batches) * 40
            organize_progress['percent'] = progress_percent
            
            # 每个批次使用不同的状态消息，使界面更加动态
            if batch_index % 5 == 0:
                organize_progress['status'] = f'正在验证股票代码有效性 ({i+1}-{min(i+batch_size, len(all_stocks))}/{len(all_stocks)})...'
            elif batch_index % 5 == 1:
                organize_progress['status'] = f'正在查询股票信息和最新数据 ({i+1}-{min(i+batch_size, len(all_stocks))}/{len(all_stocks)})...'
            elif batch_index % 5 == 2:
                organize_progress['status'] = f'正在翻译股票名称为中文 ({i+1}-{min(i+batch_size, len(all_stocks))}/{len(all_stocks)})...'
            elif batch_index % 5 == 3:
                organize_progress['status'] = f'正在修复无效的股票代码 ({i+1}-{min(i+batch_size, len(all_stocks))}/{len(all_stocks)})...'
            else:
                organize_progress['status'] = f'正在处理特殊格式的股票代码 ({i+1}-{min(i+batch_size, len(all_stocks))}/{len(all_stocks)})...'
            
            # 验证股票代码
            results = batch_validate_stock_codes(symbols, 'US', translate=True)
            
            # 处理验证结果
            for j, result in enumerate(results):
                stock = batch[j]
                
                if result.get('valid', False):
                    # 有效股票
                    validated_stock = {
                        'valid': True,
                        'original': stock['symbol'],
                        'converted': result.get('converted', stock['symbol']),
                        'name': result.get('name', stock['name']),
                        'chineseName': result.get('chineseName', ''),
                        'category': result.get('category', '其他股票'),
                        'originalGroup': stock['group']
                    }
                    
                    # 检查是否有中文名称
                    if validated_stock['chineseName'] and validated_stock['chineseName'] != validated_stock['name']:
                        stats['translated'] += 1
                    
                    validated_stocks.append(validated_stock)
                else:
                    # 尝试修复无效股票
                    fixed = False
                    
                    # 尝试不同的修复方法
                    if stock['symbol'].startswith('.'):
                        # 可能是指数，尝试转换为^格式
                        fixed_symbol = '^' + stock['symbol'][1:]
                        fixed_result = validate_stock_code(fixed_symbol, 'US')
                        if fixed_result.get('valid', False):
                            fixed = True
                            stats['fixed'] += 1
                            validated_stocks.append({
                                'valid': True,
                                'original': stock['symbol'],
                                'converted': fixed_result.get('converted', fixed_symbol),
                                'name': fixed_result.get('name', stock['name']),
                                'chineseName': fixed_result.get('chineseName', ''),
                                'category': fixed_result.get('category', '指数与ETF'),
                                'originalGroup': stock['group']
                            })
                    
                    if not fixed:
                        # 无法修复，保留原始信息
                        validated_stocks.append({
                            'valid': False,
                            'original': stock['symbol'],
                            'reason': result.get('reason', '无效股票代码'),
                            'originalGroup': stock['group']
                        })
            
            # 避免API限制
            time.sleep(0.5)
            
            # 每处理完一批次，稍微增加一点进度，让用户感觉到系统在持续工作
            organize_progress['percent'] += 0.5
        
        # 更新进度 - 分类阶段
        organize_progress['percent'] = 65
        organize_progress['status'] = '正在智能分类股票到不同分组...'
        
        # 按分类整理股票
        categorized_stocks = {}
        valid_stocks = [s for s in validated_stocks if s.get('valid', False)]
        total_valid = len(valid_stocks)
        
        # 分类处理进度 - 占20%的进度(65%-85%)
        for i, stock in enumerate(valid_stocks):
            if stock.get('valid', False):
                category = stock.get('category', '其他股票')
                
                if category not in categorized_stocks:
                    categorized_stocks[category] = {}
                    stats['groups'] += 1
                    
                    # 每创建一个新分组，更新一下状态
                    organize_progress['status'] = f'创建分组: {category}...'
                
                symbol = stock.get('converted')
                
                # 优先使用中文名称
                if stock.get('chineseName'):
                    name = stock.get('chineseName')
                else:
                    name = stock.get('name', symbol)
                
                categorized_stocks[category][symbol] = name
            
            # 每处理10个股票，更新一次进度
            if i % 10 == 0 and total_valid > 0:
                progress = 65 + (i / total_valid) * 20
                organize_progress['percent'] = progress
        
        # 更新进度 - 写入文件阶段
        organize_progress['percent'] = 85
        organize_progress['status'] = '正在写入更新后的文件...'
        
        # 写入更新后的文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(categorized_stocks, f, ensure_ascii=False, indent=4)
        
        # 更新进度 - 更新全局变量
        organize_progress['percent'] = 95
        organize_progress['status'] = '正在更新系统配置...'
        
        # 更新全局变量
        global watchlists
        watchlists = categorized_stocks
        
        # 完成进度
        organize_progress['percent'] = 100
        organize_progress['status'] = '整理完成！所有股票已成功分类并保存。'
        organize_progress['in_progress'] = False
        organize_progress['completed'] = True
        
        return jsonify({
            'success': True,
            'message': f'成功整理自选股列表！共整理了{stats["stocks"]}个股票，分为{stats["groups"]}个分组，翻译了{stats["translated"]}个名称，修复了{stats["fixed"]}个无效代码。',
            'stats': stats,
            'watchlists': categorized_stocks
        })
    except Exception as e:
        # 更新进度为错误状态
        organize_progress['in_progress'] = False
        organize_progress['status'] = f'出错: {str(e)}'
        organize_progress['completed'] = False
        
        logger.exception(f"自动整理自选股列表时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-organize-progress', methods=['GET'])
def auto_organize_progress():
    """获取自动整理进度"""
    global organize_progress
    return jsonify(organize_progress)

@app.route('/api/cancel-validation', methods=['POST'])
def cancel_validation():
    """取消正在进行的验证过程"""
    try:
        # 这里可以添加取消验证的逻辑，如果有后台任务正在运行
        # 例如，设置一个全局标志，让验证过程检查这个标志并提前退出
        
        return jsonify({
            'success': True,
            'message': '验证过程已取消'
        })
    except Exception as e:
        logger.exception(f"取消验证过程时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-watchlist-groups', methods=['GET'])
def get_watchlist_groups():
    """获取自选股分组列表"""
    try:
        # 获取当前用户ID
        user_id = session.get('user_id', 'default')
        
        # 获取用户的自选股列表
        user_watchlists = get_user_watchlists(user_id)
        
        # 提取分组名称和股票数量
        groups = {}
        for group_name, stocks in user_watchlists.items():
            groups[group_name] = len(stocks)
        
        return jsonify({
            'success': True,
            'groups': groups
        })
    except Exception as e:
        logger.exception(f"获取自选股分组列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clean', methods=['POST'])
def clean_reports():
    """
    清理报告API
    """
    try:
        days = request.form.get('days', '30')
        force_all = request.form.get('force_all', 'false').lower() == 'true'
        
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        # 获取报告目录
        reports_dir = analyzer.results_path
        
        # 如果目录不存在，创建它
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            return jsonify({'success': True, 'message': '没有报告需要清理'})
        
        # 获取当前时间
        now = datetime.now()
        
        # 计算删除的文件数量
        deleted_count = 0
        
        # 遍历报告目录
        for filename in os.listdir(reports_dir):
            file_path = os.path.join(reports_dir, filename)
            
            # 只处理HTML文件
            if not filename.endswith('.html'):
                continue
                
            # 如果强制删除所有，直接删除
            if force_all:
                os.remove(file_path)
                deleted_count += 1
                continue
                
            # 获取文件修改时间
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # 计算文件年龄（天）
            file_age = (now - file_time).days
            
            # 如果文件年龄大于指定天数，删除它
            if file_age >= days:
                os.remove(file_path)
                deleted_count += 1
        
        # 返回成功消息
        return jsonify({
            'success': True, 
            'message': f'成功清理 {deleted_count} 个报告文件'
        })
        
    except Exception as e:
        logger.exception(f"清理报告时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    """
    关闭服务器API
    """
    global server_running, analysis_progress
    try:
        # 设置服务器停止标志
        if 'server_running' in globals() and server_running is not None:
            server_running.clear()
            # 如果正在分析，标记分析为已完成
            if analysis_progress["in_progress"]:
                analysis_progress["in_progress"] = False
                print("\n浏览器已关闭，但分析任务正在进行。正在安全停止...")
            else:
                print("\n浏览器已关闭，服务器正在停止...")
        return jsonify({'success': True, 'message': '服务器正在关闭'})
    except Exception as e:
        logger.exception(f"关闭服务器时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def refresh_reports_cache():
    """
    刷新报告缓存
    """
    # 获取报告目录
    # 这里可以添加任何需要的缓存刷新逻辑
    logger.info("刷新报告列表缓存")

def load_watchlists() -> Dict[str, Dict[str, str]]:
    """
    加载自选股列表
    
    返回:
        Dict[str, Dict[str, str]]: 自选股列表
    """
    global watchlists
    
    try:
        # 获取当前用户ID
        user_id = session.get('user_id', 'default')
        
        # 使用get_user_watchlists函数获取用户的自选股列表
        user_watchlists = get_user_watchlists(user_id)
        
        # 更新全局变量
        watchlists = user_watchlists
        
        return watchlists
    except Exception as e:
        logger.error(f"加载自选股列表时出错: {str(e)}")
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
    global server_running
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
        last_check_time = time.time()
        check_interval = 1.0  # 每秒检查一次服务器状态
        
        while server_running.is_set():
            try:
                # 使用非阻塞的方式检查输入
                import select
                import sys
                
                # 检查是否有输入可用（非阻塞）
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)  # 0.5秒超时，更频繁地检查
                
                # 定期检查服务器状态，即使没有用户输入
                current_time = time.time()
                if current_time - last_check_time >= check_interval:
                    last_check_time = current_time
                    if not server_running.is_set():
                        print("\n检测到浏览器已关闭，服务器正在停止...")
                        print("服务器已停止，返回主菜单...")
                        return False
                
                # 如果有输入可用
                if ready:
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
        
        # 如果服务器停止了，自动返回到主菜单
        print("\n服务器已停止，返回主菜单...")
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