import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from .technical_analyzer import TechnicalAnalyzer

class StrategyManager:
    """策略管理器
    
    提供各种交易策略的实现和管理：
    - 移动平均线交叉策略
    - MACD策略
    - RSI策略
    - 布林带策略
    - 成交量策略
    - KDJ策略
    - 多因子策略
    
    每个策略都包含：
    - 信号生成
    - 参数优化
    - 风险控制
    - 绩效评估
    
    Attributes:
        logger: 日志记录器
        indicators: 技术指标计算器
    """
    
    def __init__(self):
        """初始化策略管理器"""
        self.logger = logging.getLogger(__name__)
        self.indicators = TechnicalAnalyzer()
        
    def apply_strategy(self, df: pd.DataFrame, strategy_name: str, 
                      params: Optional[Dict] = None) -> pd.DataFrame:
        """应用选定的交易策略
        
        Args:
            df: 包含价格和技术指标的DataFrame
            strategy_name: 策略名称
            params: 策略参数字典，可选
            
        Returns:
            添加了交易信号的DataFrame
            
        Raises:
            ValueError: 如果策略名称无效
        """
        try:
            # 确保数据包含必要的技术指标
            df = self.indicators.calculate_all(df)
            
            # 策略映射表
            strategy_map = {
                'ma_cross': self._ma_cross_strategy,
                'macd': self._macd_strategy,
                'rsi': self._rsi_strategy,
                'bollinger_bands': self._bollinger_bands_strategy,
                'volume': self._volume_strategy,
                'kdj': self._kdj_strategy,
                'multi_factor': self._multi_factor_strategy
            }
            
            if strategy_name not in strategy_map:
                raise ValueError(f"未找到策略: {strategy_name}")
                
            # 执行策略
            params = params or {}
            df = strategy_map[strategy_name](df, **params)
            
            # 添加风险控制
            if params.get('use_risk_control', True):
                stop_loss = params.get('stop_loss', 0.05)
                take_profit = params.get('take_profit', 0.1)
                df = self._add_risk_control(df, stop_loss, take_profit)
            
            # 添加持仓信息
            df['position'] = self._calculate_positions(df['signal'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"应用策略时出错: {str(e)}")
            return df

    def _ma_cross_strategy(self, df: pd.DataFrame, 
                          short_period: int = 20, 
                          long_period: int = 60) -> pd.DataFrame:
        """移动平均线交叉策略
        
        生成信号规则：
        - 短期均线上穿长期均线：买入信号(1)
        - 短期均线下穿长期均线：卖出信号(-1)
        - 其他情况：持仓不变(0)
        
        Args:
            df: 包含价格数据的DataFrame
            short_period: 短期均线周期，默认20
            long_period: 长期均线周期，默认60
            
        Returns:
            添加了交易信号的DataFrame
        """
        try:
            # 计算金叉和死叉
            df['signal'] = 0
            df.loc[df[f'ma{short_period}'] > df[f'ma{long_period}'], 'signal'] = 1
            df.loc[df[f'ma{short_period}'] < df[f'ma{long_period}'], 'signal'] = -1
            
            # 只在交叉点产生信号
            df['signal'] = df['signal'].diff()
            
            return df
        except Exception as e:
            self.logger.error(f"执行MA交叉策略时出错: {str(e)}")
            return df
            
    def _macd_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD策略"""
        try:
            df['signal'] = 0
            # MACD柱状图由负变正
            df.loc[(df['macd_hist'] > 0) & (df['macd_hist'].shift(1) < 0), 'signal'] = 1
            # MACD柱状图由正变负
            df.loc[(df['macd_hist'] < 0) & (df['macd_hist'].shift(1) > 0), 'signal'] = -1
            return df
        except Exception as e:
            self.logger.error(f"MACD策略计算出错: {str(e)}")
            return df
            
    def _rsi_strategy(self, df: pd.DataFrame, 
                     oversold: int = 30, 
                     overbought: int = 70) -> pd.DataFrame:
        """
        RSI策略
        
        Args:
            df (pd.DataFrame): 数据
            oversold (int): 超卖阈值
            overbought (int): 超买阈值
        """
        try:
            df['signal'] = 0
            # RSI超卖
            df.loc[(df['rsi'] < oversold) & (df['rsi'].shift(1) >= oversold), 'signal'] = 1
            # RSI超买
            df.loc[(df['rsi'] > overbought) & (df['rsi'].shift(1) <= overbought), 'signal'] = -1
            return df
        except Exception as e:
            self.logger.error(f"RSI策略计算出错: {str(e)}")
            return df
            
    def _bollinger_bands_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """布林带策略"""
        try:
            df['signal'] = 0
            # 价格触及下轨
            df.loc[(df['close'] < df['bb_lower']) & (df['close'].shift(1) >= df['bb_lower']), 'signal'] = 1
            # 价格触及上轨
            df.loc[(df['close'] > df['bb_upper']) & (df['close'].shift(1) <= df['bb_upper']), 'signal'] = -1
            return df
        except Exception as e:
            self.logger.error(f"布林带策略计算出错: {str(e)}")
            return df
            
    def _volume_strategy(self, df: pd.DataFrame, 
                        volume_threshold: float = 1.5) -> pd.DataFrame:
        """
        成交量策略
        
        Args:
            df (pd.DataFrame): 数据
            volume_threshold (float): 成交量放大阈值
        """
        try:
            df['signal'] = 0
            # 放量上涨
            volume_increase = df['volume'] > df['volume_ma5'] * volume_threshold
            price_increase = df['close'] > df['close'].shift(1)
            df.loc[volume_increase & price_increase, 'signal'] = 1
            # 放量下跌
            price_decrease = df['close'] < df['close'].shift(1)
            df.loc[volume_increase & price_decrease, 'signal'] = -1
            return df
        except Exception as e:
            self.logger.error(f"成交量策略计算出错: {str(e)}")
            return df

    def _kdj_strategy(self, df: pd.DataFrame, 
                     oversold: int = 20, 
                     overbought: int = 80) -> pd.DataFrame:
        """
        KDJ策略
        
        Args:
            df (pd.DataFrame): 数据
            oversold (int): 超卖阈值
            overbought (int): 超买阈值
        """
        try:
            df['signal'] = 0
            # K线上穿D线且处于超卖区域
            df.loc[(df['k'] > df['d']) & (df['k'].shift(1) <= df['d'].shift(1)) & 
                  (df['k'] < oversold), 'signal'] = 1
            # K线下穿D线且处于超买区域
            df.loc[(df['k'] < df['d']) & (df['k'].shift(1) >= df['d'].shift(1)) & 
                  (df['k'] > overbought), 'signal'] = -1
            return df
        except Exception as e:
            self.logger.error(f"KDJ策略计算出错: {str(e)}")
            return df
            
    def _multi_factor_strategy(self, df: pd.DataFrame, 
                             weight_ma: float = 1.0,
                             weight_macd: float = 1.0,
                             weight_rsi: float = 1.0,
                             weight_bb: float = 1.0,
                             weight_kdj: float = 1.0,
                             weight_vol: float = 0.5) -> pd.DataFrame:
        """
        增强版多因子策略
        """
        try:
            # 计算各个策略的信号
            strategies = {
                'ma': (self._ma_cross_strategy, weight_ma),
                'macd': (self._macd_strategy, weight_macd),
                'rsi': (self._rsi_strategy, weight_rsi),
                'bb': (self._bollinger_bands_strategy, weight_bb),
                'kdj': (self._kdj_strategy, weight_kdj),
                'volume': (self._volume_strategy, weight_vol)
            }
            
            # 计算各个策略信号
            signals = {}
            for name, (strategy_func, _) in strategies.items():
                temp_df = strategy_func(df.copy())
                signals[f'{name}_signal'] = temp_df['signal']
            
            # 添加信号列到DataFrame
            for col, signal in signals.items():
                df[col] = signal
            
            # 计算加权综合信号
            total_weight = sum(weight for _, weight in strategies.values())
            df['signal'] = sum(df[f'{name}_signal'] * weight 
                             for name, (_, weight) in strategies.items()) / total_weight
            
            # 信号阈值
            df.loc[df['signal'] > 0.5, 'signal'] = 1
            df.loc[df['signal'] < -0.5, 'signal'] = -1
            df.loc[(df['signal'] >= -0.5) & (df['signal'] <= 0.5), 'signal'] = 0
            
            return df
        except Exception as e:
            self.logger.error(f"多因子策略计算出错: {str(e)}")
            return df

    def _add_risk_control(self, df: pd.DataFrame, 
                         stop_loss: float = 0.05,
                         take_profit: float = 0.1) -> pd.DataFrame:
        """添加风险控制
        
        实现止损和止盈：
        - 当亏损超过止损线时，强制平仓
        - 当盈利超过止盈线时，锁定利润
        
        Args:
            df: 包含交易信号的DataFrame
            stop_loss: 止损比例，默认5%
            take_profit: 止盈比例，默认10%
            
        Returns:
            添加了风险控制的DataFrame
        """
        try:
            # 计算收益率
            df['returns'] = df['close'].pct_change()
            
            # 计算累计收益
            df['cumulative_returns'] = (1 + df['returns']).cumprod()
            
            # 添加止损止盈
            df.loc[df['cumulative_returns'] <= (1 - stop_loss), 'signal'] = -1
            df.loc[df['cumulative_returns'] >= (1 + take_profit), 'signal'] = -1
            
            return df
        except Exception as e:
            self.logger.error(f"添加风险控制时出错: {str(e)}")
            return df

    def _calculate_positions(self, signals: pd.Series) -> pd.Series:
        """计算持仓
        
        根据交易信号计算持仓：
        1: 持有多头
        0: 空仓
        -1: 持有空头
        
        Args:
            signals: 交易信号序列
            
        Returns:
            持仓序列
        """
        try:
            return signals.cumsum().fillna(0)
        except Exception as e:
            self.logger.error(f"计算持仓时出错: {str(e)}")
            return pd.Series(0, index=signals.index)

    def evaluate_strategy(self, df: pd.DataFrame) -> Dict:
        """
        评估策略性能
        
        Args:
            df (pd.DataFrame): 包含交易信号和持仓的DataFrame
            
        Returns:
            Dict: 策略评估指标
        """
        try:
            # 计算每日收益率
            df['daily_returns'] = df['close'].pct_change()
            
            # 计算策略收益率
            df['strategy_returns'] = df['daily_returns'] * df['position'].shift(1)
            
            # 计算累计收益
            df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
            
            # 计算评估指标
            total_returns = df['cumulative_returns'].iloc[-1] - 1
            annual_returns = (1 + total_returns) ** (252 / len(df)) - 1
            
            # 计算夏普比率
            risk_free_rate = 0.02  # 假设无风险利率为2%
            excess_returns = df['strategy_returns'] - risk_free_rate/252
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
            
            # 计算最大回撤
            cumulative = df['cumulative_returns']
            rolling_max = cumulative.expanding().max()
            drawdowns = cumulative/rolling_max - 1
            max_drawdown = drawdowns.min()
            
            return {
                'total_returns': total_returns,
                'annual_returns': annual_returns,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': len(df[df['strategy_returns'] > 0]) / len(df[df['strategy_returns'] != 0]),
                'profit_factor': abs(df[df['strategy_returns'] > 0]['strategy_returns'].sum() / 
                                   df[df['strategy_returns'] < 0]['strategy_returns'].sum())
            }
            
        except Exception as e:
            self.logger.error(f"策略评估时出错: {str(e)}")
            return {}

    def optimize_strategy_params(self, df: pd.DataFrame, strategy_name: str, 
                               param_grid: Dict[str, List]) -> Dict:
        """
        优化策略参数
        
        Args:
            df (pd.DataFrame): 数据
            strategy_name (str): 策略名称
            param_grid (Dict[str, List]): 参数网格
            
        Returns:
            Dict: 最优参数组合
        """
        try:
            best_sharpe = -np.inf
            best_params = {}
            
            # 生成参数组合
            from itertools import product
            param_names = list(param_grid.keys())
            param_values = list(param_grid.values())
            
            for params in product(*param_values):
                param_dict = dict(zip(param_names, params))
                
                # 应用策略
                result_df = self.apply_strategy(df.copy(), strategy_name, param_dict)
                
                # 评估策略
                metrics = self.evaluate_strategy(result_df)
                current_sharpe = metrics.get('sharpe_ratio', -np.inf)
                
                # 更新最优参数
                if current_sharpe > best_sharpe:
                    best_sharpe = current_sharpe
                    best_params = param_dict
            
            return {
                'best_params': best_params,
                'best_sharpe': best_sharpe
            }
            
        except Exception as e:
            self.logger.error(f"参数优化时出错: {str(e)}")
            return {}

    def combine_strategies(self, df: pd.DataFrame, strategy_configs: List[Dict]) -> pd.DataFrame:
        """
        组合多个策略
        
        Args:
            df (pd.DataFrame): 数据
            strategy_configs (List[Dict]): 策略配置列表，每个配置包含策略名称和权重
        """
        try:
            signals = pd.DataFrame(index=df.index)
            total_weight = sum(config['weight'] for config in strategy_configs)
            
            for config in strategy_configs:
                strategy_df = self.apply_strategy(df.copy(), 
                                               config['name'], 
                                               config.get('params', {}))
                signals[f"{config['name']}_signal"] = strategy_df['signal'] * (config['weight'] / total_weight)
            
            # 合并信号
            df['signal'] = signals.sum(axis=1)
            df.loc[df['signal'] > 0.5, 'signal'] = 1
            df.loc[df['signal'] < -0.5, 'signal'] = -1
            df.loc[(df['signal'] >= -0.5) & (df['signal'] <= 0.5), 'signal'] = 0
            
            return df
        except Exception as e:
            self.logger.error(f"组合策略时出错: {str(e)}")
            return df

    def compare_strategies(self, df: pd.DataFrame, strategy_list: List[str]) -> Dict:
        """
        比较多个策略的性能
        
        Args:
            df (pd.DataFrame): 数据
            strategy_list (List[str]): 策略名称列表
        """
        try:
            results = {}
            for strategy in strategy_list:
                # 应用策略
                strategy_df = self.apply_strategy(df.copy(), strategy)
                
                # 评估策略
                metrics = self.evaluate_strategy(strategy_df)
                results[strategy] = metrics
                
            # 计算相关性
            signals = pd.DataFrame()
            for strategy in strategy_list:
                strategy_df = self.apply_strategy(df.copy(), strategy)
                signals[strategy] = strategy_df['signal']
            
            correlation = signals.corr()
            
            return {
                'metrics': results,
                'correlation': correlation.to_dict()
            }
        except Exception as e:
            self.logger.error(f"比较策略时出错: {str(e)}")
            return {}

    def _calculate_trading_costs(self, df: pd.DataFrame, 
                           commission_rate: float = 0.001,
                           slippage: float = 0.001) -> pd.DataFrame:
        """
        计算交易成本和滑点
        
        Args:
            df (pd.DataFrame): 数据
            commission_rate (float): 佣金率
            slippage (float): 滑点率
        """
        try:
            # 找出交易发生的位置
            trades = df['signal'] != 0
            
            # 计算交易成本
            df['trading_cost'] = 0.0
            df.loc[trades, 'trading_cost'] = (df.loc[trades, 'close'] * 
                                            (commission_rate + slippage))
            
            # 调整策略收益
            df['strategy_returns'] = df['strategy_returns'] - df['trading_cost']
            
            return df
        except Exception as e:
            self.logger.error(f"计算交易成本时出错: {str(e)}")
            return df