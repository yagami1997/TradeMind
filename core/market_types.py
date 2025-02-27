"""
市场类型定义
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import time

class MarketType(Enum):
    """市场类型"""
    STOCK = "STOCK"          # 股票
    CRYPTO = "CRYPTO"        # 加密货币
    FOREX = "FOREX"          # 外汇（预留）
    FUTURES = "FUTURES"      # 期货（预留）

class ExchangeType(Enum):
    """交易所类型"""
    # 美洲
    NYSE = "NYSE"           # 纽约证券交易所
    NASDAQ = "NASDAQ"       # 纳斯达克
    
    # 亚洲
    HKEx = "HKEx"          # 香港交易所
    SSE = "SSE"            # 上海证券交易所
    SZSE = "SZSE"          # 深圳证券交易所
    JPX = "JPX"            # 日本交易所集团
    SGX = "SGX"            # 新加坡交易所
    
    # 欧洲
    LSE = "LSE"            # 伦敦证券交易所
    
    # 加密货币
    BINANCE = "BINANCE"    # 币安

class Exchange:
    """交易所配置管理"""
    
    CONFIGS: Dict[str, Dict[str, Any]] = {
        ExchangeType.NYSE.value: {
            "name": "New York Stock Exchange",
            "timezone": "America/New_York",
            "trading_hours": {
                "pre_market": {"start": "04:00", "end": "09:30"},
                "regular": {"start": "09:30", "end": "16:00"},
                "post_market": {"start": "16:00", "end": "20:00"}
            },
            "market_type": MarketType.STOCK.value,
            "symbol_pattern": r"^[A-Z]{1,5}$",
            "data_source": "yfinance",
            "currency": "USD",
            "holidays": [],  # 需要实现假期日历
            "supported_intervals": ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
        },
        ExchangeType.HKEx.value: {
            "name": "Hong Kong Stock Exchange",
            "timezone": "Asia/Hong_Kong",
            "trading_hours": {
                "pre_market": {"start": "09:00", "end": "09:30"},
                "regular": {"start": "09:30", "end": "16:00"},
                "post_market": None
            },
            "market_type": MarketType.STOCK.value,
            "symbol_pattern": r"^\d{4}$",
            "data_source": None,  # 待实现
            "currency": "HKD",
            "holidays": [],
            "supported_intervals": ["1d", "1wk", "1mo"]
        },
        ExchangeType.SSE.value: {
            "name": "Shanghai Stock Exchange",
            "timezone": "Asia/Shanghai",
            "trading_hours": {
                "morning": {"start": "09:30", "end": "11:30"},
                "afternoon": {"start": "13:00", "end": "15:00"}
            },
            "market_type": MarketType.STOCK.value,
            "symbol_pattern": r"^6\d{5}$",
            "data_source": None,  # 待实现
            "currency": "CNY",
            "holidays": [],
            "supported_intervals": ["1d", "1wk", "1mo"]
        },
        ExchangeType.SZSE.value: {
            "name": "Shenzhen Stock Exchange",
            "timezone": "Asia/Shanghai",
            "trading_hours": {
                "morning": {"start": "09:30", "end": "11:30"},
                "afternoon": {"start": "13:00", "end": "15:00"}
            },
            "market_type": MarketType.STOCK.value,
            "symbol_pattern": r"^[03]\d{5}$",
            "data_source": None,  # 待实现
            "currency": "CNY",
            "holidays": [],
            "supported_intervals": ["1d", "1wk", "1mo"]
        },
        ExchangeType.JPX.value: {
            "name": "Japan Exchange Group",
            "timezone": "Asia/Tokyo",
            "trading_hours": {
                "morning": {"start": "09:00", "end": "11:30"},
                "afternoon": {"start": "12:30", "end": "15:10"}
            },
            "market_type": MarketType.STOCK.value,
            "symbol_pattern": r"^\d{4}\.T$",
            "data_source": "yfinance",
            "currency": "JPY",
            "holidays": [],
            "supported_intervals": ["1d", "1wk", "1mo"]
        },
        ExchangeType.LSE.value: {
            "name": "London Stock Exchange",
            "timezone": "Europe/London",
            "trading_hours": {
                "regular": {"start": "08:00", "end": "16:30"}
            },
            "market_type": MarketType.STOCK.value,
            "symbol_pattern": r"^[A-Z]+\.L$",
            "data_source": "yfinance",
            "currency": "GBP",
            "holidays": [],
            "supported_intervals": ["1d", "1wk", "1mo"]
        },
        ExchangeType.BINANCE.value: {
            "name": "Binance",
            "timezone": "UTC",
            "trading_hours": {
                "regular": {"start": "00:00", "end": "23:59"}
            },
            "market_type": MarketType.CRYPTO.value,
            "symbol_pattern": r"^[A-Z]+USDT$",
            "data_source": None,  # 待实现
            "currency": "USDT",
            "holidays": [],
            "supported_intervals": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
        }
    }
    
    @classmethod
    def get_config(cls, exchange_code: str) -> Dict[str, Any]:
        """获取交易所配置"""
        return cls.CONFIGS.get(exchange_code, {})
    
    @classmethod
    def is_supported(cls, exchange_code: str) -> bool:
        """检查交易所是否支持"""
        return exchange_code in cls.CONFIGS
    
    @classmethod
    def get_supported_exchanges(cls, market_type: Optional[str] = None) -> List[str]:
        """获取支持的交易所列表"""
        if market_type:
            return [code for code, config in cls.CONFIGS.items() 
                   if config["market_type"] == market_type]
        return list(cls.CONFIGS.keys()) 