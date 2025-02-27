"""
市场类型定义
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import time
import re

class MarketType(Enum):
    """市场类型"""
    STOCK = "STOCK"          # 股票
    CRYPTO = "CRYPTO"        # 加密货币
    FOREX = "FOREX"          # 外汇
    FUTURES = "FUTURES"      # 期货
    BONDS = "BONDS"          # 债券
    OPTIONS = "OPTIONS"      # 期权
    ETF = "ETF"             # ETF基金
    INDEX = "INDEX"         # 指数

class ExchangeType(Enum):
    """交易所类型"""
    # 美洲
    NYSE = "NYSE"           # 纽约证券交易所
    NASDAQ = "NASDAQ"       # 纳斯达克
    TSX = "TSX"            # 多伦多证券交易所
    
    # 亚洲
    HKEx = "HKEx"          # 香港交易所
    SSE = "SSE"            # 上海证券交易所
    SZSE = "SZSE"          # 深圳证券交易所
    JPX = "JPX"            # 日本交易所集团
    SGX = "SGX"            # 新加坡交易所
    KRX = "KRX"            # 韩国交易所
    
    # 欧洲
    LSE = "LSE"            # 伦敦证券交易所
    XETRA = "XETRA"        # 德国证券交易所
    EURONEXT = "EURONEXT"  # 泛欧交易所
    
    # 加密货币
    BINANCE = "BINANCE"    # 币安
    COINBASE = "COINBASE"  # 比特币基地

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
            "supported_intervals": ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"],
            "min_order_size": 1,
            "price_decimals": 2,
            "volume_decimals": 0,
            "fees": {
                "maker": 0.0,
                "taker": 0.0
            }
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
    
    @classmethod
    def validate_symbol(cls, symbol: str, exchange_code: str) -> bool:
        """验证股票代码格式
        
        Args:
            symbol: 股票代码
            exchange_code: 交易所代码
            
        Returns:
            bool: 是否符合格式要求
        """
        config = cls.get_config(exchange_code)
        if not config:
            return False
            
        pattern = config.get("symbol_pattern")
        if not pattern:
            return True
            
        return bool(re.match(pattern, symbol))
    
    @classmethod
    def get_exchange_info(cls, exchange_code: str) -> Dict[str, Any]:
        """获取交易所详细信息
        
        Args:
            exchange_code: 交易所代码
            
        Returns:
            Dict[str, Any]: 交易所信息
        """
        config = cls.get_config(exchange_code)
        if not config:
            return {}
            
        return {
            "code": exchange_code,
            "name": config["name"],
            "timezone": config["timezone"],
            "market_type": config["market_type"],
            "currency": config["currency"],
            "trading_hours": config["trading_hours"],
            "supported_intervals": config.get("supported_intervals", []),
            "min_order_size": config.get("min_order_size"),
            "price_decimals": config.get("price_decimals"),
            "volume_decimals": config.get("volume_decimals"),
            "fees": config.get("fees", {}),
            "data_source": config.get("data_source")
        } 