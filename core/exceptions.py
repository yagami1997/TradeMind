"""
市场数据相关异常类定义
"""

class MarketError(Exception):
    """市场相关错误基类"""
    pass

class MarketNotSupportedError(MarketError):
    """市场不支持错误"""
    pass

class SymbolNotFoundError(MarketError):
    """股票代码不存在错误"""
    pass

class DataValidationError(MarketError):
    """数据验证错误"""
    pass

class MarketClosedError(MarketError):
    """市场休市错误"""
    pass

class NetworkError(MarketError):
    """网络请求错误"""
    pass

class CacheError(MarketError):
    """缓存操作错误"""
    pass 