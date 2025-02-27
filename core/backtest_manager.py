import os
import json
import logging
import webbrowser
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import pandas as pd

from strategies.backtester import Backtester
import importlib

logger = logging.getLogger(__name__)

class BacktestManager:
    """回测管理器：负责回测流程控制和交互"""
    
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
                'max_positions': 5,
                'position_sizing_method': 'equal'  # 'equal' or 'volatility'
            },
            'cost_params': {
                'commission_rate': 0.0003,
                'slippage_rate': 0.0002,
                'min_commission': 5.0,
                'stamp_duty': 0.001
            }
        }
        self.backtester: Optional[Backtester] = None
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
    def configure_backtest(self) -> bool:
        """配置回测参数"""
        try:
            print("\n=== 回测参数配置 ===")
            
            # 1. 尝试加载已保存的配置
            if self._ask_load_config():
                return True
                
            print("\n1. 基础参数设置")
            self.params['initial_capital'] = float(input("初始资金（默认100000）: ") or "100000")
            self.params['start_date'] = input("开始日期（YYYY-MM-DD）: ")
            self.params['end_date'] = input("结束日期（留空为当前日期）: ") or datetime.now().strftime('%Y-%m-%d')
            symbols = input("交易品种（用逗号分隔）: ")
            self.params['symbols'] = [s.strip() for s in symbols.split(',')]
            
            print("\n2. 风险参数设置")
            self.params['risk_params']['max_position_size'] = float(input("最大持仓比例（默认0.1）: ") or "0.1")
            self.params['risk_params']['max_drawdown'] = float(input("最大回撤限制（默认0.2）: ") or "0.2")
            self.params['risk_params']['max_positions'] = int(input("最大持仓数量（默认5）: ") or "5")
            
            sizing_method = input("头寸管理方法（1:等额, 2:波动率）[默认1]: ") or "1"
            self.params['risk_params']['position_sizing_method'] = 'equal' if sizing_method == "1" else 'volatility'
            
            print("\n3. 交易成本设置")
            self.params['cost_params']['commission_rate'] = float(input("佣金率（默认0.0003）: ") or "0.0003")
            self.params['cost_params']['slippage_rate'] = float(input("滑点率（默认0.0002）: ") or "0.0002")
            self.params['cost_params']['min_commission'] = float(input("最小佣金（默认5.0）: ") or "5.0")
            
            # 保存配置
            if input("\n是否保存当前配置？(y/n) ").lower() == 'y':
                self.save_parameters()
            
            return True
        except ValueError as e:
            logger.error(f"参数设置错误: {e}")
            return False
            
    def _ask_load_config(self) -> bool:
        """询问是否加载已保存的配置"""
        config_path = Path("config/backtest_config.json")
        if config_path.exists():
            if input("发现已保存的配置，是否加载？(y/n) ").lower() == 'y':
                return self.load_parameters()
        return False
            
    def select_strategy(self) -> bool:
        """选择交易策略"""
        print("\n=== 可用策略 ===")
        strategies = self._get_available_strategies()
        
        for key, name in strategies.items():
            print(f"{key}. {name}")
            
        choice = input("\n请选择策略编号: ")
        if choice in strategies:
            try:
                self.strategy = self._load_strategy(choice)
                return True
            except Exception as e:
                logger.error(f"策略加载失败: {e}")
                return False
        return False
    
    def _get_available_strategies(self) -> Dict[str, str]:
        """获取可用的策略列表"""
        # 扫描strategies目录下的所有策略文件
        strategies_dir = Path(__file__).parent
        strategy_files = list(strategies_dir.glob("*_strategy.py"))
        
        strategies = {}
        for i, file in enumerate(strategy_files, 1):
            strategy_name = file.stem.replace('_', ' ').title()
            strategies[str(i)] = strategy_name
            
        if not strategies:
            # 默认策略列表
            strategies = {
                "1": "双均线策略",
                "2": "趋势跟踪策略",
                "3": "网格交易策略",
                "4": "动量策略"
            }
            
        return strategies
    
    def _load_strategy(self, strategy_id: str):
        """加载选择的策略"""
        try:
            # 策略映射表
            strategy_map = {
                "1": "MAStrategy",  # 双均线策略
                "2": "TrendStrategy",  # 趋势跟踪策略
                "3": "GridStrategy",  # 网格交易策略
                "4": "MomentumStrategy"  # 动量策略
            }
            
            if strategy_id not in strategy_map:
                raise ValueError("无效的策略ID")
                
            strategy_name = strategy_map[strategy_id]
            # 动态导入策略模块
            module = importlib.import_module(f"strategies.{strategy_name.lower()}")
            strategy_class = getattr(module, strategy_name)
            return strategy_class()
        except Exception as e:
            logger.error(f"策略加载失败: {e}")
            raise
        
    def load_data(self) -> bool:
        """加载回测数据"""
        try:
            for symbol in self.params['symbols']:
                if symbol not in self.data_cache:
                    data = self._load_historical_data(
                        symbol,
                        self.params['start_date'],
                        self.params['end_date']
                    )
                    if data is not None:
                        self.data_cache[symbol] = data
                    else:
                        raise ValueError(f"无法加载{symbol}的历史数据")
            return True
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            return False

    def _load_historical_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """加载历史数据"""
        try:
            # 首先尝试从本地CSV文件加载
            data_path = Path(f"data/{symbol}.csv")
            if data_path.exists():
                df = pd.read_csv(data_path, parse_dates=['date'], index_col='date')
                return df.loc[start_date:end_date]
                
            # 如果本地文件不存在，尝试从数据API获取
            # TODO: 实现从API获取数据的逻辑
            
            logger.error(f"未找到{symbol}的历史数据")
            return None
        except Exception as e:
            logger.error(f"加载{symbol}的历史数据失败: {e}")
            return None
        
    def run_backtest(self) -> bool:
        """执行回测"""
        if not self.strategy or not self.params['start_date']:
            logger.error("请先配置策略和参数！")
            return False
            
        try:
            # 创建回测实例
            self.backtester = Backtester(self.params['initial_capital'])
            
            # 配置风险和成本参数
            self.backtester.risk_manager.max_position_size = self.params['risk_params']['max_position_size']
            self.backtester.risk_manager.max_drawdown = self.params['risk_params']['max_drawdown']
            self.backtester.risk_manager.max_positions = self.params['risk_params']['max_positions']
            self.backtester.risk_manager.position_sizing_method = self.params['risk_params']['position_sizing_method']
            
            # 更新交易成本设置
            self.backtester.portfolio.transaction_costs.commission_rate = self.params['cost_params']['commission_rate']
            self.backtester.portfolio.transaction_costs.slippage_rate = self.params['cost_params']['slippage_rate']
            self.backtester.portfolio.transaction_costs.min_commission = self.params['cost_params']['min_commission']
            self.backtester.portfolio.transaction_costs.stamp_duty = self.params['cost_params']['stamp_duty']
            
            # 加载数据
            if not self.load_data():
                return False
                
            for symbol, data in self.data_cache.items():
                self.backtester.load_data(symbol, data)
            
            # 运行回测
            self.backtester.run_backtest(
                self.strategy,
                self.params['start_date'],
                self.params['end_date']
            )
            
            # 生成报告
            report_path = self.backtester.generate_report(format='html')
            webbrowser.open(f'file://{report_path}')
            
            return True
            
        except Exception as e:
            logger.error(f"回测执行错误: {e}")
            self._save_checkpoint()  # 保存检查点
            return False
            
    def save_parameters(self, filename: str = "backtest_config.json"):
        """保存回测参数"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / filename
        with open(config_path, 'w') as f:
            json.dump(self.params, f, indent=4, default=str)
        logger.info(f"参数已保存到: {config_path}")

    def load_parameters(self, filename: str = "backtest_config.json"):
        """加载回测参数"""
        try:
            config_path = Path("config") / filename
            if config_path.exists():
                with open(config_path, 'r') as f:
                    loaded_params = json.load(f)
                    # 验证加载的参数
                    if self._validate_loaded_params(loaded_params):
                        self.params.update(loaded_params)
                        logger.info("成功加载参数配置")
                        return True
            return False
        except Exception as e:
            logger.error(f"加载参数失败: {e}")
            return False
            
    def _validate_loaded_params(self, params: dict) -> bool:
        """验证加载的参数是否有效"""
        required_keys = ['initial_capital', 'risk_params', 'cost_params']
        return all(key in params for key in required_keys)
            
    def _save_checkpoint(self):
        """保存回测检查点"""
        if self.backtester:
            checkpoint_dir = Path("checkpoints")
            checkpoint_dir.mkdir(exist_ok=True)
            
            checkpoint = {
                'params': self.params,
                'portfolio_state': {
                    'current_capital': self.backtester.portfolio.current_capital,
                    'positions': self.backtester.portfolio.positions,
                    'trade_history': self.backtester.portfolio.trade_history
                }
            }
            
            checkpoint_path = checkpoint_dir / f"backtest_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, indent=4, default=str)
            logger.info(f"检查点已保存到: {checkpoint_path}")
            
    def view_reports(self):
        """查看历史回测报告"""
        reports_dir = Path("reports/output/backtest")
        if not reports_dir.exists():
            print("回测报告目录不存在")
            return
            
        reports = list(reports_dir.glob("*.html"))
        
        if not reports:
            print("没有找到历史回测报告")
            return
            
        print("\n=== 历史回测报告 ===")
        # 按创建时间排序
        reports.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        for i, report in enumerate(reports, 1):
            created_time = datetime.fromtimestamp(os.path.getctime(report)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{i}. {report.name} (创建于: {created_time})")
            
        choice = input("\n请选择要查看的报告编号（回车返回）: ")
        if choice.isdigit() and 0 < int(choice) <= len(reports):
            report_path = reports[int(choice)-1]
            webbrowser.open(f'file://{report_path}')
            
    def validate_parameters(self) -> bool:
        """验证回测参数是否完整有效"""
        if not self.strategy:
            logger.error("未选择策略")
            return False
            
        if not self.params['symbols']:
            logger.error("未指定交易品种")
            return False
            
        if not self.params['start_date']:
            logger.error("未设置开始日期")
            return False
            
        try:
            start_date = datetime.strptime(self.params['start_date'], '%Y-%m-%d')
            if self.params['end_date']:
                end_date = datetime.strptime(self.params['end_date'], '%Y-%m-%d')
                if end_date <= start_date:
                    logger.error("结束日期必须晚于开始日期")
                    return False
        except ValueError:
            logger.error("日期格式错误")
            return False
            
        # 验证风险参数
        if not (0 < self.params['risk_params']['max_position_size'] <= 1):
            logger.error("最大持仓比例必须在0到1之间")
            return False
            
        if not (0 < self.params['risk_params']['max_drawdown'] <= 1):
            logger.error("最大回撤限制必须在0到1之间")
            return False
            
        return True 

    def _generate_html_report(self, path: Path):
        """生成HTML格式报告"""
        try:
            # 计算当前价格
            current_prices = {
                symbol: df.iloc[-1]['close']
                for symbol, df in self.data_cache.items()
            }
            
            # 基础样式
            css = """
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .section { margin-bottom: 30px; }
                .metric { margin: 10px 0; }
                .metric-name { font-weight: bold; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th, td { padding: 8px; text-align: left; border: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
                .chart { margin: 20px 0; }
                .positive { color: green; }
                .negative { color: red; }
            </style>
            """
            
            # 生成HTML内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>回测报告</title>
                {css}
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body>
                <div class="container">
                    <h1>回测报告</h1>
                    <div class="section">
                        <h2>回测参数</h2>
                        <div class="metric">
                            <span class="metric-name">初始资金:</span> 
                            {self.backtester.portfolio.initial_capital:,.2f}
                        </div>
                        <div class="metric">
                            <span class="metric-name">回测区间:</span> 
                            {min(df.index[0] for df in self.data_cache.values())} 至 
                            {max(df.index[-1] for df in self.data_cache.values())}
                        </div>
                        <div class="metric">
                            <span class="metric-name">交易品种:</span> 
                            {', '.join(self.data_cache.keys())}
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>绩效指标</h2>
                        <div class="metric">
                            <span class="metric-name">总收益率:</span> 
                            <span class="{self._get_color_class(self.backtester.performance_metrics['total_return'])}">
                                {self.backtester.performance_metrics['total_return']:.2%}
                            </span>
                        </div>
                        <div class="metric">
                            <span class="metric-name">年化收益率:</span>
                            <span class="{self._get_color_class(self.backtester.performance_metrics['annual_return'])}">
                                {self.backtester.performance_metrics['annual_return']:.2%}
                            </span>
                        </div>
                        <div class="metric">
                            <span class="metric-name">夏普比率:</span>
                            <span class="{self._get_color_class(self.backtester.performance_metrics['sharpe_ratio'])}">
                                {self.backtester.performance_metrics['sharpe_ratio']:.2f}
                            </span>
                        </div>
                        <div class="metric">
                            <span class="metric-name">最大回撤:</span>
                            <span class="negative">
                                {self.backtester.performance_metrics['max_drawdown']:.2%}
                            </span>
                        </div>
                        <div class="metric">
                            <span class="metric-name">波动率:</span>
                            {self.backtester.performance_metrics['volatility']:.2%}
                        </div>
                        <div class="metric">
                            <span class="metric-name">胜率:</span>
                            {self.backtester.performance_metrics['win_rate']:.2%}
                        </div>
                        <div class="metric">
                            <span class="metric-name">盈亏比:</span>
                            {self.backtester.performance_metrics['profit_factor']:.2f}
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>交易记录</h2>
                        <table>
                            <tr>
                                <th>时间</th>
                                <th>代码</th>
                                <th>类型</th>
                                <th>数量</th>
                                <th>价格</th>
                                <th>成本</th>
                            </tr>
                            {''.join(
                                f"<tr><td>{trade['timestamp']}</td>"
                                f"<td>{trade['symbol']}</td>"
                                f"<td>{trade['type']}</td>"
                                f"<td>{trade['quantity']}</td>"
                                f"<td>{trade['price']:.2f}</td>"
                                f"<td>{trade['cost']:.2f}</td></tr>"
                                for trade in self.backtester.portfolio.trade_history[-50:]  # 显示最近50条记录
                            )}
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>当前持仓</h2>
                        <table>
                            <tr>
                                <th>代码</th>
                                <th>数量</th>
                                <th>当前价值</th>
                                <th>持仓比例</th>
                            </tr>
                            {''.join(
                                f"<tr><td>{symbol}</td>"
                                f"<td>{quantity}</td>"
                                f"<td>{quantity * self.data_cache[symbol].iloc[-1]['close']:.2f}</td>"
                                f"<td>{quantity * self.data_cache[symbol].iloc[-1]['close'] / self.backtester.portfolio.get_portfolio_value(current_prices):.2%}</td></tr>"
                                for symbol, quantity in self.backtester.portfolio.positions.items()
                            )}
                        </table>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存报告
            with open(path, 'w') as f:
                f.write(html_content)
                
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            raise
            
    def _get_color_class(self, value: float) -> str:
        """获取数值的颜色类名"""
        return "positive" if value > 0 else "negative" if value < 0 else "" 