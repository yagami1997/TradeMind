# 标准库
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 第三方库
import pandas as pd

# 项目模块
from .tech_indicator_calculator import TechIndicatorCalculator

class AdvancedAnalysis:
    """高级技术分析：提供深度市场分析和预测"""
    
    def __init__(self):
        """初始化高级分析器"""
        self.setup_logging()
        self.indicators = TechIndicatorCalculator()
        
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(
            "logs/advanced_analysis.log", 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)

    def analyze_trend_strength(self, df: pd.DataFrame) -> Dict:
        """
        分析趋势强度
        
        Args:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame
            
        Returns:
            Dict: 趋势强度分析结果
        """
        try:
            # 确保数据包含必要的技术指标
            df = self.indicators.calculate_all(df)
            
            # 计算趋势强度指标
            trend_metrics = {
                'price_trend': self._analyze_price_trend(df),
                'volume_trend': self._analyze_volume_trend(df),
                'momentum': self._analyze_momentum(df),
                'volatility': self._analyze_volatility(df)
            }
            
            # 计算综合趋势强度
            trend_strength = self._calculate_trend_strength(trend_metrics)
            
            return {
                'metrics': trend_metrics,
                'strength': trend_strength,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"分析趋势强度时出错: {str(e)}")
            return {}
            
    def _analyze_price_trend(self, df: pd.DataFrame) -> Dict:
        """分析价格趋势"""
        try:
            latest = df.iloc[-1]
            
            # 计算各均线位置关系
            ma_trend = {
                'above_ma20': latest['close'] > latest['ma20'],
                'above_ma60': latest['close'] > latest['ma60'],
                'ma20_above_ma60': latest['ma20'] > latest['ma60']
            }
            
            # 计算趋势得分
            trend_score = sum(1 for v in ma_trend.values() if v) / len(ma_trend)
            
            return {
                'score': trend_score,
                'direction': 'up' if trend_score > 0.5 else 'down',
                'details': ma_trend
            }
            
        except Exception as e:
            self.logger.error(f"分析价格趋势时出错: {str(e)}")
            return {}
            
    def _analyze_volume_trend(self, df: pd.DataFrame) -> Dict:
        """分析成交量趋势"""
        try:
            latest = df.iloc[-1]
            
            # 计算成交量变化
            volume_change = (latest['volume'] - df['volume'].mean()) / df['volume'].mean()
            
            # 计算成交量趋势
            volume_trend = {
                'above_ma5': latest['volume'] > latest['volume_ma5'],
                'above_ma10': latest['volume'] > latest['volume_ma10'],
                'increasing': volume_change > 0
            }
            
            # 计算趋势得分
            trend_score = sum(1 for v in volume_trend.values() if v) / len(volume_trend)
            
            return {
                'score': trend_score,
                'change': volume_change,
                'details': volume_trend
            }
            
        except Exception as e:
            self.logger.error(f"分析成交量趋势时出错: {str(e)}")
            return {}
            
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """分析动量指标"""
        try:
            latest = df.iloc[-1]
            
            # 分析各动量指标
            momentum = {
                'rsi_strong': latest['rsi'] > 50,
                'macd_positive': latest['macd'] > latest['macd_signal'],
                'kdj_strong': latest['k'] > latest['d']
            }
            
            # 计算动量得分
            momentum_score = sum(1 for v in momentum.values() if v) / len(momentum)
            
            return {
                'score': momentum_score,
                'strength': 'strong' if momentum_score > 0.7 else 'weak',
                'details': momentum
            }
            
        except Exception as e:
            self.logger.error(f"分析动量指标时出错: {str(e)}")
            return {}
            
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """分析波动性"""
        try:
            # 计算波动率
            returns = df['close'].pct_change()
            volatility = returns.std()
            
            # 计算布林带宽度
            latest = df.iloc[-1]
            bb_width = (latest['bb_upper'] - latest['bb_lower']) / latest['bb_middle']
            
            # 判断波动状态
            volatility_state = {
                'high_volatility': volatility > returns.std().mean(),
                'expanding_bb': bb_width > df['bb_upper'].sub(df['bb_lower']).div(df['bb_middle']).mean(),
                'price_near_band': min(
                    abs(latest['close'] - latest['bb_upper']),
                    abs(latest['close'] - latest['bb_lower'])
                ) < (latest['bb_upper'] - latest['bb_lower']) * 0.1
            }
            
            return {
                'volatility': volatility,
                'bb_width': bb_width,
                'state': volatility_state
            }
            
        except Exception as e:
            self.logger.error(f"分析波动性时出错: {str(e)}")
            return {}
            
    def _calculate_trend_strength(self, metrics: Dict) -> float:
        """计算综合趋势强度"""
        try:
            weights = {
                'price_trend': 0.4,
                'volume_trend': 0.2,
                'momentum': 0.3,
                'volatility': 0.1
            }
            
            # 计算加权得分
            weighted_score = (
                metrics['price_trend']['score'] * weights['price_trend'] +
                metrics['volume_trend']['score'] * weights['volume_trend'] +
                metrics['momentum']['score'] * weights['momentum']
            )
            
            # 根据波动性调整得分
            if metrics['volatility']['state']['high_volatility']:
                weighted_score *= 0.9  # 高波动性降低可信度
                
            return round(weighted_score, 2)
            
        except Exception as e:
            self.logger.error(f"计算趋势强度时出错: {str(e)}")
            return 0.0

    def analyze_market_sentiment(self, df: pd.DataFrame) -> Dict:
        """
        分析市场情绪
        
        Args:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame
            
        Returns:
            Dict: 市场情绪分析结果
        """
        try:
            # 确保数据包含必要的技术指标
            df = self.indicators.calculate_all(df)
            
            # 分析各个维度的市场情绪
            sentiment = {
                'technical': self._analyze_technical_sentiment(df),
                'momentum': self._analyze_momentum_sentiment(df),
                'volatility': self._analyze_volatility_sentiment(df)
            }
            
            # 计算综合情绪指标
            overall_sentiment = self._calculate_overall_sentiment(sentiment)
            
            return {
                'sentiment': sentiment,
                'overall': overall_sentiment,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"分析市场情绪时出错: {str(e)}")
            return {}
            
    def _analyze_technical_sentiment(self, df: pd.DataFrame) -> Dict:
        """分析技术面情绪"""
        try:
            latest = df.iloc[-1]
            
            # 分析技术指标
            technical = {
                'ma_alignment': all([
                    latest['ma5'] > latest['ma20'],
                    latest['ma20'] > latest['ma60']
                ]),
                'bb_position': (
                    'overbought' if latest['close'] > latest['bb_upper']
                    else 'oversold' if latest['close'] < latest['bb_lower']
                    else 'neutral'
                ),
                'rsi_state': (
                    'overbought' if latest['rsi'] > 70
                    else 'oversold' if latest['rsi'] < 30
                    else 'neutral'
                )
            }
            
            # 计算技术面得分
            score = 0.5  # 基础分
            if technical['ma_alignment']: score += 0.2
            if technical['bb_position'] == 'oversold': score += 0.2
            if technical['rsi_state'] == 'oversold': score += 0.1
            
            return {
                'score': min(score, 1.0),
                'details': technical
            }
            
        except Exception as e:
            self.logger.error(f"分析技术面情绪时出错: {str(e)}")
            return {}
            
    def _analyze_momentum_sentiment(self, df: pd.DataFrame) -> Dict:
        """分析动量情绪"""
        try:
            latest = df.iloc[-1]
            
            # 分析动量指标
            momentum = {
                'macd': latest['macd'] > latest['macd_signal'],
                'kdj': latest['k'] > latest['d'],
                'rsi_trend': latest['rsi'] > df['rsi'].shift(1).iloc[-1]
            }
            
            # 计算动量情绪得分
            score = sum(1 for v in momentum.values() if v) / len(momentum)
            
            return {
                'score': score,
                'details': momentum
            }
            
        except Exception as e:
            self.logger.error(f"分析动量情绪时出错: {str(e)}")
            return {}
            
    def _analyze_volatility_sentiment(self, df: pd.DataFrame) -> Dict:
        """分析波动性情绪"""
        try:
            # 计算波动指标
            returns = df['close'].pct_change()
            current_vol = returns.std()
            hist_vol = returns.rolling(window=20).std().mean()
            
            volatility = {
                'increasing': current_vol > hist_vol,
                'level': 'high' if current_vol > hist_vol * 1.2 else 'low',
                'trend': current_vol / hist_vol
            }
            
            # 计算波动性情绪得分
            score = 0.5  # 基础分
            if not volatility['increasing']: score += 0.2
            if volatility['level'] == 'low': score += 0.3
            
            return {
                'score': score,
                'details': volatility
            }
            
        except Exception as e:
            self.logger.error(f"分析波动性情绪时出错: {str(e)}")
            return {}
            
    def _calculate_overall_sentiment(self, sentiment: Dict) -> Dict:
        """计算综合情绪指标"""
        try:
            # 设置权重
            weights = {
                'technical': 0.4,
                'momentum': 0.4,
                'volatility': 0.2
            }
            
            # 计算加权得分
            weighted_score = sum(
                sentiment[k]['score'] * weights[k]
                for k in weights.keys()
            )
            
            # 确定情绪状态
            if weighted_score >= 0.7:
                state = 'bullish'
            elif weighted_score <= 0.3:
                state = 'bearish'
            else:
                state = 'neutral'
                
            return {
                'score': round(weighted_score, 2),
                'state': state
            }
            
        except Exception as e:
            self.logger.error(f"计算综合情绪指标时出错: {str(e)}")
            return {'score': 0.5, 'state': 'neutral'}

    def identify_patterns(self, df: pd.DataFrame) -> Dict:
        """
        识别市场形态
        
        Args:
            df (pd.DataFrame): 价格数据
            
        Returns:
            Dict: 形态识别结果
        """
        try:
            patterns = {
                'candlestick': self._identify_candlestick_patterns(df),
                'chart': self._identify_chart_patterns(df),
                'support_resistance': self._calculate_support_resistance(df)
            }
            
            return {
                'patterns': patterns,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.logger.error(f"识别市场形态时出错: {str(e)}")
            return {}

    def _identify_candlestick_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """识别K线形态"""
        try:
            patterns = []
            latest = df.iloc[-3:]  # 分析最近3根K线
            
            # 十字星
            if abs(latest.iloc[-1]['open'] - latest.iloc[-1]['close']) < (latest.iloc[-1]['high'] - latest.iloc[-1]['low']) * 0.1:
                patterns.append({
                    'name': 'doji',
                    'type': 'reversal',
                    'confidence': 0.6
                })
                
            # 锤子线
            if (latest.iloc[-1]['low'] - min(latest.iloc[-1]['open'], latest.iloc[-1]['close'])) > \
               abs(latest.iloc[-1]['open'] - latest.iloc[-1]['close']) * 2:
                patterns.append({
                    'name': 'hammer',
                    'type': 'bullish',
                    'confidence': 0.7
                })
                
            return patterns
        except Exception as e:
            self.logger.error(f"识别K线形态时出错: {str(e)}")
            return []

    def _identify_chart_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """识别图表形态"""
        try:
            patterns = []
            
            # 双底形态
            if self._is_double_bottom(df):
                patterns.append({
                    'name': 'double_bottom',
                    'type': 'bullish',
                    'confidence': 0.8
                })
                
            # 头肩顶形态
            if self._is_head_and_shoulders(df):
                patterns.append({
                    'name': 'head_and_shoulders',
                    'type': 'bearish',
                    'confidence': 0.75
                })
                
            return patterns
        except Exception as e:
            self.logger.error(f"识别图表形态时出错: {str(e)}")
            return []

    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """计算支撑和阻力位"""
        try:
            # 使用过去30天的数据
            recent_df = df.tail(30)
            
            # 寻找局部最高点和最低点
            highs = recent_df[recent_df['high'] == recent_df['high'].rolling(5, center=True).max()]
            lows = recent_df[recent_df['low'] == recent_df['low'].rolling(5, center=True).min()]
            
            current_price = df['close'].iloc[-1]
            
            # 找到最近的支撑位和阻力位
            support = lows[lows['low'] < current_price]['low'].max()
            resistance = highs[highs['high'] > current_price]['high'].min()
            
            return {
                'support': support,
                'resistance': resistance,
                'current_price': current_price
            }
        except Exception as e:
            self.logger.error(f"计算支撑阻力位时出错: {str(e)}")
            return {}

    def _is_double_bottom(self, df: pd.DataFrame) -> bool:
        """识别双底形态"""
        try:
            # 使用过去60天的数据
            recent_df = df.tail(60)
            
            # 寻找局部最低点
            lows = recent_df[recent_df['low'] == recent_df['low'].rolling(10, center=True).min()]
            if len(lows) < 2:
                return False
            
            # 获取最后两个低点
            last_two_lows = lows.tail(2)
            
            # 检查双底条件
            price_diff = abs(last_two_lows['low'].iloc[0] - last_two_lows['low'].iloc[1])
            time_diff = (last_two_lows.index[1] - last_two_lows.index[0]).days
            
            # 两个低点价格接近且时间间隔合适
            return price_diff < last_two_lows['low'].mean() * 0.02 and 10 <= time_diff <= 40
        
        except Exception as e:
            self.logger.error(f"识别双底形态时出错: {str(e)}")
            return False

    def _is_head_and_shoulders(self, df: pd.DataFrame) -> bool:
        """识别头肩顶形态"""
        try:
            # 使用过去90天的数据
            recent_df = df.tail(90)
            
            # 寻找局部最高点
            highs = recent_df[recent_df['high'] == recent_df['high'].rolling(10, center=True).max()]
            if len(highs) < 3:
                return False
            
            # 获取最后三个高点
            last_three_highs = highs.tail(3)
            
            # 检查头肩顶条件
            left_shoulder = last_three_highs['high'].iloc[0]
            head = last_three_highs['high'].iloc[1]
            right_shoulder = last_three_highs['high'].iloc[2]
            
            # 头部高于两肩，两肩高度接近
            return (head > left_shoulder and 
                    head > right_shoulder and 
                    abs(left_shoulder - right_shoulder) < left_shoulder * 0.02)
        
        except Exception as e:
            self.logger.error(f"识别头肩顶形态时出错: {str(e)}")
            return False

if __name__ == "__main__":
    # 示例用法
    import yfinance as yf
    
    try:
        # 获取示例数据
        symbol = "AAPL"
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        
        # 创建分析器
        analyzer = AdvancedAnalysis()
        
        # 分析趋势强度
        trend_analysis = analyzer.analyze_trend_strength(df)
        print("\n=== 趋势强度分析 ===")
        print(f"综合强度: {trend_analysis.get('strength', 0)}")
        
        # 分析市场情绪
        sentiment_analysis = analyzer.analyze_market_sentiment(df)
        print("\n=== 市场情绪分析 ===")
        overall = sentiment_analysis.get('overall', {})
        print(f"情绪状态: {overall.get('state', 'unknown')}")
        print(f"情绪得分: {overall.get('score', 0)}")
        
        # 分析市场形态
        print("\n=== 市场形态分析 ===")
        pattern_analysis = analyzer.identify_patterns(df)
        if pattern_analysis.get('patterns'):
            print("\n发现的形态:")
            for pattern_type, patterns in pattern_analysis['patterns'].items():
                if isinstance(patterns, list):
                    for p in patterns:
                        print(f"- {p['name']} ({p['type']}, 置信度: {p['confidence']})")
                elif isinstance(patterns, dict):
                    print(f"支撑位: {patterns.get('support', 'N/A')}")
                    print(f"阻力位: {patterns.get('resistance', 'N/A')}")
        
    except Exception as e:
        print(f"分析过程中出错: {str(e)}")
