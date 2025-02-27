"""
市场数据相关异常类定义
"""
from typing import Optional, Dict, Any

__all__ = [
    'MarketError',
    'MarketNotSupportedError',
    'SymbolNotFoundError',
    'DataValidationError',
    'MarketClosedError',
    'NetworkError',
    'CacheError',
    'RateLimitError',
    'AuthenticationError',
    'DataSourceError',
    'ConfigurationError'
]

class MarketError(Exception):
    """市场相关错误基类"""
    
    # 错误代码映射
    ERROR_CODES: Dict[str, Dict[str, Any]] = {
        "E001": {"name": "MARKET_NOT_SUPPORTED", "level": "ERROR"},
        "E002": {"name": "SYMBOL_NOT_FOUND", "level": "ERROR"},
        "E003": {"name": "DATA_VALIDATION", "level": "ERROR"},
        "E004": {"name": "MARKET_CLOSED", "level": "WARNING"},
        "E005": {"name": "NETWORK", "level": "ERROR"},
        "E006": {"name": "CACHE", "level": "WARNING"},
        "E007": {"name": "RATE_LIMIT", "level": "WARNING"},
        "E008": {"name": "AUTH", "level": "ERROR"},
        "E009": {"name": "DATA_SOURCE", "level": "ERROR"},
        "E010": {"name": "CONFIG", "level": "ERROR"}
    }
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.error_code = error_code
        self.message = message
        self.error_info = self.ERROR_CODES.get(error_code, {}) if error_code else {}
        
        error_msg = f"[{error_code}] {message}" if error_code else message
        if self.error_info:
            error_msg = f"{error_msg} ({self.error_info['name']})"
            
        super().__init__(error_msg)
        
    @property
    def is_critical(self) -> bool:
        """是否为严重错误"""
        return self.error_info.get("level") == "ERROR"

class MarketNotSupportedError(MarketError):
    """市场不支持错误"""
    def __init__(self, message: str):
        super().__init__(message, "E001")

class SymbolNotFoundError(MarketError):
    """股票代码不存在错误"""
    def __init__(self, message: str):
        super().__init__(message, "E002")

class DataValidationError(MarketError):
    """数据验证错误"""
    def __init__(self, message: str):
        super().__init__(message, "E003")

class MarketClosedError(MarketError):
    """市场休市错误"""
    def __init__(self, message: str):
        super().__init__(message, "E004")

class NetworkError(MarketError):
    """网络请求错误"""
    def __init__(self, message: str):
        super().__init__(message, "E005")

class CacheError(MarketError):
    """缓存操作错误"""
    def __init__(self, message: str):
        super().__init__(message, "E006")

class RateLimitError(MarketError):
    """接口调用频率限制错误"""
    def __init__(self, message: str):
        super().__init__(message, "E007")

class AuthenticationError(MarketError):
    """认证错误"""
    def __init__(self, message: str):
        super().__init__(message, "E008")

class DataSourceError(MarketError):
    """数据源错误"""
    def __init__(self, message: str):
        super().__init__(message, "E009")

class ConfigurationError(MarketError):
    """配置错误"""
    def __init__(self, message: str):
        super().__init__(message, "E010")

"""
自定义异常类
"""

class StrategyError(Exception):
    """策略错误"""
    pass

class BacktestError(Exception):
    """回测错误"""
    pass

class PortfolioError(Exception):
    """投资组合错误"""
    pass

class RiskManagementError(Exception):
    """风险管理错误"""
    pass 