"""
数据源工厂
"""
from typing import Type, Dict, Optional, Any, List
from functools import lru_cache

from .data_source import DataSource
from .market_sources import (
    YahooFinanceSource,
    HKStockSource,
    ChinaStockSource
)
from .exceptions import MarketNotSupportedError
from .market_types import Exchange, ExchangeType

class DataSourceFactory:
    """数据源工厂类"""
    
    # 数据源映射
    _sources: Dict[str, Type[DataSource]] = {
        "yfinance": YahooFinanceSource,
        # 其他数据源待实现
    }
    
    # 实例缓存
    _instances: Dict[str, DataSource] = {}
    
    @classmethod
    def get_source_stats(cls) -> Dict[str, Any]:
        """获取数据源统计信息
        
        Returns:
            Dict[str, Any]: 包含数据源统计信息的字典
        """
        stats = {
            "total_sources": len(cls._sources),
            "active_instances": len(cls._instances),
            "sources": {},
            "exchanges": {}
        }
        
        # 统计数据源信息
        for name, source_class in cls._sources.items():
            stats["sources"][name] = {
                "class": source_class.__name__,
                "exchanges": []
            }
            
        # 统计交易所信息
        for exchange in ExchangeType:
            config = Exchange.get_config(exchange.value)
            source_name = config.get("data_source")
            
            if source_name in cls._sources:
                stats["exchanges"][exchange.value] = {
                    "data_source": source_name,
                    "status": "active" if exchange.value in cls._instances else "inactive"
                }
                stats["sources"][source_name]["exchanges"].append(exchange.value)
                
        return stats
        
    @classmethod
    def validate_source(cls, source_class: Type[DataSource]) -> bool:
        """验证数据源类是否实现了所有必要的方法
        
        Args:
            source_class: 数据源类
            
        Returns:
            bool: 是否通过验证
        """
        required_methods = [
            "get_stock_data",
            "get_stock_info",
            "validate_symbol",
            "normalize_symbol",
            "is_market_open",
            "get_trading_hours",
            "market_timezone"
        ]
        
        for method in required_methods:
            if not hasattr(source_class, method):
                return False
        return True
        
    @classmethod
    def register_source(cls, source_name: str, source_class: Type[DataSource]):
        """注册新的数据源
        
        Args:
            source_name: 数据源名称
            source_class: 数据源类
        """
        # 验证数据源类
        if not cls.validate_source(source_class):
            raise ValueError(f"数据源类 {source_class.__name__} 未实现所有必要的方法")
            
        cls._sources[source_name] = source_class
        # 清除实例缓存
        cls._instances.clear()
        # 清除 lru_cache
        cls.create_source.cache_clear()
        
    @classmethod
    def unregister_source(cls, source_name: str):
        """注销数据源
        
        Args:
            source_name: 数据源名称
        """
        if source_name in cls._sources:
            del cls._sources[source_name]
            # 清除实例缓存
            cls._instances.clear()
            # 清除 lru_cache
            cls.create_source.cache_clear()
            
    @classmethod
    @lru_cache(maxsize=None)
    def create_source(cls, exchange_code: str) -> Optional[DataSource]:
        """创建数据源实例（使用缓存）
        
        Args:
            exchange_code: 交易所代码
            
        Returns:
            Optional[DataSource]: 数据源实例
            
        Raises:
            MarketNotSupportedError: 当交易所不支持或数据源创建失败时
        """
        if exchange_code not in cls._instances:
            config = Exchange.get_config(exchange_code)
            source_name = config.get("data_source")
            
            if not source_name:
                raise MarketNotSupportedError(f"交易所 {exchange_code} 未配置数据源")
                
            if source_name not in cls._sources:
                raise MarketNotSupportedError(f"未实现的数据源: {source_name}")
                
            try:
                cls._instances[exchange_code] = cls._sources[source_name]()
            except Exception as e:
                raise MarketNotSupportedError(f"创建数据源实例失败: {str(e)}")
                
        return cls._instances[exchange_code]
        
    @classmethod
    def get_source_info(cls) -> Dict[str, list]:
        """获取数据源信息
        
        Returns:
            Dict[str, list]: 包含数据源信息的字典
        """
        info = {
            "registered_sources": list(cls._sources.keys()),
            "active_instances": list(cls._instances.keys()),
            "supported_exchanges": []
        }
        
        # 获取支持的交易所
        for exchange in ExchangeType:
            config = Exchange.get_config(exchange.value)
            if config.get("data_source") in cls._sources:
                info["supported_exchanges"].append(exchange.value)
                
        return info
        
    @classmethod
    def clear_cache(cls):
        """清除所有缓存"""
        cls._instances.clear()
        cls.create_source.cache_clear() 