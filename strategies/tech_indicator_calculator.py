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
    - DMI, SAR等趋势指标
    
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
                self.calculate_vwap,
                self.calculate_dmi,
                self.calculate_parabolic_sar
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
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            添加了移动平均线的DataFrame
            
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

    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD指标
        
        计算移动平均收敛散度指标，包括：
        - MACD线 (快速EMA - 慢速EMA)
        - 信号线 (MACD的EMA)
        - MACD柱状图 (MACD线 - 信号线)
        
        Args:
            df: 包含收盘价数据的DataFrame
            fast: 快速EMA周期，默认12
            slow: 慢速EMA周期，默认26
            signal: 信号线周期，默认9
            
        Returns:
            添加了MACD指标的DataFrame
        """
        try:
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            df['macd'] = macd[f'MACD_{fast}_{slow}_{signal}']
            df['macd_signal'] = macd[f'MACDs_{fast}_{slow}_{signal}']
            df['macd_hist'] = macd[f'MACDh_{fast}_{slow}_{signal}']
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
            
        Returns:
            添加了RSI指标的DataFrame
        """
        try:
            df['rsi'] = ta.rsi(df['close'], length=period)
            return df
        except Exception as e:
            self.logger.error(f"计算RSI指标时出错: {str(e)}")
            return df

    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
        """计算布林带指标
        
        布林带包含三条线：
        - 中轨：N日移动平均线
        - 上轨：中轨 + K倍标准差
        - 下轨：中轨 - K倍标准差
        
        Args:
            df: 包含价格数据的DataFrame
            period: 移动平均的周期，默认20天
            std: 标准差的倍数，默认2.0
            
        Returns:
            添加了布林带指标的DataFrame
        """
        try:
            bollinger = ta.bbands(df['close'], length=period, std=std)
            df['bb_upper'] = bollinger[f'BBU_{period}_{std}.0']
            df['bb_middle'] = bollinger[f'BBM_{period}_{std}.0']
            df['bb_lower'] = bollinger[f'BBL_{period}_{std}.0']
            return df
        except Exception as e:
            self.logger.error(f"计算布林带时出错: {str(e)}")
            return df

    def calculate_kdj(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """计算KDJ指标
        
        随机指标KDJ，用于判断超买超卖：
        - K值：快速线
        - D值：慢速线
        - J值：预警线，J = 3K - 2D
        
        Args:
            df: 包含OHLC数据的DataFrame
            k_period: K值的计算周期，默认14天
            d_period: D值的计算周期，默认3天
            
        Returns:
            添加了KDJ指标的DataFrame
        """
        try:
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
            df['k'] = stoch[f'STOCHk_{k_period}_{d_period}_3']
            df['d'] = stoch[f'STOCHd_{k_period}_{d_period}_3']
            df['j'] = 3 * df['k'] - 2 * df['d']
            return df
        except Exception as e:
            self.logger.error(f"计算KDJ指标时出错: {str(e)}")
            return df

    def calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量相关指标
        
        包含以下成交量分析指标：
        - 成交量移动平均 (5日，10日)
        - 成交量变化率
        - 价格成交量趋势（PVT）
        - 成交量相对强弱
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            添加了成交量分析指标的DataFrame
        """
        try:
            # 成交量移动平均
            df['volume_ma5'] = ta.sma(df['volume'], length=5)
            df['volume_ma10'] = ta.sma(df['volume'], length=10)
            
            # 成交量变化率
            df['volume_change'] = df['volume'].pct_change()
            
            # 价格成交量趋势
            df['pvt'] = ta.pvt(df['close'], df['volume'])
            
            # 成交量相对强弱
            df['volume_rsi'] = ta.rsi(df['volume'], length=14)
            
            return df
        except Exception as e:
            self.logger.error(f"计算成交量指标时出错: {str(e)}")
            return df

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算ATR指标
        
        平均真实范围指标，用于衡量市场波动性：
        TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
        ATR = TR的N日移动平均
        
        Args:
            df: 包含OHLC数据的DataFrame
            period: ATR计算周期，默认14天
            
        Returns:
            添加了ATR指标的DataFrame
        """
        try:
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=period)
            return df
        except Exception as e:
            self.logger.error(f"计算ATR指标时出错: {str(e)}")
            return df

    def calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算OBV指标
        
        能量潮指标，通过成交量分析股价趋势：
        - 收盘价上涨，OBV = 前一日OBV + 当日成交量
        - 收盘价下跌，OBV = 前一日OBV - 当日成交量
        
        Args:
            df: 包含价格和成交量数据的DataFrame
            
        Returns:
            添加了OBV指标的DataFrame
        """
        try:
            df['obv'] = ta.obv(df['close'], df['volume'])
            return df
        except Exception as e:
            self.logger.error(f"计算OBV指标时出错: {str(e)}")
            return df

    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算VWAP指标
        
        成交量加权平均价格，反映市场交易的平均成本：
        VWAP = Σ(价格 * 成交量) / Σ(成交量)
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            添加了VWAP指标的DataFrame
        """
        try:
            df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            return df
        except Exception as e:
            self.logger.error(f"计算VWAP指标时出错: {str(e)}")
            return df

    def calculate_dmi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算DMI指标
        
        动向指标，用于判断趋势强度：
        - +DI: 上升动向指标
        - -DI: 下降动向指标
        - ADX: 平均动向指数
        
        Args:
            df: 包含OHLC数据的DataFrame
            period: 计算周期，默认14天
            
        Returns:
            添加了DMI指标的DataFrame
        """
        try:
            dmi = ta.adx(df['high'], df['low'], df['close'], length=period)
            df['plus_di'] = dmi[f'DMP_{period}']
            df['minus_di'] = dmi[f'DMN_{period}']
            df['adx'] = dmi[f'ADX_{period}']
            return df
        except Exception as e:
            self.logger.error(f"计算DMI指标时出错: {str(e)}")
            return df

    def calculate_parabolic_sar(self, df: pd.DataFrame, 
                              acceleration: float = 0.02, 
                              maximum: float = 0.2) -> pd.DataFrame:
        """计算抛物线SAR指标
        
        用于确定趋势的反转点：
        - SAR点在价格下方，表示上升趋势
        - SAR点在价格上方，表示下降趋势
        
        Args:
            df: 包含OHLC数据的DataFrame
            acceleration: 加速因子，默认0.02
            maximum: 最大加速因子，默认0.2
            
        Returns:
            添加了SAR指标的DataFrame
        """
        try:
            df['sar'] = ta.psar(df['high'], df['low'], 
                               af=acceleration, 
                               max_af=maximum)['PSARl_0.02_0.2']
            return df
        except Exception as e:
            self.logger.error(f"计算SAR指标时出错: {str(e)}")
            return df 