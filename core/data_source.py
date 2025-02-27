"""
数据源抽象基类定义
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
import pandas as pd

from .exceptions import DataValidationError
from .config import Config

class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self):
        self.config = Config()
    
    @abstractmethod
    def get_stock_data(self, 
                      symbol: str,
                      start_date: Optional[str | date] = None,
                      end_date: Optional[str | date] = None,
                      interval: str = "1d") -> Optional[pd.DataFrame]:
        """获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 数据间隔 (1m/5m/15m/30m/1h/1d/1wk/1mo)
        """
        pass
        
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票信息"""
        pass
        
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """验证股票代码格式"""
        pass
        
    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码格式"""
        pass
        
    @abstractmethod
    def is_market_open(self) -> bool:
        """检查市场是否开市"""
        pass
        
    @abstractmethod
    def get_trading_hours(self) -> Dict[str, Dict[str, str]]:
        """获取交易时间"""
        pass
        
    @property
    @abstractmethod
    def market_timezone(self) -> str:
        """获取市场时区"""
        pass

    def get_multiple_stock_data(self,
                              symbols: List[str],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              interval: str = "1d") -> Dict[str, Optional[pd.DataFrame]]:
        """批量获取多个股票数据"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_stock_data(
                    symbol, 
                    start_date, 
                    end_date,
                    interval
                )
            except Exception as e:
                results[symbol] = None
        return results

    def get_realtime_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """获取实时价格（默认实现）"""
        try:
            df = self.get_stock_data(symbol, interval="1m")
            if df is not None and not df.empty:
                last_row = df.iloc[-1]
                return {
                    "symbol": symbol,
                    "timestamp": last_row.name.isoformat(),
                    "open": float(last_row["open"]),
                    "high": float(last_row["high"]),
                    "low": float(last_row["low"]),
                    "close": float(last_row["close"]),
                    "volume": float(last_row["volume"])
                }
        except Exception:
            pass
        return None

    def get_market_status(self) -> Dict[str, Any]:
        """获取市场状态（默认实现）"""
        is_open = self.is_market_open()
        trading_hours = self.get_trading_hours()
        
        return {
            "is_open": is_open,
            "trading_hours": trading_hours,
            "current_period": self._get_current_trading_period()
        }

    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据质量"""
        if data is None or data.empty:
            return False
            
        required_columns = self.config.REQUIRED_COLUMNS
        
        # 检查必要列是否存在
        if not all(col in data.columns for col in required_columns):
            raise DataValidationError(f"数据缺少必要列: {required_columns}")
            
        # 检查是否有异常值
        for col in required_columns:
            if (data[col] <= 0).any():
                raise DataValidationError(f"列 {col} 包含异常值(<=0)")
            
        return True

    def _get_current_trading_period(self) -> Optional[str]:
        """获取当前交易时段"""
        if not self.is_market_open():
            return None
            
        hours = self.get_trading_hours()
        now = datetime.now()
        current_time = now.time()
        
        for period, times in hours.items():
            start = datetime.strptime(times["start"], "%H:%M").time()
            end = datetime.strptime(times["end"], "%H:%M").time()
            if start <= current_time <= end:
                return period
                
        return None 