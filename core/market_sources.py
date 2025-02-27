import re
import time
from typing import Optional, Dict, Any
from datetime import datetime
import pytz
import pandas as pd
import yfinance as yf

from .data_source import DataSource
from .exceptions import *
from .config import Config as GlobalConfig

class YahooFinanceSource(DataSource):
    """美股数据源实现"""
    
    def __init__(self):
        super().__init__()
        self._tz = pytz.timezone(self.market_timezone)
        self.config = GlobalConfig()
        
    def get_stock_data(self, 
                      symbol: str, 
                      start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取股票数据，带重试机制"""
        normalized_symbol = self.normalize_symbol(symbol)
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                stock = yf.Ticker(normalized_symbol)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    raise SymbolNotFoundError(f"未找到股票数据: {symbol}")
                    
                if not self.validate_data(data):
                    raise MarketError(f"数据验证失败: {symbol}")
                    
                return data
                
            except Exception as e:
                if attempt == self.config.MAX_RETRIES - 1:
                    if isinstance(e, MarketError):
                        raise e
                    raise NetworkError(f"网络请求失败: {str(e)}")
                time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票信息，带重试机制"""
        normalized_symbol = self.normalize_symbol(symbol)
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                stock = yf.Ticker(normalized_symbol)
                info = stock.info
                
                return {
                    'symbol': symbol,
                    'name': info.get('longName', ''),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'market_cap': info.get('marketCap', 0),
                    'currency': info.get('currency', 'USD'),
                    'exchange': info.get('exchange', ''),
                    'country': info.get('country', 'US')
                }
                
            except Exception as e:
                if attempt == self.config.MAX_RETRIES - 1:
                    raise NetworkError(f"获取股票信息失败: {str(e)}")
                time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                
    def validate_symbol(self, symbol: str) -> bool:
        """验证美股代码格式"""
        pattern = r'^[A-Z]{1,5}$'
        return bool(re.match(pattern, symbol))
        
    def normalize_symbol(self, symbol: str) -> str:
        """标准化美股代码"""
        return symbol.upper()
        
    def is_market_open(self) -> bool:
        """检查美股市场是否开市"""
        now = datetime.now(self._tz)
        
        # 检查是否是周末
        if now.weekday() >= 5:
            return False
            
        # 获取交易时间
        hours = self.get_trading_hours()
        market_start = datetime.strptime(hours['start'], '%H:%M').time()
        market_end = datetime.strptime(hours['end'], '%H:%M').time()
        
        # 检查当前时间是否在交易时间内
        current_time = now.time()
        return market_start <= current_time <= market_end
        
    def get_trading_hours(self) -> Dict[str, str]:
        """获取美股交易时间"""
        return self.config.MARKET_CONFIG['US']['trading_hours']
        
    @property
    def market_timezone(self) -> str:
        """获取美股市场时区"""
        return self.config.MARKET_CONFIG['US']['timezone']

class HKStockSource(DataSource):
    """港股数据源实现"""
    
    def __init__(self):
        super().__init__()
        self._tz = pytz.timezone(self.market_timezone)
    
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        # TODO: 实现港股数据获取逻辑
        raise MarketNotSupportedError("港股数据源尚未实现")
        
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        # TODO: 实现港股信息获取逻辑
        raise MarketNotSupportedError("港股数据源尚未实现")
        
    def validate_symbol(self, symbol: str) -> bool:
        """验证港股代码格式"""
        pattern = r'^\d{4}$'
        return bool(re.match(pattern, symbol))
        
    def normalize_symbol(self, symbol: str) -> str:
        """标准化港股代码 (例如: 添加.HK后缀)"""
        symbol = symbol.zfill(4)  # 补足4位
        return f"{symbol}.HK"
        
    def is_market_open(self) -> bool:
        # TODO: 实现港股市场开市检查
        return False
        
    def get_trading_hours(self) -> Dict[str, str]:
        return self.config.MARKET_CONFIG['HK']['trading_hours']
        
    @property
    def market_timezone(self) -> str:
        return self.config.MARKET_CONFIG['HK']['timezone']

class ChinaStockSource(DataSource):
    """A股数据源实现"""
    
    def __init__(self):
        super().__init__()
        self._tz = pytz.timezone(self.market_timezone)
    
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        # TODO: 实现A股数据获取逻辑
        raise MarketNotSupportedError("A股数据源尚未实现")
        
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        # TODO: 实现A股信息获取逻辑
        raise MarketNotSupportedError("A股数据源尚未实现")
        
    def validate_symbol(self, symbol: str) -> bool:
        """验证A股代码格式"""
        pattern = r'^[36][0-9]{5}$'
        return bool(re.match(pattern, symbol))
        
    def normalize_symbol(self, symbol: str) -> str:
        """标准化A股代码"""
        if symbol.startswith('6'):
            return f"{symbol}.SH"  # 上海
        return f"{symbol}.SZ"  # 深圳
        
    def is_market_open(self) -> bool:
        # TODO: 实现A股市场开市检查
        return False
        
    def get_trading_hours(self) -> Dict[str, str]:
        return self.config.MARKET_CONFIG['CN']['trading_hours']
        
    @property
    def market_timezone(self) -> str:
        return self.config.MARKET_CONFIG['CN']['timezone'] 