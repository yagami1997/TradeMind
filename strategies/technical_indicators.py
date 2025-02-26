import pandas as pd
import numpy as np
import pandas_ta as ta
import logging
from typing import Union, Tuple

class TechnicalIndicators:
    """技术指标计算类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 添加了技术指标的DataFrame
        """
        try:
            # 确保列名小写
            df.columns = [col.lower() for col in df.columns]
            
            # 移动平均线
            df = self.calculate_ma(df)
            
            # MACD
            df = self.calculate_macd(df)
            
            # RSI
            df = self.calculate_rsi(df)
            
            # 布林带
            df = self.calculate_bollinger_bands(df)
            
            # KDJ
            df = self.calculate_kdj(df)
            
            # 成交量指标
            df = self.calculate_volume_indicators(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算技术指标时出错: {str(e)}")
            return df

    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均线"""
        try:
            # 简单移动平均线
            df['ma5'] = ta.sma(df['close'], length=5)
            df['ma10'] = ta.sma(df['close'], length=10)
            df['ma20'] = ta.sma(df['close'], length=20)
            df['ma60'] = ta.sma(df['close'], length=60)
            
            # 指数移动平均线
            df['ema12'] = ta.ema(df['close'], length=12)
            df['ema26'] = ta.ema(df['close'], length=26)
            
            return df
        except Exception as e:
            self.logger.error(f"计算MA指标时出错: {str(e)}")
            return df

    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        try:
            macd = ta.macd(df['close'])
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']
            return df
        except Exception as e:
            self.logger.error(f"计算MACD指标时出错: {str(e)}")
            return df

    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算RSI指标"""
        try:
            df['rsi'] = ta.rsi(df['close'], length=14)
            return df
        except Exception as e:
            self.logger.error(f"计算RSI指标时出错: {str(e)}")
            return df

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算布林带"""
        try:
            bollinger = ta.bbands(df['close'], length=20)
            df['bb_upper'] = bollinger['BBU_20_2.0']
            df['bb_middle'] = bollinger['BBM_20_2.0']
            df['bb_lower'] = bollinger['BBL_20_2.0']
            return df
        except Exception as e:
            self.logger.error(f"计算布林带时出错: {str(e)}")
            return df

    def calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ指标"""
        try:
            stoch = ta.stoch(df['high'], df['low'], df['close'])
            df['k'] = stoch['STOCHk_14_3_3']
            df['d'] = stoch['STOCHd_14_3_3']
            df['j'] = 3 * df['k'] - 2 * df['d']
            return df
        except Exception as e:
            self.logger.error(f"计算KDJ指标时出错: {str(e)}")
            return df

    def calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量相关指标"""
        try:
            # 成交量移动平均
            df['volume_ma5'] = ta.sma(df['volume'], length=5)
            df['volume_ma10'] = ta.sma(df['volume'], length=10)
            
            # 成交量变化率
            df['volume_change'] = df['volume'].pct_change()
            
            # 价格成交量趋势指标
            df['pvt'] = ta.pvt(df['close'], df['volume'])
            
            return df
        except Exception as e:
            self.logger.error(f"计算成交量指标时出错: {str(e)}")
            return df