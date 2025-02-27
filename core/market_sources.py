import re
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import pytz
import pandas as pd
import yfinance as yf
from requests.exceptions import RequestException
from pandas.errors import EmptyDataError
import logging

from .data_source import DataSource
from .exceptions import (
    DataSourceError,
    NetworkError,
    DataValidationError,
    SymbolNotFoundError,
    RateLimitError,
    MarketNotSupportedError
)
from .config import Config as GlobalConfig
from .market_types import Exchange

logger = logging.getLogger(__name__)

class YahooFinanceSource(DataSource):
    """Yahoo Finance数据源"""
    
    def __init__(self):
        """初始化Yahoo Finance数据源"""
        super().__init__()
        self._session = None
        self._init_session()
        self._tz = pytz.timezone(self.market_timezone)
        self.config = GlobalConfig()
        
    def _init_session(self):
        """初始化会话"""
        try:
            self._session = yf.Tickers("")
        except Exception as e:
            logger.error(f"初始化Yahoo Finance会话失败: {e}")
            raise DataSourceError("初始化数据源失败")
            
    def get_stock_data(self, 
                      symbol: str,
                      start_date: Optional[str | date] = None,
                      end_date: Optional[str | date] = None,
                      interval: str = "1d") -> Optional[pd.DataFrame]:
        """获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 数据间隔
            
        Returns:
            DataFrame或None
            
        Raises:
            NetworkError: 网络请求错误
            DataValidationError: 数据验证错误
            SymbolNotFoundError: 股票代码不存在
            RateLimitError: 接口调用频率限制
        """
        try:
            # 标准化股票代码
            symbol = self.normalize_symbol(symbol)
            
            # 获取数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            # 验证数据
            if df.empty:
                raise SymbolNotFoundError(f"未找到股票数据: {symbol}")
                
            # 处理数据
            df.index.name = 'date'
            df.columns = df.columns.str.lower()
            
            # 验证数据质量
            self.validate_data(df)
            
            return df
            
        except RequestException as e:
            logger.error(f"网络请求错误: {e}")
            raise NetworkError(f"获取数据失败: {str(e)}")
        except EmptyDataError:
            logger.error(f"获取到空数据: {symbol}")
            raise DataValidationError(f"获取到空数据: {symbol}")
        except RateLimitError:
            logger.warning("达到API调用限制")
            raise
        except Exception as e:
            logger.error(f"获取股票数据时发生错误: {e}")
            raise DataSourceError(f"获取数据失败: {str(e)}")
            
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票信息"""
        try:
            symbol = self.normalize_symbol(symbol)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                raise SymbolNotFoundError(f"未找到股票信息: {symbol}")
                
            return info
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None
            
    def validate_symbol(self, symbol: str) -> bool:
        """验证股票代码格式"""
        try:
            ticker = yf.Ticker(symbol)
            return bool(ticker.info)
        except:
            return False
            
    def normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码格式"""
        # Yahoo Finance格式转换
        return symbol.upper().replace('_', '-')
        
    def is_market_open(self) -> bool:
        """检查市场是否开市"""
        # Yahoo Finance没有直接的API，使用美股时间
        try:
            nyse_config = Exchange.get_config('NYSE')
            if not nyse_config:
                return False
                
            now = datetime.now()
            trading_hours = nyse_config['trading_hours']['regular']
            
            start_time = datetime.strptime(trading_hours['start'], '%H:%M').time()
            end_time = datetime.strptime(trading_hours['end'], '%H:%M').time()
            
            return start_time <= now.time() <= end_time
            
        except Exception as e:
            logger.error(f"检查市场状态失败: {e}")
            return False
            
    def get_trading_hours(self) -> Dict[str, Dict[str, str]]:
        """获取交易时间"""
        # 返回美股交易时间
        return Exchange.get_config('NYSE')['trading_hours']
        
    @property
    def market_timezone(self) -> str:
        """获取市场时区"""
        return "America/New_York"

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