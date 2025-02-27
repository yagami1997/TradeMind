# 标准库
import logging
import shutil
from datetime import datetime, date
from pathlib import Path
import pickle
from typing import Optional, Dict, Any, List

# 第三方库
import pandas as pd

# 本地导入
from .market_types import Exchange
from .exceptions import MarketError, MarketNotSupportedError, DataValidationError
from .config import Config
from .data_source_factory import DataSourceFactory
from .market_calendar import MarketCalendar

logger = logging.getLogger(__name__)

class DataManager:
    """数据管理器，负责管理市场数据的获取和缓存"""
    
    def __init__(self, cache_dir: Optional[str] = None, cache_expire_days: Optional[int] = None):
        """
        初始化数据管理器
        
        Args:
            cache_dir: 缓存目录路径，默认为 Config.CACHE_DIR
            cache_expire_days: 缓存过期天数，默认为 Config.CACHE_EXPIRE_DAYS
        """
        self.config = Config()
        self.cache_dir = Path(cache_dir or self.config.CACHE_DIR)
        self.cache_expire_days = cache_expire_days or self.config.CACHE_EXPIRE_DAYS
        self.setup_logging()
        self.setup_cache_dir()
        
        # 初始化数据源
        self.sources = {}
        for exchange in Exchange.CONFIGS:
            try:
                self.sources[exchange] = DataSourceFactory.create_source(exchange)
            except MarketNotSupportedError:
                continue
                
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
            # 为每个交易所创建子目录
            for exchange in Exchange.CONFIGS:
                (self.cache_dir / exchange.lower()).mkdir(exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建缓存目录失败: {e}")
            
    def get_stock_data(self,
                      symbol: str,
                      exchange: str,
                      start_date: Optional[str | date] = None,
                      end_date: Optional[str | date] = None,
                      interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所代码
            start_date: 开始日期，默认为前30天
            end_date: 结束日期，默认为今天
            interval: 数据间隔，默认为日线 "1d"
            
        Returns:
            DataFrame 包含股票数据，如果获取失败则返回 None
        """
        try:
            # 验证交易所是否支持
            if not Exchange.is_supported(exchange):
                raise MarketNotSupportedError(f"不支持的交易所: {exchange}")
                
            # 获取数据源
            source = self.sources[exchange]
            
            # 获取数据
            data = source.get_stock_data(symbol, start_date, end_date, interval)
            if data is None:
                self.logger.error(f"获取股票数据失败: {symbol}")
                return None
                
            # 缓存数据
            self._save_to_cache(symbol, exchange, data)
            return data
            
        except Exception as e:
            self.logger.error(f"获取股票数据时发生错误: {str(e)}")
            return None
            
    def get_multiple_stock_data(self,
                              symbols: List[str],
                              exchange: str,
                              start_date: Optional[str | date] = None,
                              end_date: Optional[str | date] = None,
                              interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        批量获取多个股票的数据
        
        Args:
            symbols: 股票代码列表
            exchange: 交易所代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 数据间隔
            
        Returns:
            字典，key为股票代码，value为对应的DataFrame数据
        """
        results = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol, exchange, start_date, end_date, interval)
            if data is not None:
                results[symbol] = data
        return results
        
    def get_stock_info(self, symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """获取指定交易所的股票信息"""
        try:
            if exchange not in self.sources:
                raise MarketNotSupportedError(f"暂时不支持的交易所: {exchange}")
                
            source = self.sources[exchange]
            return source.get_stock_info(symbol)
            
        except MarketError as e:
            self.logger.error(str(e))
            return None
        except Exception as e:
            self.logger.error(f"获取股票信息时出错: {e}")
            return None
            
    def is_market_open(self, exchange: str) -> bool:
        """检查指定交易所是否开市"""
        try:
            # 首先检查是否为交易日
            if not MarketCalendar.is_trading_day(exchange):
                return False
                
            # 获取当前交易时间
            trading_hours = MarketCalendar.get_trading_hours(exchange)
            now = datetime.now(trading_hours["regular"]["start"].tzinfo)
            
            # 检查是否在交易时间内
            regular_hours = trading_hours.get("regular", {})
            if regular_hours:
                return regular_hours["start"] <= now <= regular_hours["end"]
                
            return False
            
        except Exception as e:
            self.logger.error(f"检查市场状态时发生错误: {str(e)}")
            return False
            
    def get_trading_hours(self, exchange: str) -> Optional[Dict]:
        """获取指定交易所的交易时间"""
        try:
            return MarketCalendar.get_trading_hours(exchange)
        except Exception as e:
            self.logger.error(f"获取交易时间时发生错误: {str(e)}")
            return None
            
    def clear_cache(self, exchange: Optional[str] = None):
        """清理缓存数据
        
        Args:
            exchange: 可选，指定要清理的交易所缓存，如果不指定则清理所有缓存
        """
        try:
            if exchange:
                cache_dir = self.cache_dir / exchange.lower()
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    self.setup_cache_dir()
            else:
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.setup_cache_dir()
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
            
    def get_next_trading_day(self, exchange: str, from_date: Optional[date] = None) -> Optional[date]:
        """获取下一个交易日"""
        return MarketCalendar.get_next_trading_day(exchange, from_date)
        
    def get_previous_trading_day(self, exchange: str, from_date: Optional[date] = None) -> Optional[date]:
        """获取上一个交易日"""
        return MarketCalendar.get_previous_trading_day(exchange, from_date)
        
    def get_trading_days(self, 
                        exchange: str,
                        start_date: date,
                        end_date: date) -> List[date]:
        """获取交易日列表"""
        return MarketCalendar.get_trading_days(exchange, start_date, end_date)
            
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
            
    def _get_cache_path(self, symbol: str, exchange: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / exchange.lower() / f"{symbol}_data.pkl"
        
    def _get_from_cache(self, symbol: str, exchange: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所代码
            
        Returns:
            Optional[pd.DataFrame]: 缓存的数据，如果不存在或已过期则返回 None
        """
        cache_path = self._get_cache_path(symbol, exchange)
        
        try:
            if not cache_path.exists():
                return None
                
            # 检查缓存是否过期
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if (datetime.now() - cache_time).days >= self.cache_expire_days:
                self.logger.info(f"缓存已过期: {exchange}:{symbol}")
                return None
                
            # 读取缓存
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
                
            # 验证缓存格式
            if not isinstance(cache_data, dict) or "data" not in cache_data:
                self.logger.warning(f"缓存格式无效: {exchange}:{symbol}")
                return None
                
            # 记录缓存命中
            metadata = cache_data.get("metadata", {})
            self.logger.debug(
                f"缓存命中: {exchange}:{symbol}, "
                f"上次更新: {metadata.get('last_update')}, "
                f"数据范围: {metadata.get('start_date')} - {metadata.get('end_date')}"
            )
            
            return cache_data["data"]
            
        except Exception as e:
            self.logger.error(f"读取缓存时出错: {e}")
            return None
            
    def _save_to_cache(self, symbol: str, exchange: str, data: pd.DataFrame) -> bool:
        """保存数据到缓存
        
        Args:
            symbol: 股票代码
            exchange: 交易所代码
            data: 股票数据
            
        Returns:
            bool: 是否保存成功
        """
        cache_path = self._get_cache_path(symbol, exchange)
        
        try:
            # 创建缓存元数据
            metadata = {
                "symbol": symbol,
                "exchange": exchange,
                "last_update": datetime.now().isoformat(),
                "rows": len(data),
                "columns": list(data.columns),
                "start_date": data.index[0].isoformat() if not data.empty else None,
                "end_date": data.index[-1].isoformat() if not data.empty else None
            }
            
            # 保存数据和元数据
            cache_data = {
                "metadata": metadata,
                "data": data
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
            
        except Exception as e:
            self.logger.error(f"保存缓存时出错: {e}")
            return False
