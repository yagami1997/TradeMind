"""Portfolio class for managing backtest portfolio."""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

@dataclass
class CompressionConfig:
    """数据压缩配置"""
    enabled: bool = True
    auto_compress_threshold: int = 10000  # 自动压缩阈值
    min_points: int = 1000  # 压缩后最小保留点数
    max_points: int = 5000  # 压缩后最大保留点数
    importance_window: int = 20  # 重要性计算窗口
    
class DataType(Enum):
    """数据类型枚举"""
    TRADES = 'trades'
    POSITIONS = 'positions'
    EQUITY = 'equity'
    PRICE = 'price'

class Portfolio:
    """
    投资组合类：管理回测期间的投资组合状态
    
    功能：
    1. 跟踪现金和持仓
    2. 记录交易历史
    3. 计算组合价值
    4. 生成权益曲线
    5. 智能数据压缩
    """
    
    def __init__(
        self, 
        initial_capital: float, 
        symbols: List[str],
        max_history_length: int = 10000,
        cleanup_threshold: int = 5000,
        compression_config: Optional[CompressionConfig] = None
    ):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
            symbols: 交易品种列表
            max_history_length: 最大历史记录长度
            cleanup_threshold: 清理阈值，达到此数量时触发清理
            compression_config: 数据压缩配置
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.symbols = symbols
        self.max_history_length = max_history_length
        self.cleanup_threshold = cleanup_threshold
        self.compression_config = compression_config or CompressionConfig()
        
        # 持仓信息
        self.positions = {symbol: 0 for symbol in symbols}
        self.position_avg_price = {symbol: 0.0 for symbol in symbols}
        self.position_values = {symbol: 0.0 for symbol in symbols}
        
        # 历史记录
        self.trades = []
        self.positions_history = []
        self.equity_curve = []
        
        # 性能指标
        self.peak_value = initial_capital
        self.current_value = initial_capital
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.daily_returns = {}
        
        # 压缩状态
        self._compressed = {
            DataType.TRADES: False,
            DataType.POSITIONS: False,
            DataType.EQUITY: False,
            DataType.PRICE: False
        }
        
        # 价格历史
        self.price_history = {}
        
    def _calculate_point_importance(
        self, 
        data: pd.Series, 
        window: int = 20
    ) -> pd.Series:
        """
        计算数据点的重要性
        
        使用以下指标计算重要性：
        1. 局部极值（高点/低点）
        2. 趋势变化点
        3. 波动率变化点
        
        Args:
            data: 时间序列数据
            window: 计算窗口
            
        Returns:
            pd.Series: 重要性得分
        """
        importance = pd.Series(0.0, index=data.index)
        
        # 1. 局部极值
        rolling_max = data.rolling(window=window, center=True).max()
        rolling_min = data.rolling(window=window, center=True).min()
        importance += ((data == rolling_max) | (data == rolling_min)).astype(float)
        
        # 2. 趋势变化点
        returns = data.pct_change()
        trend = returns.rolling(window=window).mean()
        trend_change = abs(trend.diff())
        importance += trend_change / trend_change.std()
        
        # 3. 波动率变化点
        volatility = returns.rolling(window=window).std()
        vol_change = abs(volatility.diff())
        importance += vol_change / vol_change.std()
        
        return importance
        
    def _compress_series(
        self,
        data: pd.Series,
        min_points: int,
        max_points: int,
        importance_window: int
    ) -> pd.Series:
        """
        压缩时间序列数据，保留重要点位
        
        Args:
            data: 原始数据
            min_points: 最小保留点数
            max_points: 最大保留点数
            importance_window: 重要性计算窗口
            
        Returns:
            pd.Series: 压缩后的数据
        """
        if len(data) <= max_points:
            return data
            
        # 计算点的重要性
        importance = self._calculate_point_importance(data, importance_window)
        
        # 确保保留首尾点
        keep_points = set([data.index[0], data.index[-1]])
        
        # 添加局部极值点
        keep_points.update(data[data == data.max()].index)
        keep_points.update(data[data == data.min()].index)
        
        # 根据重要性选择其他点
        remaining_points = set(data.index) - keep_points
        importance_threshold = importance[list(remaining_points)].quantile(
            1 - (max_points - len(keep_points)) / len(remaining_points)
        )
        keep_points.update(
            importance[importance >= importance_threshold].index
        )
        
        # 如果点数不足，添加均匀采样点
        if len(keep_points) < min_points:
            step = len(data) // (min_points - len(keep_points))
            keep_points.update(data.index[::step])
            
        return data[sorted(keep_points)]
        
    def _compress_trades(self) -> None:
        """压缩交易历史"""
        if self._compressed[DataType.TRADES]:
            return
            
        if len(self.trades) <= self.compression_config.max_points:
            return
            
        # 转换为DataFrame进行处理
        df = pd.DataFrame(self.trades)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 按日期聚合交易
        daily_trades = df.resample('D').agg({
            'type': 'count',
            'symbol': 'first',
            'quantity': 'sum',
            'price': 'mean',
            'cost': 'sum'
        }).dropna()
        
        # 压缩日期序列
        important_dates = self._compress_series(
            daily_trades['quantity'],
            self.compression_config.min_points,
            self.compression_config.max_points,
            self.compression_config.importance_window
        ).index
        
        # 重建交易记录
        compressed_trades = []
        for date in important_dates:
            day_trades = df.loc[date.strftime('%Y-%m-%d')]
            if len(day_trades) > 0:
                if len(day_trades) == 1:
                    compressed_trades.append(day_trades.to_dict('records')[0])
                else:
                    # 合并同一天的交易
                    compressed_trades.append({
                        'date': date,
                        'type': 'summary',
                        'trades_count': len(day_trades),
                        'total_quantity': day_trades['quantity'].sum(),
                        'avg_price': day_trades['price'].mean(),
                        'total_cost': day_trades['cost'].sum()
                    })
                    
        self.trades = compressed_trades
        self._compressed[DataType.TRADES] = True
        
    def _compress_positions_history(self) -> None:
        """压缩持仓历史"""
        if self._compressed[DataType.POSITIONS]:
            return
            
        if len(self.positions_history) <= self.compression_config.max_points:
            return
            
        # 转换为DataFrame
        df = pd.DataFrame(self.positions_history)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算持仓变化
        position_changes = df['positions'].apply(
            lambda x: sum(abs(x[s]['quantity']) for s in x)
        )
        
        # 选择重要时间点
        important_dates = self._compress_series(
            position_changes,
            self.compression_config.min_points,
            self.compression_config.max_points,
            self.compression_config.importance_window
        ).index
        
        # 重建持仓历史
        self.positions_history = df.loc[important_dates].reset_index().to_dict('records')
        self._compressed[DataType.POSITIONS] = True
        
    def _compress_equity_curve(self) -> None:
        """压缩权益曲线"""
        if self._compressed[DataType.EQUITY]:
            return
            
        if len(self.equity_curve) <= self.compression_config.max_points:
            return
            
        # 转换为DataFrame
        df = pd.DataFrame(self.equity_curve)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 压缩权益曲线
        important_dates = self._compress_series(
            df['value'],
            self.compression_config.min_points,
            self.compression_config.max_points,
            self.compression_config.importance_window
        ).index
        
        # 重建权益曲线
        self.equity_curve = df.loc[important_dates].reset_index().to_dict('records')
        self._compressed[DataType.EQUITY] = True
        
    def _check_and_compress(self) -> None:
        """检查并执行数据压缩"""
        if not self.compression_config.enabled:
            return
            
        # 检查是否需要压缩
        for data_type in DataType:
            if data_type == DataType.TRADES and len(self.trades) > self.compression_config.auto_compress_threshold:
                self._compress_trades()
            elif data_type == DataType.POSITIONS and len(self.positions_history) > self.compression_config.auto_compress_threshold:
                self._compress_positions_history()
            elif data_type == DataType.EQUITY and len(self.equity_curve) > self.compression_config.auto_compress_threshold:
                self._compress_equity_curve()
                
    def update(self, date: datetime, market_data: Dict[str, pd.Series], trades: List[Dict]) -> None:
        """
        更新投资组合状态
        
        Args:
            date: 当前日期
            market_data: 市场数据，包含每个股票的OHLCV数据
            trades: 当日交易列表
        """
        # 更新价格历史
        for symbol, data in market_data.items():
            self.update_price_history(symbol, data['close'], date)
            
        # 执行交易
        for trade in trades:
            self._process_trade(trade)
            self.trades.append(trade)
        
        # 更新持仓价值
        total_value = self.cash
        positions = {}
        
        for symbol, quantity in self.positions.items():
            if quantity != 0 and symbol in market_data:
                price = market_data[symbol]['close']
                market_value = quantity * price
                total_value += market_value
                positions[symbol] = {
                    'quantity': quantity,
                    'price': price,
                    'value': market_value,
                    'avg_cost': self.position_avg_price[symbol]
                }
        
        # 更新最高市值
        self.high_value = max(self.high_value, total_value)
        
        # 更新权益曲线
        self.equity_curve.append({
            'date': date,
            'value': total_value,
            'cash': self.cash,
            'high_value': self.high_value
        })
        
        self.positions_history.append({
            'date': date,
            'positions': positions.copy()
        })
        
        self.current_value = total_value
        
        # 更新最大回撤
        if len(self.equity_curve) > 1:
            peak = self.equity_curve[-1]['value']
            self.current_drawdown = (peak - total_value) / peak
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
            
        # 更新日收益率
        if len(self.equity_curve) > 1:
            prev_value = self.equity_curve[-2]['value']
            self.daily_returns[date] = (total_value - prev_value) / prev_value
            
        # 检查是否需要清理历史数据
        self._check_and_cleanup()
        
        # 更新峰值
        if total_value > self.peak_value:
            self.peak_value = total_value
        
        # 检查是否需要压缩数据
        self._check_and_compress()
        
    def _check_and_cleanup(self) -> None:
        """检查并清理历史数据"""
        if (len(self.trades) > self.cleanup_threshold or
            len(self.positions_history) > self.cleanup_threshold or
            len(self.equity_curve) > self.cleanup_threshold):
            self._cleanup_history()
            
    def _cleanup_history(self) -> None:
        """清理历史数据"""
        if len(self.trades) > self.max_history_length:
            self.trades = self.trades[-self.max_history_length:]
            
        if len(self.positions_history) > self.max_history_length:
            self.positions_history = self.positions_history[-self.max_history_length:]
            
        if len(self.equity_curve) > self.max_history_length:
            self.equity_curve = self.equity_curve[-self.max_history_length:]
            
    def _process_trade(self, trade: Dict) -> None:
        """处理单个交易"""
        symbol = trade['symbol']
        quantity = trade['quantity']
        price = trade['price']
        cost = trade['cost']
        
        if trade['type'] == 'buy':
            # 买入更新
            old_quantity = self.positions[symbol]
            old_cost = old_quantity * self.position_avg_price[symbol]
            new_cost = quantity * price
            
            self.positions[symbol] += quantity
            self.position_avg_price[symbol] = (old_cost + new_cost) / self.positions[symbol]
            self.cash -= (price * quantity + cost)
            
        elif trade['type'] == 'sell':
            # 卖出更新
            self.positions[symbol] -= quantity
            self.cash += (price * quantity - cost)
            
            if self.positions[symbol] == 0:
                self.position_avg_price[symbol] = 0.0
                
    def get_total_value(self) -> float:
        """获取当前总市值"""
        return self.current_value
        
    def get_position(self, symbol: str) -> int:
        """获取某个品种的持仓数量"""
        return self.positions.get(symbol, 0)
        
    def get_position_value(self, symbol: str, price: float) -> float:
        """计算某个持仓的市值"""
        return self.positions.get(symbol, 0) * price
        
    def get_trades(self, compressed: bool = True) -> List[Dict]:
        """获取交易历史"""
        if compressed and not self._compressed[DataType.TRADES]:
            self._compress_trades()
        return self.trades
        
    def get_positions_history(self, compressed: bool = True) -> List[Dict]:
        """获取持仓历史"""
        if compressed and not self._compressed[DataType.POSITIONS]:
            self._compress_positions_history()
        return self.positions_history
        
    def get_equity_curve(self, compressed: bool = True) -> List[Dict]:
        """获取权益曲线"""
        if compressed and not self._compressed[DataType.EQUITY]:
            self._compress_equity_curve()
        return self.equity_curve
        
    def get_summary(self) -> Dict[str, Any]:
        """获取组合摘要信息"""
        return {
            'initial_capital': self.initial_capital,
            'current_value': self.current_value,
            'cash': self.cash,
            'positions': self.positions.copy(),
            'position_avg_price': self.position_avg_price.copy(),
            'total_trades': len(self.trades),
            'total_positions': sum(1 for qty in self.positions.values() if qty > 0)
        }
        
    def get_price_history(self, symbol: str, window: int = 20) -> pd.Series:
        """
        获取股票的历史价格数据
        
        Args:
            symbol: 股票代码
            window: 历史数据窗口大小
            
        Returns:
            pd.Series: 历史价格数据
        """
        if symbol not in self.price_history:
            return pd.Series()
            
        prices = self.price_history[symbol]
        if len(prices) > window:
            return prices[-window:]
        return prices
        
    def update_price_history(self, symbol: str, price: float, date: datetime) -> None:
        """
        更新价格历史数据
        
        Args:
            symbol: 股票代码
            price: 当前价格
            date: 数据时间
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = pd.Series(dtype=float)
            
        self.price_history[symbol][date] = price
        
        # 清理过期数据
        if len(self.price_history[symbol]) > self.max_history_length:
            self._check_and_cleanup()
            
    def _cleanup_price_history(self) -> None:
        """清理价格历史数据"""
        for symbol in self.price_history:
            if len(self.price_history[symbol]) > self.cleanup_threshold:
                # 保留最近的数据
                self.price_history[symbol] = self.price_history[symbol][-self.cleanup_threshold:] 

    def set_compression_config(self, config: CompressionConfig) -> None:
        """设置数据压缩配置"""
        self.compression_config = config
        # 重置压缩状态
        self._compressed = {dt: False for dt in DataType}
        
    def get_compression_stats(self) -> Dict:
        """获取数据压缩统计信息"""
        return {
            'trades': {
                'original_count': len(self.trades),
                'compressed': self._compressed[DataType.TRADES]
            },
            'positions': {
                'original_count': len(self.positions_history),
                'compressed': self._compressed[DataType.POSITIONS]
            },
            'equity': {
                'original_count': len(self.equity_curve),
                'compressed': self._compressed[DataType.EQUITY]
            }
        } 