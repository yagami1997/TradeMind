import pandas as pd
import pandas_ta as ta
import logging

class TechIndicatorCalculator:
    """技术指标计算器
    
    该类负责计算各种技术分析指标，包括：
    - 移动平均线 (MA, EMA)
    - MACD指标
    - RSI指标
    - 布林带
    - KDJ指标
    - 成交量指标
    - ATR, OBV, VWAP等高级指标
    
    所有方法都包含错误处理，确保在计算失败时返回原始DataFrame。
    
    Attributes:
        logger: 日志记录器
        required_columns (list): 必需的数据列名列表
    """
    
    def __init__(self):
        """初始化技术指标计算器"""
        self.logger = logging.getLogger(__name__)
        self.required_columns = ['open', 'high', 'low', 'close', 'volume']

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """验证DataFrame是否包含所需的列
        
        Args:
            df: 输入的DataFrame
            
        Raises:
            KeyError: 如果缺少必要的列
        """
        df.columns = [col.lower() for col in df.columns]
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"缺少必要的列: {missing_columns}")

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标
        
        Args:
            df: 必须包含OHLCV数据的DataFrame
            
        Returns:
            添加了所有技术指标的DataFrame
            
        Note:
            如果计算过程中出现错误，将记录错误并返回原始DataFrame
        """
        try:
            self._validate_dataframe(df)
            df = df.copy()  # 避免修改原始数据
            
            # 计算各类指标
            calculators = [
                self.calculate_ma,
                self.calculate_macd,
                self.calculate_rsi,
                self.calculate_bollinger_bands,
                self.calculate_kdj,
                self.calculate_volume_indicators,
                self.calculate_atr,
                self.calculate_obv,
                self.calculate_vwap
            ]
            
            for calculator in calculators:
                df = calculator(df)
            
            return df
        except Exception as e:
            self.logger.error(f"计算技术指标时出错: {str(e)}")
            return df

    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均线
        
        计算以下指标：
        - 短期均线: MA5, MA10, MA20 (日内/短线交易)
        - 中期均线: MA30, MA60, MA120 (趋势跟踪)
        - 长期均线: MA200, MA250 (年线/大趋势)
        - 指数均线: EMA12, EMA26 (MACD基础)
        
        Args:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 添加了移动平均线的DataFrame
            
        Note:
            短期均线用于日内和短线交易
            中期均线用于判断中期趋势
            长期均线用于判断大趋势和牛熊分界
        """
        try:
            # 短期均线
            short_periods = [5, 10, 20]
            for period in short_periods:
                df[f'ma{period}'] = ta.sma(df['close'], length=period)
            
            # 中期均线
            medium_periods = [30, 60, 120]
            for period in medium_periods:
                df[f'ma{period}'] = ta.sma(df['close'], length=period)
            
            # 长期均线
            long_periods = [200, 250]
            for period in long_periods:
                df[f'ma{period}'] = ta.sma(df['close'], length=period)
            
            # 指数移动平均线
            df['ema12'] = ta.ema(df['close'], length=12)
            df['ema26'] = ta.ema(df['close'], length=26)
            
            return df
        except Exception as e:
            self.logger.error(f"计算MA指标时出错: {str(e)}")
            return df

    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标
        
        计算移动平均收敛散度指标，包括：
        - MACD线 (12日EMA - 26日EMA)
        - 信号线 (9日MACD的EMA)
        - MACD柱状图 (MACD线 - 信号线)
        
        Args:
            df (pd.DataFrame): 包含收盘价数据的DataFrame
            
        Returns:
            pd.DataFrame: 添加了MACD指标的DataFrame
        """
        try:
            macd = ta.macd(df['close'])
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']
            return df
        except Exception as e:
            self.logger.error(f"计算MACD指标时出错: {str(e)}")
            return df

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI指标
        
        相对强弱指标，用于判断超买超卖：
        - RSI > 70: 超买区域
        - RSI < 30: 超卖区域
        
        Args:
            df: 包含收盘价数据的DataFrame
            period: RSI计算周期，默认14天
        """
        try:
            df['rsi'] = ta.rsi(df['close'], length=period)
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
            df['volume_ma5'] = ta.sma(df['volume'], length=5)
            df['volume_ma10'] = ta.sma(df['volume'], length=10)
            df['volume_change'] = df['volume'].pct_change()
            df['pvt'] = ta.pvt(df['close'], df['volume'])
            return df
        except Exception as e:
            self.logger.error(f"计算成交量指标时出错: {str(e)}")
            return df

    def calculate_atr(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算ATR指标"""
        try:
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            return df
        except Exception as e:
            self.logger.error(f"计算ATR指标时出错: {str(e)}")
            return df

    def calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算OBV指标"""
        try:
            df['obv'] = ta.obv(df['close'], df['volume'])
            return df
        except Exception as e:
            self.logger.error(f"计算OBV指标时出错: {str(e)}")
            return df

    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算VWAP指标"""
        try:
            df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            return df
        except Exception as e:
            self.logger.error(f"计算VWAP指标时出错: {str(e)}")
            return df 