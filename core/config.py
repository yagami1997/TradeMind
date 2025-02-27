"""
全局配置管理
"""
from typing import Dict, Any
from pathlib import Path

class Config:
    """全局配置类"""
    
    # 基础配置
    BASE_DIR = Path(__file__).parent.parent
    CACHE_DIR = BASE_DIR / "data/cache"
    CACHE_EXPIRE_DAYS = 1
    
    # 网络请求配置
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # 秒
    REQUEST_TIMEOUT = 10  # 秒
    
    # 数据验证配置
    REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'volume']
    
    # 市场配置
    MARKET_CONFIG = {
        "US": {
            "timezone": "America/New_York",
            "trading_hours": {"start": "09:30", "end": "16:00"},
            "holidays": [],  # TODO: 添加假期列表
            "data_source": "yfinance"
        },
        "HK": {
            "timezone": "Asia/Hong_Kong",
            "trading_hours": {"start": "09:30", "end": "16:00"},
            "holidays": [],  # TODO: 待实现
            "data_source": None  # TODO: 待定
        },
        "CN": {
            "timezone": "Asia/Shanghai",
            "trading_hours": {"start": "09:30", "end": "15:00"},
            "holidays": [],  # TODO: 待实现
            "data_source": None  # TODO: 待定
        }
    }
    
    @classmethod
    def get_market_config(cls, market: str) -> Dict[str, Any]:
        """获取指定市场的配置"""
        return cls.MARKET_CONFIG.get(market, {}) 