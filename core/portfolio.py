"""Portfolio class for managing backtest portfolio."""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

class Portfolio:
    """
    投资组合类：管理回测期间的投资组合状态
    
    功能：
    1. 跟踪现金和持仓
    2. 记录交易历史
    3. 计算组合价值
    4. 生成权益曲线
    """
    
    def __init__(
        self, 
        initial_capital: float, 
        symbols: List[str],
        max_history_length: int = 10000,
        cleanup_threshold: int = 5000
    ):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
            symbols: 交易品种列表
            max_history_length: 最大历史记录长度
            cleanup_threshold: 清理阈值，达到此数量时触发清理
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.symbols = symbols
        self.max_history_length = max_history_length
        self.cleanup_threshold = cleanup_threshold
        
        # 持仓信息
        self.positions = {symbol: 0 for symbol in symbols}  # 持仓数量
        self.position_avg_price = {symbol: 0.0 for symbol in symbols}  # 持仓均价
        
        # 历史记录
        self.trades = []  # 交易记录
        self.positions_history = []  # 持仓历史
        self.equity_curve = []  # 权益曲线
        
        # 当前状态
        self.current_value = initial_capital
        self.high_value = initial_capital
        
        # 压缩标志
        self._compressed = False
        
        # 价格历史
        self.price_history = {}
        
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
            
    def compress_history(self) -> None:
        """压缩历史数据"""
        if self._compressed:
            return
            
        # 压缩交易记录
        if len(self.trades) > self.max_history_length:
            # 保留最近的交易记录
            recent_trades = self.trades[-self.max_history_length:]
            # 汇总早期交易
            early_trades_summary = {
                'date': self.trades[0]['date'],
                'type': 'summary',
                'count': len(self.trades) - len(recent_trades),
                'total_value': sum(t.get('value', 0) for t in self.trades[:-self.max_history_length])
            }
            self.trades = [early_trades_summary] + recent_trades
            
        # 压缩持仓历史
        if len(self.positions_history) > self.max_history_length:
            # 每日记录改为每周记录
            df = pd.DataFrame(self.positions_history)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            weekly_history = df.resample('W').last().dropna()
            self.positions_history = weekly_history.reset_index().to_dict('records')
            
        # 压缩权益曲线
        if len(self.equity_curve) > self.max_history_length:
            # 保持关键点：开始、结束、最高、最低点
            df = pd.DataFrame(self.equity_curve)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 获取关键点
            start_point = df.iloc[0]
            end_point = df.iloc[-1]
            high_point = df.loc[df['value'].idxmax()]
            low_point = df.loc[df['value'].idxmin()]
            
            # 重采样为日频率
            resampled = df.resample('D').last().dropna()
            
            # 合并关键点
            key_points = pd.concat([
                pd.DataFrame([start_point]),
                pd.DataFrame([high_point]),
                pd.DataFrame([low_point]),
                pd.DataFrame([end_point])
            ]).drop_duplicates()
            
            # 合并数据
            final_df = pd.concat([resampled, key_points]).sort_index()
            self.equity_curve = final_df.reset_index().to_dict('records')
            
        self._compressed = True
        
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
        
    def get_trades(self, compressed: bool = False) -> List[Dict]:
        """获取交易历史"""
        if compressed and not self._compressed:
            self.compress_history()
        return self.trades
        
    def get_positions_history(self, compressed: bool = False) -> List[Dict]:
        """获取持仓历史"""
        if compressed and not self._compressed:
            self.compress_history()
        return self.positions_history
        
    def get_equity_curve(self, compressed: bool = False) -> List[Dict]:
        """获取权益曲线"""
        if compressed and not self._compressed:
            self.compress_history()
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