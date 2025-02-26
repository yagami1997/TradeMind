from ib_insync import *
import pandas as pd
import logging
import configparser
import os
from datetime import datetime, timedelta

class IBKRManager:
    """IBKR数据管理类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.ib = IB()
        self._connect()
        
    def _load_config(self) -> configparser.ConfigParser:
        """加载配置文件"""
        config = configparser.ConfigParser()
        config_path = os.path.join('config', 'config.ini')
        config.read(config_path)
        return config
        
    def _connect(self):
        """连接到IBKR"""
        try:
            host = self.config['data_source']['ibkr_host']
            port = self.config['data_source'].getint('ibkr_port')
            client_id = self.config['data_source'].getint('ibkr_client_id')
            
            self.ib.connect(host, port, clientId=client_id)
            self.logger.info("成功连接到IBKR")
            
        except Exception as e:
            self.logger.error(f"IBKR连接失败: {str(e)}")
            raise
            
    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """
        获取股票实时数据
        
        Args:
            symbol (str): 股票代码
            
        Returns:
            pd.DataFrame: 包含实时数据的DataFrame
        """
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # 获取实时数据
            ticker = self.ib.reqMktData(contract)
            self.ib.sleep(2)  # 等待数据
            
            # 构建DataFrame
            data = {
                'last': ticker.last,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'volume': ticker.volume,
                'timestamp': datetime.now()
            }
            
            return pd.DataFrame([data])
            
        except Exception as e:
            self.logger.error(f"{symbol}: 获取数据失败 - {str(e)}")
            return None
            
    def __del__(self):
        """析构函数，确保断开连接"""
        if self.ib.isConnected():
            self.ib.disconnect()