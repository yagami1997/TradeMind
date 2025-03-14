"""
TradeMind Lite（轻量版）- 分析器模块

本模块包含主要的股票分析协调器，负责调用各个功能模块完成分析工作。
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import json
import warnings
import os
import sys
import time

from trademind.core.indicators import (
    calculate_rsi, 
    calculate_macd, 
    calculate_kdj, 
    calculate_bollinger_bands
)
from trademind.core.patterns import identify_candlestick_patterns
from trademind.core.signals import generate_trading_advice, generate_signals
from trademind.backtest.engine import run_backtest
from trademind.reports.generator import generate_html_report, generate_performance_charts

# 忽略警告
warnings.filterwarnings('ignore', category=Warning)
warnings.filterwarnings('ignore', category=RuntimeWarning)


class StockAnalyzer:
    """
    股票分析器类 - 作为各功能模块的协调器
    
    该类负责协调各个功能模块完成股票分析工作，包括：
    - 技术指标计算
    - 形态识别
    - 信号生成
    - 回测
    - 报告生成
    """
    
    def __init__(self):
        """初始化股票分析器"""
        self.setup_logging()
        self.setup_paths()
        self.setup_colors()
    
    def setup_logging(self):
        """设置日志记录"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/stock_analyzer.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("stock_analyzer")
    
    def setup_paths(self):
        """设置路径"""
        self.results_path = Path("reports/stocks")
        self.results_path.mkdir(parents=True, exist_ok=True)
    
    def setup_colors(self):
        """设置颜色方案"""
        self.colors = {
            "primary": "#1976D2",
            "secondary": "#0D47A1",
            "success": "#2E7D32",
            "warning": "#F57F17",
            "danger": "#C62828",
            "info": "#0288D1",
            "background": "#FFFFFF",
            "text": "#212121",
            "card": "#FFFFFF",
            "border": "#E0E0E0",
            "gradient_start": "#1976D2",
            "gradient_end": "#0D47A1",
            "strong_buy": "#00796B",
            "buy": "#26A69A",
            "strong_sell": "#D32F2F",
            "sell": "#EF5350",
            "neutral": "#FFA000"
        }
    
    def analyze_stocks(self, symbols: List[str], names: Dict[str, str] = None) -> List[Dict]:
        """
        分析多只股票
        
        参数:
            symbols: 股票代码列表
            names: 股票名称字典，格式为 {代码: 名称}
            
        返回:
            List[Dict]: 分析结果列表
        """
        if names is None:
            names = {}
            
        results = []
        total = len(symbols)
        print("\n开始技术分析...")
        
        for index, symbol in enumerate(symbols, 1):
            try:
                print(f"\n[{index}/{total} - {index/total*100:.1f}%] 分析: {names.get(symbol, symbol)} ({symbol})")
                
                # 获取股票数据
                hist = self.get_stock_data(symbol)
                
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
                        # 打印调试信息
                        print(f"计算涨跌幅 - 当前价格: {current_price:.2f}, 前一收盘价: {prev_price:.2f}")
                        print(f"计算涨跌幅 - 价格变化: {price_change:.2f}, 变化百分比: {price_change_pct:.2f}%")
                    else:
                        price_change_pct = 0.0
                        print(f"计算涨跌幅 - 前一收盘价为零或负值: {prev_price:.2f}, 使用默认值0.0%")
                else:
                    # 如果只有一天数据，尝试使用当天的开盘价和收盘价
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Open'].iloc[-1]
                        price_change = current_price - prev_price
                        # 确保除数不为零
                        if prev_price > 0:
                            price_change_pct = (price_change / prev_price) * 100
                            print(f"计算涨跌幅(单日) - 收盘价: {current_price:.2f}, 开盘价: {prev_price:.2f}")
                            print(f"计算涨跌幅(单日) - 价格变化: {price_change:.2f}, 变化百分比: {price_change_pct:.2f}%")
                        else:
                            price_change_pct = 0.0
                            print(f"计算涨跌幅(单日) - 开盘价为零或负值: {prev_price:.2f}, 使用默认值0.0%")
                    else:
                        current_price = 0.0
                        prev_price = 0.0
                        price_change = 0.0
                        price_change_pct = 0.0
                        print("计算涨跌幅 - 无历史数据，使用默认值0.0%")
                
                # 确保价格变化百分比不是NaN或无穷大
                if pd.isna(price_change_pct) or np.isinf(price_change_pct):
                    price_change_pct = 0.0
                    print(f"计算涨跌幅 - 结果为NaN或无穷大，使用默认值0.0%")
                
                # 打印最终使用的涨跌幅
                print(f"最终涨跌幅: {price_change_pct:.2f}%")
                
                print("计算技术指标...")
                # 计算技术指标
                indicators = self.calculate_indicators(hist)
                
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
                
                # 确保回测结果包含所有必要的字段
                if 'total_trades' not in backtest_results or backtest_results['total_trades'] == 0:
                    # 如果没有足够的数据进行回测，提供一些基本信息
                    backtest_results = {
                        'total_trades': 0,
                        'win_rate': 0,
                        'avg_profit': 0.00,
                        'max_profit': 0.00,
                        'max_loss': 0.00,
                        'profit_factor': 0.00,
                        'max_drawdown': 0.00,
                        'consecutive_losses': 0,
                        'avg_hold_days': 0,
                        'final_return': 0.00,
                        'sharpe_ratio': 0.00,
                        'sortino_ratio': 0.00,
                        'net_profit': 0.00,
                        'annualized_return': 0.00
                    }
                
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
                self.logger.error(f"分析 {symbol} 时出错", exc_info=True)
                print(f"❌ {symbol} 分析失败: {str(e)}")
                continue
        
        return results
    
    def generate_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        """
        生成HTML分析报告
        
        参数:
            results: 分析结果列表
            title: 报告标题
            
        返回:
            str: HTML报告文件路径
        """
        # 调用报告生成模块
        return generate_html_report(results, title, output_dir=self.results_path)
    
    def analyze_and_report(self, symbols: List[str], names: Dict[str, str] = None, title: str = "股票分析报告") -> str:
        """
        分析股票并生成报告
        
        参数:
            symbols: 股票代码列表
            names: 股票名称字典，格式为 {代码: 名称}
            title: 报告标题
            
        返回:
            str: HTML报告文件路径
        """
        results = self.analyze_stocks(symbols, names)
        if not results:
            print("❌ 没有可用的分析结果")
            return None
        
        print("\n生成分析报告...")
        report_path = self.generate_report(results, title)
        print(f"✅ 报告已生成: {report_path}")
        
        return report_path
    
    def clean_reports(self, days_threshold: int = 30):
        """
        清理旧的报告文件
        
        参数:
            days_threshold: 保留的天数阈值，默认30天。如果为None，则删除所有报告。
        """
        if not self.results_path.exists():
            print("报告目录不存在")
            return 0
        
        now = datetime.now()
        count = 0
        
        # 打印调试信息
        print(f"开始清理报告，阈值: {days_threshold if days_threshold is not None else '全部删除'}天")
        print(f"报告目录: {self.results_path}")
        
        # 检查stocks子目录
        stocks_path = self.results_path / "stocks"
        if stocks_path.exists():
            print(f"股票报告目录: {stocks_path}")
        
        # 递归遍历目录，找出所有HTML文件
        all_files = []
        
        # 主报告目录中的HTML文件
        main_html_files = list(self.results_path.glob("*.html"))
        all_files.extend(main_html_files)
        
        # stocks子目录中的HTML文件
        if stocks_path.exists():
            stocks_html_files = list(stocks_path.glob("*.html"))
            all_files.extend(stocks_html_files)
            
            # 递归查找子目录中的文件
            for subdir in stocks_path.glob("**/"):
                if subdir != stocks_path:  # 避免重复
                    subdir_files = list(subdir.glob("*.html"))
                    all_files.extend(subdir_files)
        
        print(f"找到 {len(all_files)} 个报告文件")
        
        for file in all_files:
            try:
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                days_old = (now - file_time).days
                
                print(f"检查文件: {file.name}, 创建于: {file_time}, 已有 {days_old} 天")
                
                # 如果days_threshold为None或者文件超过阈值天数，则删除
                if days_threshold is None or days_old > days_threshold:
                    print(f"删除文件: {file}")
                    # 确保文件存在且可写
                    if file.exists():
                        try:
                            # 使用os.remove而不是Path.unlink，可能更可靠
                            os.remove(str(file))
                            count += 1
                            print(f"已删除文件: {file}")
                        except PermissionError:
                            # 尝试修改权限后再删除
                            try:
                                os.chmod(str(file), 0o666)  # 设置读写权限
                                os.remove(str(file))
                                count += 1
                                print(f"修改权限后已删除文件: {file}")
                            except Exception as e2:
                                print(f"修改权限后仍无法删除文件 {file}: {str(e2)}")
                                
                                # 尝试使用系统命令删除
                                try:
                                    import subprocess
                                    if os.name == 'nt':  # Windows
                                        cmd = f'del /F /Q "{file}"'
                                    else:  # Unix/Linux/Mac
                                        cmd = f'rm -f "{file}"'
                                    
                                    print(f"尝试使用系统命令删除: {cmd}")
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                    
                                    if result.returncode == 0:
                                        count += 1
                                        print(f"使用系统命令成功删除文件: {file}")
                                    else:
                                        print(f"系统命令删除失败: {result.stderr}")
                                except Exception as e3:
                                    print(f"使用系统命令删除失败: {str(e3)}")
                        except Exception as e:
                            print(f"删除文件失败: {str(e)}")
                    else:
                        print(f"文件不存在: {file}")
            except Exception as e:
                print(f"处理文件 {file} 时出错: {str(e)}")
                self.logger.error(f"处理文件 {file} 时出错: {str(e)}")
        
        print(f"已删除 {count} 个{'所有' if days_threshold is None else f'超过 {days_threshold} 天的旧'}报告")
        return count  # 返回删除的文件数量，方便前端显示

    def analyze_stock(self, symbol: str, period: str = '1y', interval: str = '1d') -> Dict:
        """
        分析单个股票
        
        参数:
            symbol: 股票代码
            period: 数据周期，如1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: 数据间隔，如1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            
        返回:
            Dict: 分析结果
        """
        try:
            # 获取股票数据
            data = self.get_stock_data(symbol)
            if data.empty:
                return self._get_empty_result(symbol)
            
            # 获取股票信息
            info = self.get_stock_info(symbol)
            
            # 获取当前价格和名称
            current_price = data['Close'].iloc[-1]
            stock_name = info.get('shortName', symbol)
            
            # 计算价格变化 - 修复价格变化百分比计算
            if len(data) > 1:
                prev_close = data['Close'].iloc[-2]
                price_change = current_price - prev_close
                price_change_pct = (price_change / prev_close * 100) if prev_close > 0 else 0
            else:
                # 如果只有一天数据，使用开盘价计算
                prev_close = data['Open'].iloc[-1]
                price_change = current_price - prev_close
                price_change_pct = (price_change / prev_close * 100) if prev_close > 0 else 0
            
            # 确保价格变化百分比不是NaN或无穷大
            if pd.isna(price_change_pct) or np.isinf(price_change_pct):
                price_change_pct = 0.0
            
            # 计算技术指标
            indicators = self.calculate_indicators(data)
            
            # 识别K线形态
            patterns = self.identify_patterns(data)
            
            # 生成交易建议
            advice = self.generate_trading_advice(indicators, current_price, patterns)
            
            # 执行回测
            backtest_results = self.backtest_strategy(data)
            
            # 构建结果
            result = {
                'symbol': symbol,
                'name': stock_name,
                'price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'prev_close': prev_close,
                'indicators': indicators,
                'patterns': patterns,
                'advice': advice,
                'backtest': backtest_results,
                'data': {
                    'dates': data.index.tolist(),
                    'open': data['Open'].tolist(),
                    'high': data['High'].tolist(),
                    'low': data['Low'].tolist(),
                    'close': data['Close'].tolist(),
                    'volume': data['Volume'].tolist() if 'Volume' in data.columns else []
                }
            }
            
            return result
        except Exception as e:
            self.logger.error(f"分析股票 {symbol} 时出错: {str(e)}")
            return self._get_empty_result(symbol)

    def _get_empty_result(self, symbol: str) -> Dict:
        """
        生成空的分析结果
        
        参数:
            symbol: 股票代码
            
        返回:
            Dict: 空的分析结果
        """
        return {
            'symbol': symbol,
            'name': symbol,
            'price': 0.0,
            'price_change': 0.0,
            'price_change_pct': 0.0,
            'prev_close': 0.0,
            'indicators': {},
            'patterns': [],
            'advice': {'advice': '数据不足', 'confidence': 0, 'signals': []},
            'backtest': {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0.00,
                'max_profit': 0.00,
                'max_loss': 0.00,
                'profit_factor': 0.00,
                'max_drawdown': 0.00,
                'consecutive_losses': 0,
                'avg_hold_days': 0,
                'final_return': 0.00,
                'sharpe_ratio': 0.00,
                'sortino_ratio': 0.00,
                'annualized_return': 0.00
            },
            'data': {
                'dates': [],
                'open': [],
                'high': [],
                'low': [],
                'close': [],
                'volume': []
            }
        }

    def get_stock_info(self, symbol: str) -> Dict:
        """
        获取股票信息
        
        参数:
            symbol: 股票代码
            
        返回:
            Dict: 股票信息
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return info
        except Exception as e:
            self.logger.error(f"获取 {symbol} 的信息时出错: {str(e)}")
            return {'shortName': symbol}

    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """
        获取股票历史数据
        
        参数:
            symbol: 股票代码
            
        返回:
            pd.DataFrame: 股票历史数据
        """
        try:
            # 获取更长时间的历史数据，确保有足够的数据进行回测
            stock = yf.Ticker(symbol)
            # 从2年的数据改为3年，确保有足够的数据进行回测
            hist = stock.history(period="3y")
            
            if hist.empty or len(hist) < 100:  # 确保至少有100个交易日的数据
                print(f"⚠️ {symbol} 的历史数据不足，尝试获取最大可用数据")
                # 尝试获取最大可用数据
                hist = stock.history(period="max")
            
            return hist
        except Exception as e:
            self.logger.error(f"获取 {symbol} 的历史数据时出错: {str(e)}")
            print(f"❌ 获取 {symbol} 的历史数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """
        计算技术指标
        
        参数:
            data: 股票历史数据
            
        返回:
            Dict: 技术指标字典
        """
        try:
            # 计算RSI
            rsi = calculate_rsi(data['Close'])
            
            # 计算MACD
            macd, signal, hist_macd = calculate_macd(data['Close'])
            
            # 计算KDJ
            k, d, j = calculate_kdj(data['High'], data['Low'], data['Close'])
            
            # 计算布林带
            bb_upper, bb_middle, bb_lower, bb_width, bb_percent = calculate_bollinger_bands(data['Close'])
            
            # 计算移动平均线
            sma5 = data['Close'].rolling(window=5).mean()
            sma10 = data['Close'].rolling(window=10).mean()
            sma20 = data['Close'].rolling(window=20).mean()
            sma50 = data['Close'].rolling(window=50).mean()
            sma200 = data['Close'].rolling(window=200).mean()
            
            # 构建指标字典
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
                },
                'sma5': sma5,
                'sma10': sma10,
                'sma20': sma20,
                'sma50': sma50,
                'sma200': sma200
            }
            
            return indicators
        except Exception as e:
            self.logger.error(f"计算技术指标时出错: {str(e)}")
            print(f"❌ 计算技术指标失败: {str(e)}")
            return {} 