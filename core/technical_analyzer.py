"""
技术分析工具
提供各种技术指标的计算和分析功能
"""
import pandas as pd
import numpy as np
from typing import List
import logging
from functools import lru_cache
from .exceptions import DataValidationError

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """技术分析器，用于计算各种技术指标"""
    
    def __init__(self):
        """初始化技术分析器"""
        self.required_columns = ['open', 'high', 'low', 'close', 'volume']
        self._setup_logging()
        
    def _setup_logging(self):
        """配置日志"""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def _validate_data(self, data: pd.DataFrame) -> bool:
        """验证输入数据的有效性"""
        try:
            # 检查必要的列
            missing_cols = [col for col in self.required_columns if col not in data.columns]
            if missing_cols:
                raise DataValidationError(f"数据缺少必要列: {missing_cols}")
            
            # 检查数据类型
            for col in self.required_columns:
                if not np.issubdtype(data[col].dtype, np.number):
                    raise DataValidationError(f"列 {col} 必须是数值类型")
            
            # 检查是否有空值
            if data[self.required_columns].isnull().any().any():
                raise DataValidationError("数据包含空值")
            
            # 检查是否有负值
            if (data[['open', 'high', 'low', 'close', 'volume']] < 0).any().any():
                raise DataValidationError("价格或成交量不能为负")
                
            return True
            
        except Exception as e:
            logger.error(f"数据验证失败: {str(e)}")
            raise

    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_ma(data: pd.DataFrame, periods: tuple[int, ...]) -> pd.DataFrame:
        """计算移动平均线（带缓存）
        
        Args:
            data: 包含 'close' 列的 DataFrame
            periods: MA周期元组，如 (5, 10, 20, 60)
            
        Returns:
            DataFrame: 包含MA列的DataFrame
        """
        try:
            df = data.copy()
            for period in periods:
                df[f'ma{period}'] = df['close'].rolling(window=period).mean()
            return df
        except Exception as e:
            logger.error(f"计算MA指标时出错: {str(e)}")
            raise
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, 
                      fast_period: int = 12,
                      slow_period: int = 26,
                      signal_period: int = 9) -> pd.DataFrame:
        """计算MACD指标"""
        df = data.copy()
        # 计算快速和慢速EMA
        ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # 计算MACD线
        df['macd'] = ema_fast - ema_slow
        # 计算信号线
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
        # 计算MACD柱状图
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        df = data.copy()
        delta = df['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.DataFrame, 
                                period: int = 20,
                                std_dev: float = 2.0) -> pd.DataFrame:
        """计算布林带指标"""
        df = data.copy()
        
        # 计算中轨（简单移动平均线）
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        # 计算标准差
        rolling_std = df['close'].rolling(window=period).std()
        
        # 计算上轨和下轨
        df['bb_upper'] = df['bb_middle'] + (rolling_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * std_dev)
        
        return df
    
    @staticmethod
    def calculate_kdj(data: pd.DataFrame, 
                     k_period: int = 9,
                     d_period: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        df = data.copy()
        
        # 计算最低价和最高价的N日移动窗口
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        # 计算RSV
        rsv = 100 * (df['close'] - low_min) / (high_max - low_min)
        
        # 计算K值
        df['k'] = rsv.rolling(window=d_period).mean()
        # 计算D值
        df['d'] = df['k'].rolling(window=d_period).mean()
        # 计算J值
        df['j'] = 3 * df['k'] - 2 * df['d']
        
        return df
    
    @staticmethod
    def calculate_volume_indicators(data: pd.DataFrame) -> pd.DataFrame:
        """计算成交量相关指标"""
        df = data.copy()
        
        # 计算成交量移动平均
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma10'] = df['volume'].rolling(window=10).mean()
        
        # 计算成交量变化率
        df['volume_change'] = df['volume'].pct_change()
        
        # 计算价量相关性
        df['price_volume_corr'] = (
            df['close'].rolling(window=5)
            .corr(df['volume'])
        )
        
        return df
    
    @staticmethod
    def calculate_momentum(data: pd.DataFrame, 
                         period: int = 10) -> pd.DataFrame:
        """计算动量指标"""
        df = data.copy()
        
        # 计算动量
        df['momentum'] = df['close'].diff(period)
        
        # 计算ROC（变动率）
        df['roc'] = df['close'].pct_change(period) * 100
        
        return df
    
    @staticmethod
    def calculate_volatility(data: pd.DataFrame, 
                           period: int = 20) -> pd.DataFrame:
        """计算波动率指标"""
        df = data.copy()
        
        # 计算历史波动率
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=period).std() * np.sqrt(252)
        
        # 计算真实波幅（TR和ATR）
        df['tr'] = pd.DataFrame({
            'hl': df['high'] - df['low'],
            'hc': abs(df['high'] - df['close'].shift()),
            'lc': abs(df['low'] - df['close'].shift())
        }).max(axis=1)
        
        df['atr'] = df['tr'].rolling(window=period).mean()
        
        return df

    @staticmethod
    def calculate_ichimoku(data: pd.DataFrame,
                          tenkan_period: int = 9,
                          kijun_period: int = 26,
                          senkou_b_period: int = 52) -> pd.DataFrame:
        """计算一目均衡图指标
        
        Args:
            data: 价格数据
            tenkan_period: 转换线周期
            kijun_period: 基准线周期
            senkou_b_period: 先行带B周期
        """
        try:
            df = data.copy()
            
            # 计算转换线（Tenkan-sen）
            high_tenkan = df['high'].rolling(window=tenkan_period).max()
            low_tenkan = df['low'].rolling(window=tenkan_period).min()
            df['tenkan_sen'] = (high_tenkan + low_tenkan) / 2
            
            # 计算基准线（Kijun-sen）
            high_kijun = df['high'].rolling(window=kijun_period).max()
            low_kijun = df['low'].rolling(window=kijun_period).min()
            df['kijun_sen'] = (high_kijun + low_kijun) / 2
            
            # 计算先行带A（Senkou Span A）
            df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(kijun_period)
            
            # 计算先行带B（Senkou Span B）
            high_senkou = df['high'].rolling(window=senkou_b_period).max()
            low_senkou = df['low'].rolling(window=senkou_b_period).min()
            df['senkou_span_b'] = ((high_senkou + low_senkou) / 2).shift(kijun_period)
            
            # 计算延迟线（Chikou Span）
            df['chikou_span'] = df['close'].shift(-kijun_period)
            
            return df
            
        except Exception as e:
            logger.error(f"计算一目均衡图指标时出错: {str(e)}")
            raise
            
    @staticmethod
    def calculate_dmi(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算动向指标DMI
        
        Args:
            data: 价格数据
            period: 计算周期
        """
        try:
            df = data.copy()
            
            # 计算方向变动
            df['up_move'] = df['high'].diff()
            df['down_move'] = -df['low'].diff()
            
            # 计算+DM和-DM
            df['plus_dm'] = np.where(
                (df['up_move'] > df['down_move']) & (df['up_move'] > 0),
                df['up_move'],
                0
            )
            df['minus_dm'] = np.where(
                (df['down_move'] > df['up_move']) & (df['down_move'] > 0),
                df['down_move'],
                0
            )
            
            # 计算TR
            df['tr'] = pd.DataFrame({
                'hl': df['high'] - df['low'],
                'hc': abs(df['high'] - df['close'].shift()),
                'lc': abs(df['low'] - df['close'].shift())
            }).max(axis=1)
            
            # 计算平滑值
            df['smoothed_plus_dm'] = df['plus_dm'].rolling(window=period).sum()
            df['smoothed_minus_dm'] = df['minus_dm'].rolling(window=period).sum()
            df['smoothed_tr'] = df['tr'].rolling(window=period).sum()
            
            # 计算+DI和-DI
            df['plus_di'] = 100 * df['smoothed_plus_dm'] / df['smoothed_tr']
            df['minus_di'] = 100 * df['smoothed_minus_dm'] / df['smoothed_tr']
            
            # 计算DX
            df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
            
            # 计算ADX
            df['adx'] = df['dx'].rolling(window=period).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"计算DMI指标时出错: {str(e)}")
            raise
            
    @staticmethod
    def calculate_squeeze_momentum(data: pd.DataFrame,
                                 bb_period: int = 20,
                                 kc_period: int = 20,
                                 kc_mult: float = 2.0,
                                 mom_period: int = 12) -> pd.DataFrame:
        """计算挤压动量指标（Squeeze Momentum）
        
        Args:
            data: 价格数据
            bb_period: 布林带周期
            kc_period: KC通道周期
            kc_mult: KC通道乘数
            mom_period: 动量周期
        """
        try:
            df = data.copy()
            
            # 计算布林带
            df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
            bb_std = df['close'].rolling(window=bb_period).std()
            df['bb_upper'] = df['bb_middle'] + 2 * bb_std
            df['bb_lower'] = df['bb_middle'] - 2 * bb_std
            
            # 计算Keltner通道
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            df['kc_middle'] = typical_price.rolling(window=kc_period).mean()
            range_ma = pd.DataFrame({
                'hl': df['high'] - df['low'],
                'hc': abs(df['high'] - df['close'].shift()),
                'lc': abs(df['low'] - df['close'].shift())
            }).max(axis=1).rolling(window=kc_period).mean()
            
            df['kc_upper'] = df['kc_middle'] + range_ma * kc_mult
            df['kc_lower'] = df['kc_middle'] - range_ma * kc_mult
            
            # 判断是否处于挤压状态
            df['is_squeezed'] = (df['bb_upper'] < df['kc_upper']) & (df['bb_lower'] > df['kc_lower'])
            
            # 计算线性回归斜率作为动量指标
            df['momentum'] = df['close'].rolling(window=mom_period).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            )
            
            return df
            
        except Exception as e:
            logger.error(f"计算Squeeze Momentum指标时出错: {str(e)}")
            raise

    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        try:
            # 验证数据
            self._validate_data(data)
            
            df = data.copy()
            
            # 计算移动平均线
            df = self.calculate_ma(df, (5, 10, 20, 60))
            
            # 计算MACD
            df = self.calculate_macd(df)
            
            # 计算RSI
            df = self.calculate_rsi(df)
            
            # 计算布林带
            df = self.calculate_bollinger_bands(df)
            
            # 计算KDJ
            df = self.calculate_kdj(df)
            
            # 计算成交量指标
            df = self.calculate_volume_indicators(df)
            
            # 计算动量指标
            df = self.calculate_momentum(df)
            
            # 计算波动率指标
            df = self.calculate_volatility(df)
            
            # 计算DMI指标
            df = self.calculate_dmi(df)
            
            # 计算一目均衡图
            df = self.calculate_ichimoku(df)
            
            # 计算Squeeze Momentum
            df = self.calculate_squeeze_momentum(df)
            
            logger.info("成功计算所有技术指标")
            return df
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
            raise
