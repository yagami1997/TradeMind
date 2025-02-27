# 标准库
import logging
import shutil
from datetime import datetime
from pathlib import Path
import pickle
from typing import Optional, Dict, Any, List

# 第三方库
import pandas as pd

# 本地导入
from .market_sources import YahooFinanceSource, HKStockSource, ChinaStockSource
from .exceptions import MarketError, MarketNotSupportedError
from .config import Config

class Market:
    US = "US"
    HK = "HK"
    CN = "CN"

class DataManager:
    """数据管理器：负责数据的获取、缓存和预处理
    
    支持多个市场：
    - 美股 (US)
    - 港股 (HK)
    - A股 (CN)
    """
    
    # 市场数据源映射
    MARKET_SOURCES = {
        Market.US: YahooFinanceSource,
        Market.HK: HKStockSource,
        Market.CN: ChinaStockSource
    }
    
    def __init__(self, cache_dir: Optional[str] = None, cache_expire_days: Optional[int] = None):
        self.config = Config()
        self.cache_dir = Path(cache_dir or self.config.CACHE_DIR)
        self.cache_expire_days = cache_expire_days or self.config.CACHE_EXPIRE_DAYS
        self.setup_logging()
        self.setup_cache_dir()
        
        # 初始化各市场数据源
        self.sources = {
            market: source_class() 
            for market, source_class in self.MARKET_SOURCES.items()
        }
        
    def setup_logging(self):
        """配置日志"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
    def setup_cache_dir(self):
        """创建缓存目录"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            # 为每个市场创建子目录
            for market in self.MARKET_SOURCES.keys():
                (self.cache_dir / market.lower()).mkdir(exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建缓存目录失败: {e}")
            
    def get_stock_data(self, 
                      symbol: str,
                      market: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取指定市场的股票数据
        
        Args:
            symbol: 股票代码
            market: 市场代码 (US/HK/CN)
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            if market not in self.sources:
                raise MarketNotSupportedError(f"暂时不支持的市场: {market}")
                
            source = self.sources[market]
            
            # 验证股票代码格式
            if not source.validate_symbol(symbol):
                self.logger.error(f"无效的股票代码格式: {symbol}")
                return None
                
            # 验证日期格式
            if not self._validate_dates(start_date, end_date):
                self.logger.error("无效的日期格式或范围")
                return None
                
            # 检查缓存
            cached_data = self._get_from_cache(symbol, market)
            if cached_data is not None:
                self.logger.info(f"从缓存获取数据: {market}:{symbol}")
                return cached_data
                
            # 从数据源获取数据
            self.logger.info(f"从{market}数据源获取数据: {symbol}")
            data = source.get_stock_data(symbol, start_date, end_date)
            
            if data is not None and not data.empty:
                # 缓存数据
                self._save_to_cache(symbol, market, data)
                return data
            else:
                self.logger.warning(f"获取数据失败: {market}:{symbol}")
                return None
                
        except MarketError as e:
            self.logger.error(str(e))
            return None
        except Exception as e:
            self.logger.error(f"获取股票数据时出错: {e}")
            return None
            
    def get_multiple_stock_data(self,
                              symbols: List[str],
                              market: str,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict[str, Optional[pd.DataFrame]]:
        """批量获取多个股票数据"""
        if market not in self.sources:
            raise MarketNotSupportedError(f"暂时不支持的市场: {market}")
            
        source = self.sources[market]
        return source.get_multiple_stock_data(symbols, start_date, end_date)
            
    def get_stock_info(self, symbol: str, market: str) -> Optional[Dict[str, Any]]:
        """获取指定市场的股票信息"""
        try:
            if market not in self.sources:
                raise MarketNotSupportedError(f"暂时不支持的市场: {market}")
                
            source = self.sources[market]
            return source.get_stock_info(symbol)
            
        except MarketError as e:
            self.logger.error(str(e))
            return None
        except Exception as e:
            self.logger.error(f"获取股票信息时出错: {e}")
            return None
            
    def is_market_open(self, market: str) -> bool:
        """检查指定市场是否开市"""
        if market not in self.sources:
            return False
            
        source = self.sources[market]
        return source.is_market_open()
            
    def get_trading_hours(self, market: str) -> Optional[Dict[str, str]]:
        """获取指定市场的交易时间"""
        if market not in self.sources:
            return None
            
        source = self.sources[market]
        return source.get_trading_hours()
            
    def clear_cache(self, market: Optional[str] = None):
        """清理缓存数据
        
        Args:
            market: 可选，指定要清理的市场缓存，如果不指定则清理所有缓存
        """
        try:
            if market:
                cache_dir = self.cache_dir / market.lower()
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    self.setup_cache_dir()
            else:
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.setup_cache_dir()
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
            
    def _validate_dates(self, start_date: Optional[str], end_date: Optional[str]) -> bool:
        """验证日期格式和范围"""
        if not start_date and not end_date:
            return True
            
        try:
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                
            if start_date and end_date:
                return start <= end and end <= datetime.now()
            return True
            
        except ValueError:
            return False
            
    def _get_cache_path(self, symbol: str, market: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / market.lower() / f"{symbol}_data.pkl"
        
    def _get_from_cache(self, symbol: str, market: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据"""
        cache_path = self._get_cache_path(symbol, market)
        
        try:
            if not cache_path.exists():
                return None
                
            # 检查缓存是否过期
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if (datetime.now() - cache_time).days >= self.cache_expire_days:
                self.logger.info(f"缓存已过期: {market}:{symbol}")
                return None
                
            # 读取缓存
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                
            return data
            
        except Exception as e:
            self.logger.error(f"读取缓存时出错: {e}")
            return None
            
    def _save_to_cache(self, symbol: str, market: str, data: pd.DataFrame) -> bool:
        """保存数据到缓存"""
        cache_path = self._get_cache_path(symbol, market)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            return True
            
        except Exception as e:
            self.logger.error(f"保存缓存时出错: {e}")
            return False
