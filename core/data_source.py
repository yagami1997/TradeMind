from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd

from .exceptions import MarketError
from .config import Config

class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self):
        self.config = Config()
    
    @abstractmethod
    def get_stock_data(self, 
                       symbol: str,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取股票数据"""
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
    def get_trading_hours(self) -> Dict[str, str]:
        """获取交易时间"""
        pass
        
    @property
    @abstractmethod
    def market_timezone(self) -> str:
        """获取市场时区"""
        pass
        
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据质量
        
        检查:
        1. 数据是否为空
        2. 必要列是否存在
        3. 数据是否有异常值
        """
        if data is None or data.empty:
            return False
            
        # 检查必要列是否存在
        if not all(col in data.columns for col in self.config.REQUIRED_COLUMNS):
            return False
            
        # 检查是否有异常值（如负数）
        if (data[self.config.REQUIRED_COLUMNS] <= 0).any().any():
            return False
            
        return True
        
    def get_multiple_stock_data(self,
                              symbols: List[str],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict[str, Optional[pd.DataFrame]]:
        """批量获取多个股票数据"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_stock_data(symbol, start_date, end_date)
            except MarketError as e:
                results[symbol] = None
        return results 