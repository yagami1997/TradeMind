import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, Callable, Any
import logging
from dataclasses import dataclass
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import jinja2
import weasyprint
import os
from pathlib import Path
import json
import itertools
from core.portfolio import Portfolio
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import threading
from queue import Queue
import time
from functools import partial

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreadPoolManager:
    """线程池管理器"""
    def __init__(self, max_workers: int = None, task_timeout: int = 30):
        """
        初始化线程池管理器
        
        Args:
            max_workers: 最大工作线程数，默认为 CPU 核心数 * 2
            task_timeout: 任务超时时间（秒）
        """
        self.max_workers = max_workers or (os.cpu_count() * 2)
        self.task_timeout = task_timeout
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.results_queue = Queue()
        self.lock = threading.Lock()
        
    def submit_task(self, task_func: Callable, *args, **kwargs) -> Any:
        """
        提交任务到线程池
        
        Args:
            task_func: 要执行的任务函数
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            future: Future对象
        """
        return self.executor.submit(task_func, *args, **kwargs)
        
    def process_batch(self, task_func: Callable, items: List[Any], 
                     callback: Callable = None, error_handler: Callable = None) -> List[Any]:
        """
        批量处理任务
        
        Args:
            task_func: 要执行的任务函数
            items: 要处理的项目列表
            callback: 可选的回调函数，处理每个任务的结果
            error_handler: 可选的错误处理函数
            
        Returns:
            List[Any]: 处理结果列表
        """
        futures = []
        results = []
        
        try:
            # 提交所有任务
            for item in items:
                future = self.submit_task(task_func, item)
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures, timeout=self.task_timeout):
                try:
                    result = future.result()
                    if callback:
                        result = callback(result)
                    results.append(result)
                except TimeoutError:
                    logger.error(f"任务执行超时")
                    if error_handler:
                        error_handler(TimeoutError("任务执行超时"))
                except Exception as e:
                    logger.error(f"任务执行出错: {str(e)}")
                    if error_handler:
                        error_handler(e)
                        
        except Exception as e:
            logger.error(f"批处理任务出错: {str(e)}")
            if error_handler:
                error_handler(e)
                
        return results
        
    def process_parallel(self, func: Callable, data: Dict[str, Any], 
                        chunk_size: int = None) -> Dict[str, Any]:
        """
        并行处理数据
        
        Args:
            func: 要执行的函数
            data: 要处理的数据字典
            chunk_size: 每个任务处理的数据量
            
        Returns:
            Dict[str, Any]: 处理结果字典
        """
        if chunk_size is None:
            chunk_size = max(1, len(data) // (self.max_workers * 2))
            
        results = {}
        chunks = [list(data.items())[i:i + chunk_size] 
                 for i in range(0, len(data), chunk_size)]
        
        def process_chunk(chunk):
            chunk_results = {}
            for key, value in chunk:
                try:
                    chunk_results[key] = func(value)
                except Exception as e:
                    logger.error(f"处理 {key} 时出错: {str(e)}")
            return chunk_results
        
        # 并行处理所有分块
        futures = [self.submit_task(process_chunk, chunk) for chunk in chunks]
        
        # 收集结果
        for future in as_completed(futures, timeout=self.task_timeout):
            try:
                chunk_results = future.result()
                with self.lock:
                    results.update(chunk_results)
            except Exception as e:
                logger.error(f"处理分块时出错: {str(e)}")
                
        return results
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=True)

@dataclass
class BacktestResult:
    """回测结果数据类"""
    period: str
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    profit_factor: float
    avg_profit_per_trade: float

@dataclass
class TradePosition:
    """交易位置数据类"""
    symbol: str
    position: float
    entry_price: float
    entry_time: datetime
    current_price: float
    pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class SlippageConfig:
    """滑点模型配置"""
    base_rate: float = 0.0002          # 基础滑点率
    volume_impact: float = 0.1         # 成交量影响因子
    max_volume_ratio: float = 0.1      # 最大成交量比例
    min_volume: int = 1000            # 最小可交易成交量
    max_slippage: float = 0.05        # 最大滑点率
    price_impact_factor: float = 0.3   # 价格影响因子
    volatility_multiplier: float = 1.5  # 波动率影响因子
    liquidity_threshold: float = 0.05   # 流动性阈值
    market_impact_decay: float = 0.85   # 市场冲击衰减因子
    min_tick_size: float = 0.01        # 最小价格变动单位
    
@dataclass
class TransactionCosts:
    """交易成本"""
    commission_rate: float  # 佣金率
    min_commission: float  # 最小佣金
    tax_rate: float = 0.001  # 印花税率
    
class Portfolio:
    """投资组合管理类"""
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, TradePosition] = {}
        self.trade_history: List[dict] = []
        self.daily_returns = []
        self.equity_curve = []
        self.transaction_costs = TransactionCosts()
        self.total_costs = 0.0  # 总交易成本
        
    def calculate_transaction_costs(self, price: float, quantity: float, is_buy: bool) -> float:
        """计算交易成本（包括佣金、印花税和滑点）"""
        # 计算滑点成本
        slippage = abs(price * quantity * self.transaction_costs.slippage_rate)
        
        # 计算佣金
        commission = max(
            abs(price * quantity) * self.transaction_costs.commission_rate,
            self.transaction_costs.min_commission if quantity != 0 else 0
        )
        
        # 计算印花税（只在卖出时收取）
        stamp_duty = abs(price * quantity) * self.transaction_costs.stamp_duty if not is_buy else 0
        
        return slippage + commission + stamp_duty
        
    def update_position(self, symbol: str, quantity: float, price: float, timestamp: datetime):
        """更新或创建新的持仓（考虑交易成本）"""
        is_buy = quantity > 0
        # 计算实际交易价格（考虑滑点）
        actual_price = price * (1 + self.transaction_costs.slippage_rate if is_buy else 1 - self.transaction_costs.slippage_rate)
        
        # 计算交易成本
        costs = self.calculate_transaction_costs(price, quantity, is_buy)
        self.total_costs += costs
        
        # 更新资金
        self.current_capital -= (actual_price * quantity + costs)
        
        if symbol in self.positions:
            current_position = self.positions[symbol]
            new_position = current_position.position + quantity
            if new_position == 0:
                del self.positions[symbol]
            else:
                # 更新持仓
                avg_price = (current_position.entry_price * current_position.position + actual_price * quantity) / new_position
                self.positions[symbol] = TradePosition(
                    symbol=symbol,
                    position=new_position,
                    entry_price=avg_price,
                    entry_time=timestamp,
                    current_price=actual_price,
                    pnl=0
                )
        else:
            if quantity != 0:
                self.positions[symbol] = TradePosition(
                    symbol=symbol,
                    position=quantity,
                    entry_price=actual_price,
                    entry_time=timestamp,
                    current_price=actual_price,
                    pnl=0
                )
        
        # 记录交易
        self.trade_history.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'actual_price': actual_price,
            'costs': costs,
            'capital': self.current_capital
        })

    def calculate_returns(self) -> float:
        """计算当前回报率（考虑交易成本）"""
        return (self.current_capital - self.initial_capital) / self.initial_capital

    def calculate_portfolio_stats(self) -> dict:
        """计算投资组合统计数据"""
        stats = {
            'total_trades': len(self.trade_history),
            'profitable_trades': sum(1 for trade in self.trade_history if trade.get('pnl', 0) > 0),
            'total_pnl': sum(trade.get('pnl', 0) for trade in self.trade_history),
            'largest_profit': max((trade.get('pnl', 0) for trade in self.trade_history), default=0),
            'largest_loss': min((trade.get('pnl', 0) for trade in self.trade_history), default=0),
            'current_positions': len(self.positions)
        }
        return stats

class RiskManager:
    """风险管理类"""
    def __init__(self, max_position_size: float = 0.1, max_drawdown: float = 0.2):
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.max_positions = 5  # 最大持仓数量
        self.position_sizing_method = 'equal'  # 头寸管理方法
        
    def calculate_position_size(self, capital: float, price: float, volatility: float = None) -> float:
        """计算建议持仓规模（考虑波动率）"""
        if self.position_sizing_method == 'volatility' and volatility is not None:
            # 基于波动率的头寸管理
            risk_factor = 1 / (volatility + 1e-6)  # 避免除零
            position_size = min(
                capital * self.max_position_size * risk_factor / price,
                capital / price
            )
        else:
            # 等额头寸管理
            position_size = min(
                capital * self.max_position_size / price,
                capital / price
            )
        return position_size
    
    def check_risk_limits(self, portfolio: Portfolio) -> bool:
        """检查是否超过风险限制"""
        # 检查回撤
        drawdown = 1 - portfolio.current_capital / portfolio.initial_capital
        if drawdown > self.max_drawdown:
            logger.warning(f"触发最大回撤限制: {drawdown:.2%}")
            return False
            
        # 检查持仓数量
        if len(portfolio.positions) >= self.max_positions:
            logger.warning(f"达到最大持仓数量限制: {self.max_positions}")
            return False
            
        return True

class PerformanceAnalyzer:
    """性能分析类"""
    def __init__(self):
        self.daily_returns = []
        self.cumulative_returns = []
        
    def calculate_metrics(self, portfolio: Portfolio):
        """计算性能指标"""
        returns = np.array(portfolio.daily_returns)
        if len(returns) == 0:
            return {}
            
        # 计算年化波动率
        volatility = np.std(returns) * np.sqrt(252)
        
        # 计算最大连续亏损天数
        negative_returns = returns < 0
        max_consecutive_losses = max(
            sum(1 for _ in group) for value, group in itertools.groupby(negative_returns) if value
        ) if len(returns) > 0 else 0
        
        # 计算月度收益率
        monthly_returns = pd.Series(returns).resample('M').agg(
            lambda x: (1 + x).prod() - 1
        )
        
        metrics = {
            'Total Return': portfolio.calculate_returns(),
            'Annual Return': self._calculate_annual_return(returns),
            'Sharpe Ratio': self._calculate_sharpe_ratio(returns),
            'Sortino Ratio': self._calculate_sortino_ratio(returns),
            'Max Drawdown': self._calculate_max_drawdown(returns),
            'Win Rate': self._calculate_win_rate(returns),
            'Volatility': volatility,
            'Max Consecutive Losses': max_consecutive_losses,
            'Monthly Win Rate': (monthly_returns > 0).mean(),
            'Best Month': monthly_returns.max(),
            'Worst Month': monthly_returns.min()
        }
        return metrics
    
    def _calculate_annual_return(self, returns: np.ndarray) -> float:
        """计算年化收益率"""
        total_return = (1 + returns).prod()
        years = len(returns) / 252
        return total_return ** (1/years) - 1 if years > 0 else 0
    
    def _calculate_sortino_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """计算索提诺比率"""
        if len(returns) < 2:
            return 0
        excess_returns = returns - risk_free_rate/252
        downside_returns = np.where(returns < 0, returns, 0)
        downside_std = np.std(downside_returns, ddof=1)
        return np.sqrt(252) * np.mean(excess_returns) / (downside_std + 1e-6)
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if len(returns) < 2:
            return 0
        excess_returns = returns - risk_free_rate/252  # 假设使用日收益率
        return np.sqrt(252) * np.mean(excess_returns) / np.std(returns, ddof=1)
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """计算最大回撤"""
        cum_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cum_returns)
        drawdowns = (running_max - cum_returns) / running_max
        return np.max(drawdowns)
    
    def _calculate_win_rate(self, returns: np.ndarray) -> float:
        """计算胜率"""
        if len(returns) == 0:
            return 0
        wins = np.sum(returns > 0)
        return wins / len(returns)

class BacktestReport:
    """回测报告生成器"""
    def __init__(self, backtester):
        self.backtester = backtester
        self.template_dir = Path("reports/templates")
        self.output_dir = Path("reports/output/backtest")
        
        # 确保目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2模板环境
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir))
        )
        
    def generate_html_report(self, filename: str = "backtest_report.html"):
        """生成HTML格式的回测报告"""
        template = self.env.get_template("backtest_report_template.html")
        
        # 准备报告数据
        report_data = self._prepare_report_data()
        
        # 渲染HTML
        html_content = template.render(**report_data)
        
        # 保存报告
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"HTML报告已生成: {output_path}")
        return output_path
        
    def generate_pdf_report(self, filename: str = "backtest_report.pdf"):
        """生成PDF格式的回测报告"""
        # 先生成HTML
        html_path = self.generate_html_report("temp_report.html")
        
        # 转换为PDF
        pdf_path = self.output_dir / filename
        html = weasyprint.HTML(filename=str(html_path))
        html.write_pdf(str(pdf_path))
        
        # 删除临时HTML文件
        os.remove(html_path)
        
        logger.info(f"PDF报告已生成: {pdf_path}")
        return pdf_path
        
    def _prepare_report_data(self) -> dict:
        """准备报告数据"""
        return {
            'strategy_name': self.backtester.__class__.__name__,
            'test_periods': self.backtester.results,
            'portfolio_stats': self._get_portfolio_stats(),
            'risk_metrics': self._get_risk_metrics(),
            'trade_analysis': self._get_trade_analysis(),
            'cost_analysis': self._get_cost_analysis(),
            'charts': self._generate_charts(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def _get_portfolio_stats(self) -> dict:
        """获取投资组合统计数据"""
        return {
            'initial_capital': self.backtester.portfolio.initial_capital,
            'final_capital': self.backtester.portfolio.current_capital,
            'total_return': self.backtester.portfolio.calculate_returns(),
            'positions': len(self.backtester.portfolio.positions)
        }
        
    def _get_risk_metrics(self) -> dict:
        """获取风险指标"""
        return {
            'max_drawdown': self.backtester.results.get('1Y', {}).max_drawdown,
            'sharpe_ratio': self.backtester.results.get('1Y', {}).sharpe_ratio,
            'win_rate': self.backtester.results.get('1Y', {}).win_rate
        }
        
    def _get_trade_analysis(self) -> dict:
        """获取交易分析"""
        return {
            'total_trades': len(self.backtester.portfolio.trade_history),
            'profit_factor': self.backtester.results.get('1Y', {}).profit_factor,
            'avg_profit': self.backtester.results.get('1Y', {}).avg_profit_per_trade
        }
        
    def _get_cost_analysis(self) -> dict:
        """获取成本分析"""
        return {
            'total_costs': self.backtester.portfolio.total_costs,
            'cost_ratio': self.backtester.portfolio.total_costs / self.backtester.portfolio.initial_capital
        }
        
    def _generate_charts(self) -> List[str]:
        """生成图表并返回文件路径列表"""
        charts = []
        
        # 生成收益曲线图
        plt.figure(figsize=(12, 6))
        self.backtester.plot_results()
        chart_path = self.output_dir / "returns_chart.png"
        plt.savefig(chart_path)
        plt.close()
        charts.append(str(chart_path))
        
        # 生成其他图表...
        
        return charts

class Backtester:
    """
    回测器：执行策略回测
    
    功能：
    1. 模拟订单执行
    2. 计算交易成本
    3. 动态滑点模型
    4. 流动性检查
    """
    
    def __init__(
        self,
        initial_capital: float,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        slippage_config: Optional[SlippageConfig] = None,
        volume_window: int = 20,
        max_workers: int = None,
        task_timeout: int = 30
    ):
        """
        初始化回测器
        
        Args:
            initial_capital: 初始资金
            commission_rate: 佣金率
            min_commission: 最小佣金
            slippage_config: 滑点配置
            volume_window: 成交量计算窗口
            max_workers: 最大工作线程数
            task_timeout: 任务超时时间（秒）
        """
        self.initial_capital = initial_capital
        self.transaction_costs = TransactionCosts(
            commission_rate=commission_rate,
            min_commission=min_commission
        )
        self.slippage_config = slippage_config or SlippageConfig()
        self.volume_window = volume_window
        
        # 缓存数据
        self._volume_cache = {}
        self._volatility_cache = {}
        
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager()
        self.performance_analyzer = PerformanceAnalyzer()
        self.data: Dict[str, pd.DataFrame] = {}
        self.results: Dict[str, BacktestResult] = {}
        self.report_generator = BacktestReport(self)
        
        # 初始化线程池管理器
        self.thread_pool = ThreadPoolManager(
            max_workers=max_workers,
            task_timeout=task_timeout
        )
        
    def load_data(self, symbol: str, data: pd.DataFrame):
        """加载历史数据"""
        self.data[symbol] = data
        
    def run_backtest(self, strategy, start_date: str, end_date: str):
        """运行回测（添加进度显示和异常恢复）"""
        logger.info(f"开始回测 - 从 {start_date} 到 {end_date}")
        
        try:
            # 确保所有数据都在同一个时间范围内
            aligned_data = self._align_data(start_date, end_date)
            if aligned_data.empty:
                logger.error("没有可用的回测数据")
                return
                
            # 并行计算技术指标
            logger.info("计算技术指标...")
            data_with_indicators = self._calculate_technical_indicators_parallel(self.data)
            
            # 计算波动率（用于风险管理）
            volatility = aligned_data.pct_change().std()
            
            # 主回测循环
            from tqdm import tqdm
            for timestamp, current_data in tqdm(aligned_data.iterrows(), total=len(aligned_data), desc="回测进度"):
                try:
                    # 并行更新当前价格和持仓状态
                    if self.portfolio.positions:
                        self._update_portfolio_state_parallel(
                            self.portfolio.positions,
                            {symbol: data.loc[timestamp] for symbol, data in self.data.items()}
                        )
                    
                    # 并行生成交易信号
                    current_data_dict = {
                        symbol: data_with_indicators[symbol].loc[:timestamp]
                        for symbol in self.data.keys()
                    }
                    signals = self._generate_signals_parallel(strategy, current_data_dict)
                    
                    # 执行交易信号
                    for symbol, signal in signals.items():
                        if symbol not in current_data or signal.iloc[-1] == 0:
                            continue
                            
                        price = current_data[symbol]
                        signal_value = signal.iloc[-1]
                        
                        # 计算交易数量（考虑波动率）
                        quantity = self.risk_manager.calculate_position_size(
                            self.portfolio.current_capital,
                            price,
                            volatility[symbol]
                        )
                        quantity *= signal_value  # signal 应该是 1 (买入) 或 -1 (卖出)
                        
                        # 执行交易
                        self.portfolio.update_position(symbol, quantity, price, timestamp)
                    
                    # 风险检查
                    if not self.risk_manager.check_risk_limits(self.portfolio):
                        logger.warning(f"触发风险限制，在 {timestamp} 停止回测")
                        break
                        
                except Exception as e:
                    logger.error(f"处理时间点 {timestamp} 时出错: {e}")
                    continue
            
            # 并行计算性能指标
            logger.info("计算性能指标...")
            performance_metrics = self._calculate_performance_metrics_parallel(self.data)
            self._print_results(performance_metrics)
            
        except Exception as e:
            logger.error(f"回测过程中出错: {e}")
            self._save_checkpoint()
            raise
        finally:
            # 确保线程池正确关闭
            self.thread_pool.executor.shutdown(wait=True)
            
    def _align_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """对齐所有数据到相同的时间索引（优化性能）"""
        if not self.data:
            return pd.DataFrame()
            
        # 使用第一个数据集作为基准
        first_symbol = list(self.data.keys())[0]
        base_data = self.data[first_symbol].loc[start_date:end_date]
        aligned_data = pd.DataFrame(index=base_data.index)
        aligned_data[first_symbol] = base_data['close']
        
        # 其他数据集与基准对齐
        for symbol, data in list(self.data.items())[1:]:
            symbol_data = data.loc[start_date:end_date]
            aligned_data[symbol] = symbol_data['close'].reindex(base_data.index)
        
        # 删除有缺失值的行
        aligned_data = aligned_data.dropna()
        
        if aligned_data.empty:
            logger.error("对齐后的数据为空")
        
        return aligned_data
    
    def _execute_signals(self, signals: Dict[str, float], timestamp: datetime, 
                        current_data: pd.Series, volatility: pd.Series):
        """执行交易信号（考虑波动率）"""
        for symbol, signal in signals.items():
            if symbol not in current_data:
                continue
                
            price = current_data[symbol]
            if signal == 0:
                continue
                
            # 计算交易数量（考虑波动率）
            quantity = self.risk_manager.calculate_position_size(
                self.portfolio.current_capital,
                price,
                volatility[symbol]
            )
            quantity *= signal  # signal 应该是 1 (买入) 或 -1 (卖出)
            
            # 执行交易
            self.portfolio.update_position(symbol, quantity, price, timestamp)
            
    def _update_portfolio_state(self, timestamp: datetime):
        """更新投资组合状态"""
        total_value = self.portfolio.current_capital
        for position in self.portfolio.positions.values():
            position.pnl = (position.current_price - position.entry_price) * position.position
            total_value += position.pnl
            
        daily_return = (total_value - self.portfolio.current_capital) / self.portfolio.current_capital
        self.portfolio.daily_returns.append(daily_return)
        self.portfolio.current_capital = total_value
        
    def _print_results(self, metrics: dict):
        """打印回测结果"""
        logger.info("\n=== 回测结果 ===")
        for metric, value in metrics.items():
            logger.info(f"{metric}: {value:.4f}")
            
    def plot_results(self):
        """绘制回测结果"""
        returns = np.array(self.portfolio.daily_returns)
        cumulative_returns = (1 + returns).cumprod()
        
        plt.figure(figsize=(12, 6))
        plt.plot(cumulative_returns)
        plt.title('Cumulative Returns')
        plt.xlabel('Trading Days')
        plt.ylabel('Returns')
        plt.grid(True)
        plt.show()

    def run_multi_period_backtest(self, strategy, symbols: List[str], end_date: str = None):
        """运行多个时间周期的回测"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # 定义回测周期
        periods = {
            '5Y': relativedelta(years=5),
            '2Y': relativedelta(years=2),
            '1Y': relativedelta(years=1),
            '6M': relativedelta(months=6)
        }
        
        results = {}
        for period_name, period_delta in periods.items():
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - period_delta).strftime('%Y-%m-%d')
            logger.info(f"\n开始 {period_name} 周期回测 ({start_date} 到 {end_date})")
            
            # 重置投资组合状态
            self.portfolio = Portfolio(self.portfolio.initial_capital)
            
            # 运行回测
            self.run_backtest(strategy, start_date, end_date)
            
            # 保存结果
            self.results[period_name] = self._calculate_period_results(period_name)
            
        self._print_multi_period_results()
    
    def _calculate_period_results(self, period: str) -> BacktestResult:
        """计算特定时间周期的回测结果"""
        metrics = self.performance_analyzer.calculate_metrics(self.portfolio)
        trades = self.portfolio.trade_history
        
        profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
        total_profit = sum(t.get('pnl', 0) for t in profitable_trades)
        total_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
        
        return BacktestResult(
            period=period,
            total_return=metrics['Total Return'],
            annual_return=self._calculate_annual_return(metrics['Total Return']),
            sharpe_ratio=metrics['Sharpe Ratio'],
            max_drawdown=metrics['Max Drawdown'],
            win_rate=metrics['Win Rate'],
            trade_count=len(trades),
            profit_factor=total_profit / total_loss if total_loss != 0 else float('inf'),
            avg_profit_per_trade=sum(t.get('pnl', 0) for t in trades) / len(trades) if trades else 0
        )
    
    def _calculate_annual_return(self, total_return: float) -> float:
        """计算年化收益率"""
        years = len(self.portfolio.daily_returns) / 252
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    def _print_multi_period_results(self):
        """打印多周期回测结果（包含交易成本分析）"""
        logger.info("\n=== 多周期回测结果 ===")
        for period, result in self.results.items():
            logger.info(f"\n{period} 周期结果:")
            logger.info(f"总收益率: {result.total_return:.2%}")
            logger.info(f"年化收益率: {result.annual_return:.2%}")
            logger.info(f"夏普比率: {result.sharpe_ratio:.2f}")
            logger.info(f"最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"胜率: {result.win_rate:.2%}")
            logger.info(f"交易次数: {result.trade_count}")
            logger.info(f"盈亏比: {result.profit_factor:.2f}")
            logger.info(f"平均每笔交易盈亏: {result.avg_profit_per_trade:.2f}")
            logger.info(f"总交易成本: {self.portfolio.total_costs:.2f}")
            logger.info(f"交易成本占比: {(self.portfolio.total_costs/self.portfolio.initial_capital):.2%}")
    
    def plot_multi_period_results(self):
        """绘制多周期回测结果对比图"""
        periods = list(self.results.keys())
        metrics = ['total_return', 'sharpe_ratio', 'win_rate', 'max_drawdown']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('多周期回测结果对比')
        
        for i, metric in enumerate(metrics):
            ax = axes[i//2, i%2]
            values = [getattr(self.results[p], metric) for p in periods]
            ax.bar(periods, values)
            ax.set_title(metric.replace('_', ' ').title())
            ax.grid(True)
            
            # 添加数值标签
            for j, v in enumerate(values):
                ax.text(j, v, f'{v:.2%}' if metric in ['total_return', 'win_rate', 'max_drawdown'] else f'{v:.2f}',
                       ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()

    def plot_key_metrics(self, period: str = None):
        """绘制关键指标的直观展示图"""
        if period:
            results = {period: self.results[period]}
        else:
            results = self.results
            
        for period, result in results.items():
            # 创建一个单独的图表
            plt.figure(figsize=(15, 8))
            
            # 定义关键指标和其值
            metrics = {
                '胜率': f"{result.win_rate:.1%}",
                '年化收益': f"{result.annual_return:.1%}",
                '最大回撤': f"{result.max_drawdown:.1%}",
                '夏普比率': f"{result.sharpe_ratio:.2f}",
                '交易次数': f"{result.trade_count}",
                '盈亏比': f"{result.profit_factor:.2f}",
                '平均盈利': f"{result.avg_profit_per_trade:.0f}"
            }
            
            # 设置颜色方案
            colors = ['#2ecc71', '#3498db', '#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c', '#e67e22']
            
            # 创建水平条形图
            y_pos = np.arange(len(metrics))
            plt.barh(y_pos, [1]*len(metrics), color=colors)
            
            # 添加指标值文本
            for i, (metric, value) in enumerate(metrics.items()):
                plt.text(0.5, i, f"{metric}: {value}", ha='center', va='center', fontsize=12, fontweight='bold', color='white')
            
            # 设置图表样式
            plt.title(f"{period} 回测关键指标", pad=20, fontsize=14, fontweight='bold')
            plt.yticks([])  # 隐藏y轴刻度
            plt.xticks([])  # 隐藏x轴刻度
            plt.box(False)  # 移除边框
            
            # 添加网格线
            plt.grid(True, axis='x', alpha=0.1)
            
            plt.tight_layout()
            plt.show()
            
    def print_summary(self, period: str = None):
        """打印简明的回测总结（包含交易成本分析）"""
        if period:
            results = {period: self.results[period]}
        else:
            results = self.results
            
        for period, result in results.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"{period} 回测结果总结")
            logger.info(f"{'='*50}")
            logger.info(f"胜率:         {result.win_rate:>10.1%}")
            logger.info(f"年化收益:     {result.annual_return:>10.1%}")
            logger.info(f"最大回撤:     {result.max_drawdown:>10.1%}")
            logger.info(f"夏普比率:     {result.sharpe_ratio:>10.2f}")
            logger.info(f"交易次数:     {result.trade_count:>10}")
            logger.info(f"盈亏比:       {result.profit_factor:>10.2f}")
            logger.info(f"平均盈利:     {result.avg_profit_per_trade:>10.0f}")
            logger.info(f"总交易成本:   {self.portfolio.total_costs:>10.2f}")
            logger.info(f"成本率:       {(self.portfolio.total_costs/self.portfolio.initial_capital):>10.1%}")
            logger.info(f"{'='*50}\n")

    def generate_report(self, format: str = 'html', filename: str = None):
        """生成回测报告"""
        if format.lower() == 'html':
            if filename is None:
                filename = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            return self.report_generator.generate_html_report(filename)
        elif format.lower() == 'pdf':
            if filename is None:
                filename = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            return self.report_generator.generate_pdf_report(filename)
        else:
            raise ValueError("不支持的报告格式。请使用 'html' 或 'pdf'。")

    def _save_checkpoint(self):
        """保存回测检查点"""
        checkpoint_dir = Path("checkpoints")
        checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio_state': {
                'current_capital': self.portfolio.current_capital,
                'positions': self.portfolio.positions,
                'trade_history': self.portfolio.trade_history
            }
        }
        
        checkpoint_path = checkpoint_dir / f"backtest_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=4, default=str)
        logger.info(f"检查点已保存到: {checkpoint_path}")

    def _calculate_volume_profile(
        self, 
        symbol: str,
        market_data: pd.Series,
        lookback_period: int = 20
    ) -> Tuple[float, float, float]:
        """
        计算成交量特征
        
        Args:
            symbol: 股票代码
            market_data: 市场数据
            lookback_period: 回溯期
            
        Returns:
            Tuple[float, float, float]: (平均成交量, 成交量波动率, 相对流动性)
        """
        if symbol not in self._volume_cache:
            # 计算成交量移动平均
            volume_ma = market_data['volume'].rolling(window=lookback_period).mean()
            
            # 计算成交量波动率
            volume_std = market_data['volume'].rolling(window=lookback_period).std()
            
            # 计算相对流动性（当前成交量/平均成交量）
            relative_liquidity = market_data['volume'] / volume_ma
            
            self._volume_cache[symbol] = {
                'avg_volume': volume_ma.mean(),
                'vol_std': volume_std.mean() / volume_ma.mean() if volume_ma.mean() > 0 else 1.0,
                'rel_liquidity': relative_liquidity.mean()
            }
            
        return (
            self._volume_cache[symbol]['avg_volume'],
            self._volume_cache[symbol]['vol_std'],
            self._volume_cache[symbol]['rel_liquidity']
        )
        
    def _check_liquidity(
        self,
        quantity: int,
        market_data: pd.Series,
        avg_volume: float,
        rel_liquidity: float
    ) -> Tuple[bool, str, float]:
        """
        检查流动性条件并计算流动性调整因子
        
        Args:
            quantity: 交易数量
            market_data: 市场数据
            avg_volume: 平均成交量
            rel_liquidity: 相对流动性
            
        Returns:
            Tuple[bool, str, float]: (是否可交易, 原因, 流动性调整因子)
        """
        current_volume = market_data['volume']
        
        # 计算流动性调整因子
        liquidity_factor = 1.0
        
        # 检查最小成交量
        if current_volume < self.slippage_config.min_volume:
            return False, "成交量过低", liquidity_factor
        
        # 检查相对成交量
        volume_ratio = quantity / avg_volume
        if volume_ratio > self.slippage_config.max_volume_ratio:
            return False, "交易量超过限制", liquidity_factor
        
        # 根据相对流动性调整因子
        if rel_liquidity < self.slippage_config.liquidity_threshold:
            liquidity_factor = (self.slippage_config.liquidity_threshold / rel_liquidity) ** 2
        
        # 检查价格波动
        if 'high' in market_data and 'low' in market_data:
            price_range = (market_data['high'] - market_data['low']) / market_data['low']
            if price_range > self.slippage_config.max_slippage:
                return False, "价格波动过大", liquidity_factor
        
        return True, "", liquidity_factor
        
    def _calculate_dynamic_slippage(
        self,
        quantity: int,
        price: float,
        market_data: pd.Series,
        avg_volume: float,
        volume_std: float,
        liquidity_factor: float
    ) -> float:
        """
        计算动态滑点
        
        Args:
            quantity: 交易数量
            price: 交易价格
            market_data: 市场数据
            avg_volume: 平均成交量
            volume_std: 成交量波动率
            liquidity_factor: 流动性调整因子
            
        Returns:
            float: 滑点率
        """
        # 基础滑点
        slippage = self.slippage_config.base_rate
        
        # 计算市场冲击成本
        market_impact = self._calculate_market_impact(
            quantity, price, avg_volume, volume_std
        )
        
        # 价格波动影响
        price_impact = 0
        if 'high' in market_data and 'low' in market_data:
            price_range = (market_data['high'] - market_data['low']) / market_data['low']
            price_impact = price_range * market_impact
        
        # 应用流动性调整
        total_slippage = (slippage + market_impact + price_impact) * liquidity_factor
        
        # 确保滑点符合最小价格变动单位
        ticks = round(total_slippage / self.slippage_config.min_tick_size)
        total_slippage = ticks * self.slippage_config.min_tick_size
        
        # 限制最大滑点
        return min(total_slippage, self.slippage_config.max_slippage)

    def execute_trades(
        self,
        signals: List[Dict],
        market_data: Dict[str, pd.Series],
        portfolio: Portfolio
    ) -> List[Dict]:
        """
        执行交易信号
        
        Args:
            signals: 交易信号列表
            market_data: 市场数据
            portfolio: 当前投资组合
            
        Returns:
            List[Dict]: 实际执行的交易列表
        """
        executed_trades = []
        
        for signal in signals:
            symbol = signal['symbol']
            quantity = signal['quantity']
            
            if symbol not in market_data:
                continue
                
            # 获取成交量特征
            avg_volume, volume_std, rel_liquidity = self._calculate_volume_profile(
                symbol, 
                market_data[symbol]
            )
            
            # 检查流动性
            can_trade, reason, liquidity_factor = self._check_liquidity(
                quantity,
                market_data[symbol],
                avg_volume,
                rel_liquidity
            )
            
            if not can_trade:
                continue
                
            # 计算动态滑点
            slippage = self._calculate_dynamic_slippage(
                quantity,
                signal['price'],
                market_data[symbol],
                avg_volume,
                volume_std,
                liquidity_factor
            )
            
            # 调整价格
            if signal['type'] == 'buy':
                executed_price = signal['price'] * (1 + slippage)
            else:
                executed_price = signal['price'] * (1 - slippage)
                
            # 计算交易成本
            commission = max(
                executed_price * quantity * self.transaction_costs.commission_rate,
                self.transaction_costs.min_commission
            )
            
            tax = (
                executed_price * quantity * self.transaction_costs.tax_rate
                if signal['type'] == 'sell'
                else 0
            )
            
            total_cost = commission + tax
            
            # 检查资金是否足够
            if signal['type'] == 'buy':
                total_cost += executed_price * quantity
                if total_cost > portfolio.cash:
                    continue
                    
            # 记录交易
            trade = {
                'date': signal['date'],
                'symbol': symbol,
                'type': signal['type'],
                'quantity': quantity,
                'price': executed_price,
                'slippage': slippage,
                'commission': commission,
                'tax': tax,
                'cost': total_cost
            }
            
            executed_trades.append(trade)
            
        return executed_trades
        
    def get_transaction_summary(self) -> Dict:
        """获取交易统计信息"""
        return {
            'transaction_costs': self.transaction_costs,
            'slippage_config': self.slippage_config,
            'volume_window': self.volume_window
        }

    def _calculate_market_impact(
        self,
        quantity: int,
        price: float,
        avg_volume: float,
        volume_std: float
    ) -> float:
        """
        计算市场冲击成本
        
        Args:
            quantity: 交易数量
            price: 交易价格
            avg_volume: 平均成交量
            volume_std: 成交量波动率
            
        Returns:
            float: 市场冲击成本
        """
        # 计算订单相对规模
        relative_size = quantity / avg_volume if avg_volume > 0 else 1.0
        
        # 使用指数衰减模型计算市场冲击
        impact = (
            self.slippage_config.volume_impact * 
            (1 - np.exp(-relative_size / self.slippage_config.market_impact_decay))
        )
        
        # 考虑成交量波动性的影响
        impact *= (1 + volume_std * self.slippage_config.volatility_multiplier)
        
        return impact

    def _process_data_parallel(self, func: Callable, data: Dict[str, pd.DataFrame], 
                              chunk_size: int = None) -> Dict[str, Any]:
        """
        并行处理数据
        
        Args:
            func: 处理函数
            data: 要处理的数据字典
            chunk_size: 数据分块大小
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        return self.thread_pool.process_parallel(func, data, chunk_size)
        
    def _calculate_technical_indicators_parallel(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        并行计算技术指标
        
        Args:
            data: 股票数据字典
            
        Returns:
            Dict[str, pd.DataFrame]: 计算结果
        """
        def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
            try:
                # 在这里添加技术指标计算逻辑
                result = df.copy()
                # 示例：计算移动平均
                result['MA5'] = df['close'].rolling(window=5).mean()
                result['MA10'] = df['close'].rolling(window=10).mean()
                result['MA20'] = df['close'].rolling(window=20).mean()
                # 添加更多指标...
                return result
            except Exception as e:
                logger.error(f"计算技术指标时出错: {str(e)}")
                return df
                
        return self._process_data_parallel(calculate_indicators, data)
        
    def _generate_signals_parallel(self, strategy, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """
        并行生成交易信号
        
        Args:
            strategy: 策略对象
            data: 股票数据字典
            
        Returns:
            Dict[str, pd.Series]: 交易信号
        """
        def generate_signal(df: pd.DataFrame) -> pd.Series:
            try:
                return strategy.generate_signals(df)
            except Exception as e:
                logger.error(f"生成交易信号时出错: {str(e)}")
                return pd.Series(index=df.index)
                
        return self._process_data_parallel(generate_signal, data)
        
    def _calculate_performance_metrics_parallel(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        并行计算性能指标
        
        Args:
            data: 股票数据字典
            
        Returns:
            Dict[str, Dict]: 性能指标
        """
        def calculate_metrics(df: pd.DataFrame) -> Dict:
            try:
                returns = df['close'].pct_change()
                return {
                    'total_return': (1 + returns).prod() - 1,
                    'annual_return': self._calculate_annual_return(returns.values),
                    'sharpe_ratio': self._calculate_sharpe_ratio(returns.values),
                    'max_drawdown': self._calculate_max_drawdown(returns.values),
                    'volatility': returns.std() * np.sqrt(252)
                }
            except Exception as e:
                logger.error(f"计算性能指标时出错: {str(e)}")
                return {}
                
        return self._process_data_parallel(calculate_metrics, data)
        
    def _update_portfolio_state_parallel(self, positions: Dict[str, TradePosition], 
                                       current_data: Dict[str, pd.Series]) -> None:
        """
        并行更新投资组合状态
        
        Args:
            positions: 当前持仓
            current_data: 当前市场数据
        """
        def update_position(position: TradePosition) -> float:
            try:
                if position.symbol in current_data:
                    position.current_price = current_data[position.symbol]['close']
                    return (position.current_price - position.entry_price) * position.position
                return 0
            except Exception as e:
                logger.error(f"更新持仓状态时出错: {str(e)}")
                return 0
                
        with self.thread_pool as pool:
            pnl_results = pool.process_batch(update_position, list(positions.values()))
            
        total_pnl = sum(pnl_results)
        self.portfolio.current_capital += total_pnl
