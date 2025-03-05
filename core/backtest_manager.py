import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from core.data_manager import DataManager
from core.market_types import MarketData
from strategies.backtester import Backtester
from core.portfolio import Portfolio
from core.risk_manager import RiskManager
from core.performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class BacktestManager:
    """
    Backtest Manager: Controls backtest process and result analysis.
    
    Manages the entire backtesting process including data loading,
    strategy execution, and report generation.
    """
    
    def __init__(self):
        self.strategy = None
        self.params = {
            'initial_capital': 100000.0,
            'start_date': None,
            'end_date': None,
            'symbols': [],
            'risk_params': {
                'max_position_size': 0.1,
                'max_drawdown': 0.2,
                'max_positions': 5
            },
            'cost_params': {
                'commission_rate': 0.0003,
                'slippage_rate': 0.0002,
                'min_commission': 5.0
            }
        }
        self.data_manager = DataManager()
        self.backtester = None
        self.results = None
        
    def set_strategy(self, strategy_name: str) -> bool:
        """设置回测策略"""
        try:
            self.strategy = strategy_name
            return True
        except Exception as e:
            logger.error(f"设置策略失败: {e}")
            return False
            
    def set_parameters(self, params: dict) -> bool:
        """设置回测参数"""
        try:
            self.params.update(params)
            return True
        except Exception as e:
            logger.error(f"设置参数失败: {e}")
            return False
            
    def validate_parameters(self) -> bool:
        """验证回测参数"""
        try:
            if not self.strategy:
                logger.error("未设置策略")
                return False
                
            if not self.params['symbols']:
                logger.error("未设置交易品种")
                return False
                
            if not self.params['start_date']:
                logger.error("未设置开始日期")
                return False
                
            return True
        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            return False
            
    def _align_market_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        对齐多个股票的交易日期
        
        Args:
            data: 原始市场数据字典
            
        Returns:
            Dict[str, pd.DataFrame]: 日期对齐后的市场数据
        """
        logger.info("对齐市场数据时间序列...")
        
        # 获取所有股票的交易日期交集
        common_dates = set.intersection(*[set(df.index) for df in data.values()])
        if not common_dates:
            logger.error("没有共同的交易日期")
            return {}
            
        # 对齐数据
        aligned_data = {}
        common_dates = sorted(common_dates)
        for symbol, df in data.items():
            aligned_data[symbol] = df.loc[common_dates].copy()
            
        logger.info(f"数据对齐完成，共{len(common_dates)}个交易日")
        return aligned_data
        
    def run_backtest(self) -> Optional[Dict[str, Any]]:
        """
        执行回测流程
        
        流程包括：
        1. 加载历史数据
        2. 逐日运行策略
        3. 计算交易信号
        4. 模拟执行交易
        5. 计算绩效指标
        6. 生成回测报告
        
        Returns:
            Dict[str, Any]: 包含回测结果的字典，如果失败则返回 None
        """
        try:
            logger.info("开始执行回测...")
            
            # 1. 验证参数
            if not self.validate_parameters():
                return None
                
            # 2. 初始化组件
            logger.info("初始化回测组件...")
            self.portfolio = Portfolio(
                initial_capital=self.params['initial_capital'],
                symbols=self.params['symbols']
            )
            
            self.risk_manager = RiskManager(
                max_position_size=self.params['risk_params']['max_position_size'],
                max_drawdown=self.params['risk_params']['max_drawdown'],
                max_positions=self.params['risk_params']['max_positions']
            )
            
            self.performance_analyzer = PerformanceAnalyzer()
            
            # 3. 加载数据
            logger.info("加载历史数据...")
            data = self._load_market_data()
            if not data:
                return None
                
            # 3.1 对齐数据
            aligned_data = self._align_market_data(data)
            if not aligned_data:
                return None
                
            # 4. 初始化回测器
            logger.info("初始化回测器...")
            self.backtester = Backtester(
                initial_capital=self.params['initial_capital'],
                commission_rate=self.params['cost_params']['commission_rate'],
                slippage_rate=self.params['cost_params']['slippage_rate'],
                min_commission=self.params['cost_params']['min_commission']
            )
            
            # 5. 执行回测
            logger.info("执行回测策略...")
            dates = sorted(list(next(iter(aligned_data.values())).index))
            total_days = len(dates)
            
            for i, date in enumerate(dates, 1):
                # 获取当日数据
                current_data = {
                    symbol: df.loc[date] 
                    for symbol, df in aligned_data.items()
                }
                
                # 运行策略获取信号
                signals = self.strategy.generate_signals(current_data)
                
                # 风险控制
                filtered_signals = self.risk_manager.filter_signals(
                    signals, 
                    self.portfolio
                )
                
                # 执行交易
                trades = self.backtester.execute_trades(
                    filtered_signals,
                    current_data,
                    self.portfolio
                )
                
                # 更新组合状态
                self.portfolio.update(date, current_data, trades)
                
                # 记录每日表现
                self.performance_analyzer.update(
                    date,
                    self.portfolio.get_total_value(),
                    trades
                )
                
                # 打印进度
                if i % 100 == 0 or i == total_days:
                    logger.info(f"回测进度: {i}/{total_days} ({i/total_days*100:.2f}%)")
            
            # 6. 计算性能指标
            logger.info("计算性能指标...")
            performance_metrics = self.performance_analyzer.calculate_metrics()
            
            # 7. 整理回测结果
            self.results = {
                'portfolio': self.portfolio.get_summary(),
                'performance': performance_metrics,
                'trades': self.portfolio.get_trades(),
                'positions': self.portfolio.get_positions_history(),
                'equity_curve': self.portfolio.get_equity_curve(),
                'drawdowns': self.performance_analyzer.get_drawdowns(),
                'backtest_info': {
                    'start_date': dates[0],
                    'end_date': dates[-1],
                    'total_days': total_days,
                    'symbols': list(aligned_data.keys())
                }
            }
            
            # 8. 生成回测报告
            logger.info("生成回测报告...")
            self._generate_report()
            
            logger.info(f"回测完成。总收益率: {performance_metrics['total_return']:.2%}")
            return self.results
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
    def _load_market_data(self) -> Optional[Dict[str, MarketData]]:
        """加载市场数据"""
        try:
            data = {}
            for symbol in self.params['symbols']:
                df = self.data_manager.get_historical_data(
                    symbol=symbol,
                    start_date=self.params['start_date'],
                    end_date=self.params['end_date']
                )
                if df is not None:
                    data[symbol] = df
                else:
                    logger.error(f"加载{symbol}数据失败")
                    return None
            return data
        except Exception as e:
            logger.error(f"加载市场数据失败: {e}")
            return None
            
    def _generate_report(self) -> bool:
        """生成回测报告"""
        try:
            if not self.results:
                logger.error("没有回测结果可供生成报告")
                return False
                
            # 创建报告目录
            report_dir = Path("reports/output/backtest")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成报告文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = report_dir / f"backtest_report_{timestamp}.html"
            
            # 生成HTML报告
            self._generate_html_report(report_path)
            
            logger.info(f"回测报告已生成: {report_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return False
            
    def _generate_html_report(self, path: Path):
        """生成HTML格式报告"""
        try:
            # 使用jinja2模板生成报告
            from jinja2 import Environment, FileSystemLoader
            
            # 加载模板
            env = Environment(loader=FileSystemLoader('reports/templates/html'))
            template = env.get_template('backtest_report.html')
            
            # 准备报告数据
            report_data = {
                'strategy': self.strategy,
                'params': self.params,
                'results': self.results,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染报告
            html_content = template.render(**report_data)
            
            # 保存报告
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            raise
