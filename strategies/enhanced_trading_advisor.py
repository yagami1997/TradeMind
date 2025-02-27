# 标准库
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache
import json
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 第三方库
import numpy as np

# 项目模块
sys.path.append(str(Path(__file__).parent.parent))
from strategies.tech_indicator_calculator import TechIndicatorCalculator
from core.strategy_manager import StrategyManager
from watchlist.watchlist_manager import WatchlistManager
from data.data_manager_yf import YahooFinanceManager

class EnhancedTradingAdvisor:
    """增强型交易顾问：整合数据获取、技术分析和策略管理
    
    该类提供以下功能：
    - 数据获取和管理
    - 技术指标计算
    - 策略应用和评估
    - 交易信号生成
    - 报告生成和缓存
    
    Attributes:
        data_manager: 数据管理器
        strategy_manager: 策略管理器
        watchlist_manager: 观察列表管理器
        indicators: 技术指标计算器
        cache_timeout: 缓存超时时间（秒）
        logger: 日志记录器
    """
    
    def __init__(self):
        """初始化交易顾问"""
        self.setup_logging()
        self.data_manager = YahooFinanceManager()
        self.strategy_manager = StrategyManager()
        self.watchlist_manager = WatchlistManager()
        self.setup_paths()
        self.cache_timeout = 300  # 5分钟缓存
        self.indicators = TechIndicatorCalculator()
        
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(
            "logs/trading_advisor.log", 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        
    def setup_paths(self):
        """设置路径"""
        self.reports_path = Path("reports")
        self.reports_path.mkdir(parents=True, exist_ok=True)
        
    def analyze_stock(self, symbol: str, 
                     strategy_name: str = 'multi_factor',
                     strategy_params: Optional[Dict] = None) -> Dict:
        """
        分析单个股票
        
        Args:
            symbol (str): 股票代码
            strategy_name (str): 策略名称
            strategy_params (Dict, optional): 策略参数
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 获取数据
            df = self.data_manager.get_stock_data(symbol)
            if df is None or df.empty:
                self.logger.error(f"{symbol}: 无法获取数据")
                return None
                
            # 应用策略
            df = self.strategy_manager.apply_strategy(
                df, 
                strategy_name, 
                strategy_params
            )
            
            # 评估策略
            metrics = self.strategy_manager.evaluate_strategy(df)
            
            # 获取最新信号
            latest_signal = df['signal'].iloc[-1]
            latest_position = df['position'].iloc[-1]
            
            # 获取股票信息
            stock_info = self.data_manager.get_stock_info(symbol)
            
            return {
                'symbol': symbol,
                'name': stock_info.get('longName', symbol) if stock_info else symbol,
                'current_price': df['close'].iloc[-1],
                'signal': latest_signal,
                'position': latest_position,
                'metrics': metrics,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"{symbol}: 分析出错 - {str(e)}")
            return None
            
    def analyze_watchlist(self, 
                         watchlist_name: str,
                         strategy_name: str = 'multi_factor',
                         strategy_params: Optional[Dict] = None,
                         max_workers: int = 4) -> List[Dict]:
        """优化后的观察列表分析方法，支持并行处理"""
        try:
            symbols = self.watchlist_manager.get_watchlist(watchlist_name)
            if not symbols:
                self.logger.error(f"观察列表 {watchlist_name} 为空或不存在")
                return []
                
            results = []
            total = len(symbols)
            
            self.logger.info(f"开始分析观察列表 {watchlist_name} ({total}支股票)")
            
            # 使用线程池并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.analyze_stock, symbol, strategy_name, strategy_params): symbol
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        self.logger.error(f"{symbol}: 分析失败 - {str(e)}")
                        
            return results
            
        except Exception as e:
            self.logger.error(f"分析观察列表时出错: {str(e)}")
            return []
            
    def optimize_strategy(self, 
                         symbol: str,
                         strategy_name: str,
                         param_grid: Dict[str, List]) -> Dict:
        """
        优化策略参数
        
        Args:
            symbol (str): 股票代码
            strategy_name (str): 策略名称
            param_grid (Dict[str, List]): 参数网格
        """
        try:
            # 获取数据
            df = self.data_manager.get_stock_data(symbol)
            if df is None or df.empty:
                self.logger.error(f"{symbol}: 无法获取数据")
                return None
                
            # 优化参数
            result = self.strategy_manager.optimize_strategy_params(
                df, 
                strategy_name, 
                param_grid
            )
            
            return {
                'symbol': symbol,
                'strategy': strategy_name,
                'best_params': result['best_params'],
                'best_sharpe': result['best_sharpe'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"{symbol}: 策略优化出错 - {str(e)}")
            return None
            
    def compare_strategies(self, 
                         symbol: str,
                         strategy_list: List[str]) -> Dict:
        """
        比较多个策略
        
        Args:
            symbol (str): 股票代码
            strategy_list (List[str]): 策略列表
        """
        try:
            # 获取数据
            df = self.data_manager.get_stock_data(symbol)
            if df is None or df.empty:
                self.logger.error(f"{symbol}: 无法获取数据")
                return None
                
            # 比较策略
            result = self.strategy_manager.compare_strategies(df, strategy_list)
            
            return {
                'symbol': symbol,
                'strategies': strategy_list,
                'metrics': result['metrics'],
                'correlation': result['correlation'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"{symbol}: 策略比较出错 - {str(e)}")
            return None
            
    def generate_trading_signals(self, 
                               watchlist_name: str,
                               strategy_name: str = 'multi_factor',
                               min_confidence: float = 0.7) -> List[Dict]:
        """
        为观察列表生成交易信号
        
        Args:
            watchlist_name (str): 观察列表名称
            strategy_name (str): 策略名称
            min_confidence (float): 最小置信度
        """
        try:
            results = self.analyze_watchlist(watchlist_name, strategy_name)
            
            # 筛选高置信度信号
            signals = []
            for result in results:
                if result and abs(result['signal']) >= min_confidence:
                    signals.append({
                        'symbol': result['symbol'],
                        'name': result['name'],
                        'price': result['current_price'],
                        'action': 'buy' if result['signal'] > 0 else 'sell',
                        'confidence': abs(result['signal']),
                        'metrics': result['metrics']
                    })
            
            return signals
            
        except Exception as e:
            self.logger.error(f"生成交易信号时出错: {str(e)}")
            return []
            
    def generate_portfolio_report(self, 
                                watchlist_name: str,
                                strategy_name: str = 'multi_factor') -> Dict:
        """
        生成投资组合报告
        
        Args:
            watchlist_name (str): 观察列表名称
            strategy_name (str): 策略名称
        """
        try:
            results = self.analyze_watchlist(watchlist_name, strategy_name)
            
            if not results:
                return None
                
            # 计算组合指标
            total_returns = np.mean([r['metrics']['total_returns'] for r in results])
            sharpe_ratio = np.mean([r['metrics']['sharpe_ratio'] for r in results])
            max_drawdown = np.mean([r['metrics']['max_drawdown'] for r in results])
            
            # 按表现排序
            sorted_stocks = sorted(
                results,
                key=lambda x: x['metrics']['sharpe_ratio'],
                reverse=True
            )
            
            return {
                'watchlist_name': watchlist_name,
                'strategy': strategy_name,
                'portfolio_metrics': {
                    'total_returns': total_returns,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown
                },
                'top_performers': sorted_stocks[:5],
                'bottom_performers': sorted_stocks[-5:],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"生成组合报告时出错: {str(e)}")
            return None

    def generate_html_report(self, results: Dict, report_type: str = 'portfolio') -> str:
        """
        生成HTML格式的分析报告
        
        Args:
            results: 分析结果
            report_type: 报告类型 ('portfolio', 'single_stock', 'signals')
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.reports_path / f"{report_type}_report_{timestamp}.html"
            
            # 根据报告类型选择模板
            if report_type == 'portfolio':
                template = self._get_portfolio_template()
            elif report_type == 'single_stock':
                template = self._get_stock_template()
            else:
                template = self._get_signals_template()
            
            # 渲染HTML
            html_content = template.format(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **results
            )
            
            # 保存报告
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"生成HTML报告时出错: {str(e)}")
            return None

    @lru_cache(maxsize=100)
    def _get_cached_data(self, symbol: str, cache_key: str) -> Optional[Dict]:
        """获取缓存的数据"""
        cache_file = self.reports_path / 'cache' / f"{symbol}_{cache_key}.json"
        if cache_file.exists():
            if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).seconds < self.cache_timeout:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        return None
        
    def _cache_data(self, symbol: str, cache_key: str, data: Dict):
        """缓存数据"""
        cache_dir = self.reports_path / 'cache'
        cache_dir.mkdir(exist_ok=True)
        
        cache_file = cache_dir / f"{symbol}_{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f)

    def _get_portfolio_template(self) -> str:
        """获取投资组合报告模板"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>投资组合分析报告</title>
            <style>
                /* 添加CSS样式 */
            </style>
        </head>
        <body>
            <h1>投资组合分析报告</h1>
            <p>生成时间: {timestamp}</p>
            <!-- 添加更多模板内容 -->
        </body>
        </html>
        """

    def _get_stock_template(self) -> str:
        """获取单个股票分析报告模板"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>股票分析报告</title>
            <style>
                /* 添加CSS样式 */
            </style>
        </head>
        <body>
            <h1>股票分析报告</h1>
            <p>生成时间: {timestamp}</p>
            <!-- 添加更多模板内容 -->
        </body>
        </html>
        """

    def _get_signals_template(self) -> str:
        """获取交易信号报告模板"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>交易信号报告</title>
            <style>
                /* 添加CSS样式 */
            </style>
        </head>
        <body>
            <h1>交易信号报告</h1>
            <p>生成时间: {timestamp}</p>
            <!-- 添加更多模板内容 -->
        </body>
        </html>
        """

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enhanced Trading Advisor')
    parser.add_argument('--mode', choices=['single', 'watchlist', 'portfolio'],
                       default='single', help='分析模式')
    parser.add_argument('--symbol', help='股票代码')
    parser.add_argument('--watchlist', help='观察列表名称')
    parser.add_argument('--strategy', default='multi_factor', help='策略名称')
    
    args = parser.parse_args()
    
    advisor = EnhancedTradingAdvisor()
    
    try:
        if args.mode == 'single' and args.symbol:
            result = advisor.analyze_stock(args.symbol, args.strategy)
            if result:
                report_file = advisor.generate_html_report(result, 'single_stock')
                print(f"报告已生成: {report_file}")
                
        elif args.mode == 'watchlist' and args.watchlist:
            signals = advisor.generate_trading_signals(args.watchlist, args.strategy)
            if signals:
                report_file = advisor.generate_html_report({'signals': signals}, 'signals')
                print(f"信号报告已生成: {report_file}")
                
        elif args.mode == 'portfolio' and args.watchlist:
            report = advisor.generate_portfolio_report(args.watchlist, args.strategy)
            if report:
                report_file = advisor.generate_html_report(report, 'portfolio')
                print(f"组合报告已生成: {report_file}")
                
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        print(f"错误: {str(e)}")
