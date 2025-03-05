"""Risk manager for controlling trading risks."""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from core.portfolio import Portfolio

class RiskManager:
    """
    风险管理器：控制交易风险
    
    功能：
    1. 头寸规模控制
    2. 回撤控制
    3. 持仓数量控制
    4. 交易信号过滤
    """
    
    def __init__(
        self,
        max_position_size: float = 0.1,
        max_drawdown: float = 0.2,
        max_positions: int = 5,
        position_sizing_method: str = 'equal',
        volatility_window: int = 20,
        target_volatility: float = 0.15,
        max_leverage: float = 2.0
    ):
        """
        初始化风险管理器
        
        Args:
            max_position_size: 最大持仓比例
            max_drawdown: 最大回撤限制
            max_positions: 最大持仓数量
            position_sizing_method: 头寸管理方法 ('equal' or 'volatility')
            volatility_window: 波动率计算窗口
            target_volatility: 目标波动率
            max_leverage: 最大杠杆倍数
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.max_positions = max_positions
        self.position_sizing_method = position_sizing_method
        self.volatility_window = volatility_window
        self.target_volatility = target_volatility
        self.max_leverage = max_leverage
        
        # 缓存数据
        self._volatility_cache = {}
        self._correlation_cache = {}
        self._last_update = None
        
    def filter_signals(self, signals: List[Dict], portfolio: Portfolio) -> List[Dict]:
        """
        过滤交易信号
        
        Args:
            signals: 原始交易信号列表
            portfolio: 当前投资组合
            
        Returns:
            List[Dict]: 过滤后的交易信号
        """
        if not signals:
            return []
            
        filtered_signals = []
        current_positions = sum(1 for qty in portfolio.positions.values() if qty > 0)
        
        # 计算当前组合风险
        portfolio_risk = self._calculate_portfolio_risk(portfolio)
        
        for signal in signals:
            # 检查是否超过最大持仓数量
            if (signal['type'] == 'buy' and 
                current_positions >= self.max_positions and 
                portfolio.get_position(signal['symbol']) == 0):
                continue
                
            # 检查持仓规模
            if not self._check_position_size(signal, portfolio):
                continue
                
            # 检查回撤限制
            if not self._check_drawdown(portfolio):
                continue
                
            # 检查组合风险
            if not self._check_portfolio_risk(signal, portfolio, portfolio_risk):
                continue
                
            # 调整头寸规模
            adjusted_signal = self._adjust_position_size(signal, portfolio)
            if adjusted_signal:
                filtered_signals.append(adjusted_signal)
                
        return filtered_signals
        
    def _calculate_volatility(self, data: pd.Series) -> float:
        """计算波动率"""
        returns = data.pct_change().dropna()
        if len(returns) < 2:
            return 0.0
        return returns.std() * np.sqrt(252)
        
    def _calculate_correlation(self, data1: pd.Series, data2: pd.Series) -> float:
        """计算相关性"""
        returns1 = data1.pct_change().dropna()
        returns2 = data2.pct_change().dropna()
        if len(returns1) < 2 or len(returns2) < 2:
            return 0.0
        return returns1.corr(returns2)
        
    def _calculate_portfolio_risk(self, portfolio: Portfolio) -> Dict:
        """计算组合风险指标"""
        # 获取当前持仓的股票
        active_positions = {
            symbol: qty for symbol, qty in portfolio.positions.items() 
            if qty > 0
        }
        
        if not active_positions:
            return {
                'volatility': 0.0,
                'var': 0.0,
                'leverage': 0.0
            }
            
        # 计算组合波动率
        position_values = []
        volatilities = []
        correlations = []
        
        for symbol, qty in active_positions.items():
            position_value = portfolio.get_position_value(symbol)
            position_values.append(position_value)
            
            # 获取或计算波动率
            if symbol not in self._volatility_cache:
                self._volatility_cache[symbol] = self._calculate_volatility(
                    portfolio.get_price_history(symbol)
                )
            volatilities.append(self._volatility_cache[symbol])
            
            # 计算相关性矩阵
            for other_symbol in active_positions:
                if symbol != other_symbol:
                    corr_key = tuple(sorted([symbol, other_symbol]))
                    if corr_key not in self._correlation_cache:
                        self._correlation_cache[corr_key] = self._calculate_correlation(
                            portfolio.get_price_history(symbol),
                            portfolio.get_price_history(other_symbol)
                        )
                    correlations.append(self._correlation_cache[corr_key])
                    
        # 计算组合风险指标
        total_value = sum(position_values)
        weights = np.array(position_values) / total_value if total_value > 0 else np.zeros_like(position_values)
        
        # 计算组合波动率
        portfolio_volatility = np.sqrt(
            np.sum(weights ** 2 * np.array(volatilities) ** 2) +
            np.sum(weights.reshape(-1, 1) @ weights.reshape(1, -1) * 
                  np.array(correlations).reshape(len(weights), len(weights)))
        )
        
        # 计算VaR
        var_95 = portfolio_volatility * 1.645 * total_value
        
        # 计算杠杆率
        leverage = total_value / portfolio.get_total_value()
        
        return {
            'volatility': portfolio_volatility,
            'var': var_95,
            'leverage': leverage
        }
        
    def _check_portfolio_risk(self, signal: Dict, portfolio: Portfolio, portfolio_risk: Dict) -> bool:
        """检查组合风险是否在可接受范围内"""
        # 检查杠杆率
        if portfolio_risk['leverage'] >= self.max_leverage:
            return False
            
        # 检查波动率
        if portfolio_risk['volatility'] > self.target_volatility:
            return False
            
        return True
        
    def _check_position_size(self, signal: Dict, portfolio: Portfolio) -> bool:
        """检查持仓规模是否符合限制"""
        if signal['type'] == 'buy':
            # 计算交易后的持仓市值
            total_value = portfolio.get_total_value()
            position_value = signal['price'] * signal['quantity']
            
            # 检查是否超过最大持仓比例
            if position_value / total_value > self.max_position_size:
                return False
                
        return True
        
    def _check_drawdown(self, portfolio: Portfolio) -> bool:
        """检查是否触及最大回撤限制"""
        current_value = portfolio.get_total_value()
        initial_value = portfolio.initial_capital
        
        if current_value < initial_value * (1 - self.max_drawdown):
            return False
            
        return True
        
    def _adjust_position_size(self, signal: Dict, portfolio: Portfolio) -> Optional[Dict]:
        """调整头寸规模"""
        if signal['type'] != 'buy':
            return signal
            
        total_value = portfolio.get_total_value()
        
        if self.position_sizing_method == 'equal':
            # 等额分配
            position_value = min(
                total_value * self.max_position_size,
                signal['price'] * signal['quantity']
            )
            
        elif self.position_sizing_method == 'volatility':
            # 基于波动率的头寸管理
            symbol = signal['symbol']
            
            # 获取或计算波动率
            if symbol not in self._volatility_cache:
                self._volatility_cache[symbol] = self._calculate_volatility(
                    portfolio.get_price_history(symbol)
                )
            
            volatility = self._volatility_cache[symbol]
            if volatility == 0:
                return None
                
            # 根据目标波动率调整持仓规模
            target_position_value = (
                total_value * 
                self.max_position_size * 
                (self.target_volatility / volatility)
            )
            
            position_value = min(
                target_position_value,
                signal['price'] * signal['quantity']
            )
            
        else:
            position_value = signal['price'] * signal['quantity']
            
        # 调整数量
        adjusted_quantity = int(position_value / signal['price'])
        if adjusted_quantity <= 0:
            return None
            
        adjusted_signal = signal.copy()
        adjusted_signal['quantity'] = adjusted_quantity
        return adjusted_signal
        
    def update_cache(self) -> None:
        """更新缓存数据"""
        current_time = datetime.now()
        if (self._last_update is None or 
            current_time - self._last_update > timedelta(hours=1)):
            self._volatility_cache.clear()
            self._correlation_cache.clear()
            self._last_update = current_time 