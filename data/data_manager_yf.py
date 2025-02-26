import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import configparser
import os

class YahooFinanceManager:
    """Yahoo Finance数据管理类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        
    def _load_config(self) -> configparser.ConfigParser:
        """加载配置文件"""
        config = configparser.ConfigParser()
        config_path = os.path.join('config', 'config.ini')
        config.read(config_path)
        return config
        
    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """
        获取单个股票的历史数据
        
        Args:
            symbol (str): 股票代码
            
        Returns:
            pd.DataFrame: 包含OHLCV数据的DataFrame
        """
        try:
            # 从配置文件获取参数
            period = self.config['data_source']['yahoo_period']
            interval = self.config['data_source']['yahoo_interval']
            
            # 获取数据
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                self.logger.error(f"{symbol}: 未找到数据")
                return None
                
            # 添加技术指标所需的列名
            df.columns = [col.lower() for col in df.columns]
            
            self.logger.info(f"{symbol}: 成功获取数据, 共{len(df)}条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"{symbol}: 获取数据失败 - {str(e)}")
            return None
            
    def get_multiple_stocks_data(self, symbols: list) -> dict:
        """
        批量获取多个股票的历史数据
        
        Args:
            symbols (list): 股票代码列表
            
        Returns:
            dict: 股票代码到DataFrame的映射
        """
        data_dict = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data is not None:
                data_dict[symbol] = data
        return data_dict
        
    def get_stock_info(self, symbol: str) -> dict:
        """
        获取股票的基本信息
        
        Args:
            symbol (str): 股票代码
            
        Returns:
            dict: 股票信息字典
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return info
        except Exception as e:
            self.logger.error(f"{symbol}: 获取信息失败 - {str(e)}")
            return None