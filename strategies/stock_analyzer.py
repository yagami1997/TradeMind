# 标准库
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from configparser import ConfigParser

# 第三方库
import pandas as pd
import numpy as np

# 项目模块
from .tech_indicator_calculator import TechIndicatorCalculator
from .advanced_analysis import AdvancedAnalysis
from data.data_manager_yf import YahooFinanceManager

@dataclass
class AnalysisResult:
    """分析结果数据类
    
    Attributes:
        score: 综合评分 (0-100)
        rating: 投资评级 (强烈推荐/推荐/持有/减持/强烈减持)
        target_price: 目标价格区间 (低/中/高)
        risk_level: 风险等级 (低/中/高)
        confidence: 分析置信度 (0-1)
        timestamp: 分析时间戳
    """
    score: float
    rating: str
    target_price: Dict[str, float]
    risk_level: str
    confidence: float
    timestamp: datetime

class StockAnalyzer:
    """股票分析器
    
    整合多维度分析功能：
    1. 基本面分析
       - 财务健康度
       - 估值水平
       - 成长潜力
       - 目标价预测
       - 投资评级
    
    2. 技术面分析
       - 趋势分析
       - 形态识别
       - 支撑阻力位
       - 技术指标综合
       - 周期分析
    
    3. 市场情绪分析
       - 成交量特征
       - 资金流向
       - 波动特征
    
    4. 综合评分
       - 多因子评分
       - 风险评估
       - 投资建议
    
    Attributes:
        logger: 日志记录器
        data_manager: 数据管理器
        tech_indicator: 技术指标计算器
        advanced_analyzer: 高级分析器
        rating_thresholds: 评级阈值设置
    """
    
    # 类常量配置
    RISK_THRESHOLDS = {
        'low': 0.15,
        'medium': 0.25
    }
    
    VALUATION_BENCHMARKS = {
        'pe_normal': 30,
        'pb_normal': 5
    }
    
    def __init__(self):
        """初始化股票分析器"""
        self.setup_logging()
        self.load_config()
        self.data_manager = YahooFinanceManager()
        self.tech_indicator = TechIndicatorCalculator()
        self.advanced_analyzer = AdvancedAnalysis()
        
        # 技术指标权重
        self.indicator_weights = {
            'trend': 0.4,         # 趋势分析权重
            'pattern': 0.2,       # 形态分析权重
            'technical': 0.2,     # 技术指标权重
            'volume': 0.2         # 成交量分析权重
        }

    def setup_logging(self):
        """设置日志系统"""
        self.logger = logging.getLogger(__name__)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(
            "logs/stock_analyzer.log", 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)

    def load_config(self):
        """加载配置文件"""
        try:
            config = ConfigParser()
            config.read('config/analysis_config.ini')
            
            # 加载各种配置
            self.score_weights = dict(config['ScoreWeights'])
            self.technical_weights = dict(config['TechnicalWeights'])
            self.fundamental_weights = dict(config['FundamentalWeights'])
            self.risk_thresholds = dict(config['RiskThresholds'])
            self.valuation_benchmarks = dict(config['ValuationBenchmarks'])
            self.rating_thresholds = dict(config['RatingThresholds'])
            self.financial_benchmarks = dict(config['FinancialBenchmarks'])
            self.pattern_params = dict(config['PatternRecognition'])
            
            # 转换字符串为浮点数
            for d in [self.score_weights, self.technical_weights, 
                     self.fundamental_weights, self.risk_thresholds,
                     self.valuation_benchmarks, self.rating_thresholds]:
                for k in d:
                    d[k] = float(d[k])
                    
        except Exception as e:
            self.logger.error(f"加载配置文件时出错: {str(e)}")
            # 使用默认值
            self._set_default_config()

    def analyze_stock(self, symbol: str, period: str = '1y') -> AnalysisResult:
        """综合分析股票
        
        Args:
            symbol: 股票代码
            period: 分析周期，默认1年
            
        Returns:
            AnalysisResult: 综合分析结果
        """
        try:
            # 获取数据
            df = self.data_manager.get_stock_data(symbol, period)
            if df.empty:
                raise ValueError(f"无法获取股票数据: {symbol}")
            
            # 技术面分析
            tech_analysis = self.technical_analysis(df)
            
            # 基本面分析
            fundamental_analysis = self.fundamental_analysis(symbol)
            
            # 市场情绪分析
            sentiment_analysis = self.sentiment_analysis(df)
            
            # 计算综合评分
            score = self.calculate_score(tech_analysis, fundamental_analysis, sentiment_analysis)
            
            # 生成目标价
            target_price = self.calculate_target_price(df, fundamental_analysis)
            
            # 确定评级
            rating = self.determine_rating(target_price['mid'], df['close'].iloc[-1])
            
            # 评估风险
            risk_level = self.assess_risk(df, fundamental_analysis)
            
            # 计算置信度
            confidence = self.calculate_confidence(tech_analysis, fundamental_analysis)
            
            return AnalysisResult(
                score=score,
                rating=rating,
                target_price=target_price,
                risk_level=risk_level,
                confidence=confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"分析股票时出错: {str(e)}")
            raise

    def technical_analysis(self, df: pd.DataFrame) -> Dict:
        """技术面分析
        
        Args:
            df: OHLCV数据
            
        Returns:
            技术分析结果字典
        """
        try:
            # 计算技术指标
            df = self.tech_indicator.calculate_all(df)
            
            # 趋势分析
            trend_analysis = self._analyze_trend(df)
            
            # 形态识别
            pattern_analysis = self._identify_patterns(df)
            
            # 支撑阻力位分析
            support_resistance = self._analyze_support_resistance(df)
            
            # 技术指标综合分析
            indicator_analysis = self._analyze_indicators(df)
            
            return {
                'trend': trend_analysis,
                'patterns': pattern_analysis,
                'support_resistance': support_resistance,
                'indicators': indicator_analysis,
                'score': self._calculate_technical_score(
                    trend_analysis,
                    pattern_analysis,
                    indicator_analysis
                )
            }
            
        except Exception as e:
            self.logger.error(f"技术分析时出错: {str(e)}")
            return {}

    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析价格趋势"""
        try:
            # 计算各周期趋势
            short_trend = df['ma20'].iloc[-1] > df['ma20'].iloc[-20]
            medium_trend = df['ma60'].iloc[-1] > df['ma60'].iloc[-60]
            long_trend = df['ma120'].iloc[-1] > df['ma120'].iloc[-120]
            
            # 趋势强度
            trend_strength = self.advanced_analyzer.analyze_trend_strength(df)
            
            return {
                'short_term': 1 if short_trend else -1,
                'medium_term': 1 if medium_trend else -1,
                'long_term': 1 if long_trend else -1,
                'strength': trend_strength.get('strength', 0)
            }
        except Exception as e:
            self.logger.error(f"分析趋势时出错: {str(e)}")
            return {}

    def _identify_patterns(self, df: pd.DataFrame) -> Dict:
        """识别技术形态"""
        try:
            patterns = {}
            
            # 头肩顶/底
            patterns['head_shoulders'] = self._check_head_shoulders(df)
            
            # 双重顶/底
            patterns['double_top_bottom'] = self._check_double_patterns(df)
            
            # 三角形整理
            patterns['triangle'] = self._check_triangle_pattern(df)
            
            # 计算形态可信度
            confidence = sum(1 for p in patterns.values() if p['identified']) / len(patterns)
            
            return {
                'patterns': patterns,
                'confidence': confidence
            }
        except Exception as e:
            self.logger.error(f"识别形态时出错: {str(e)}")
            return {}

    def _analyze_support_resistance(self, df: pd.DataFrame) -> Dict:
        """分析支撑阻力位"""
        try:
            # 使用价格分布方法查找支撑阻力位
            price_range = df['close'].max() - df['close'].min()
            bins = int(np.sqrt(len(df)))  # 使用平方根规则确定区间数
            
            hist, bin_edges = np.histogram(df['close'], bins=bins)
            peaks = self._find_peaks(hist)
            
            support_resistance_levels = [
                (bin_edges[i] + bin_edges[i+1])/2 
                for i in peaks
            ]
            
            current_price = df['close'].iloc[-1]
            
            # 找出最近的支撑位和阻力位
            support = max([p for p in support_resistance_levels if p < current_price], default=None)
            resistance = min([p for p in support_resistance_levels if p > current_price], default=None)
            
            return {
                'levels': support_resistance_levels,
                'support': support,
                'resistance': resistance,
                'strength': self._calculate_level_strength(df, support_resistance_levels)
            }
        except Exception as e:
            self.logger.error(f"分析支撑阻力位时出错: {str(e)}")
            return {}

    def fundamental_analysis(self, symbol: str) -> Dict:
        """基本面分析
        
        Args:
            symbol: 股票代码
            
        Returns:
            基本面分析结果字典
        """
        try:
            # 获取财务数据
            financial_data = self.data_manager.get_financial_data(symbol)
            
            # 财务指标分析
            financial_metrics = self._analyze_financials(financial_data)
            
            # 估值分析
            valuation = self._analyze_valuation(financial_data)
            
            # 成长性分析
            growth = self._analyze_growth(financial_data)
            
            # 计算目标价
            target_price = self._calculate_target_price(financial_data, valuation)
            
            return {
                'metrics': financial_metrics,
                'valuation': valuation,
                'growth': growth,
                'target_price': target_price,
                'score': self._calculate_fundamental_score(
                    financial_metrics,
                    valuation,
                    growth
                )
            }
        except Exception as e:
            self.logger.error(f"基本面分析时出错: {str(e)}")
            return {}

    def sentiment_analysis(self, df: pd.DataFrame) -> Dict:
        """市场情绪分析"""
        try:
            # 成交量分析
            volume_analysis = self._analyze_volume(df)
            
            # 波动性分析
            volatility_analysis = self._analyze_volatility(df)
            
            # 动量分析
            momentum_analysis = self._analyze_momentum(df)
            
            return {
                'volume': volume_analysis,
                'volatility': volatility_analysis,
                'momentum': momentum_analysis,
                'score': self._calculate_sentiment_score(
                    volume_analysis,
                    volatility_analysis,
                    momentum_analysis
                )
            }
        except Exception as e:
            self.logger.error(f"情绪分析时出错: {str(e)}")
            return {}

    def calculate_score(self, 
                       technical: Dict, 
                       fundamental: Dict, 
                       sentiment: Dict) -> float:
        """计算综合评分"""
        try:
            weights = {
                'technical': 0.4,
                'fundamental': 0.4,
                'sentiment': 0.2
            }
            
            scores = {
                'technical': technical.get('score', 0),
                'fundamental': fundamental.get('score', 0),
                'sentiment': sentiment.get('score', 0)
            }
            
            total_score = sum(
                scores[k] * weights[k]
                for k in weights
            )
            
            return round(total_score, 2)
        except Exception as e:
            self.logger.error(f"计算综合评分时出错: {str(e)}")
            return 0.0

    def determine_rating(self, target_price: float, current_price: float) -> str:
        """确定投资评级"""
        try:
            potential_return = (target_price - current_price) / current_price
            
            if potential_return > self.rating_thresholds['strong_buy']:
                return '强烈推荐'
            elif potential_return > self.rating_thresholds['buy']:
                return '推荐'
            elif potential_return > self.rating_thresholds['hold']:
                return '持有'
            elif potential_return > self.rating_thresholds['sell']:
                return '减持'
            else:
                return '强烈减持'
        except Exception as e:
            self.logger.error(f"确定评级时出错: {str(e)}")
            return '未知'

    def assess_risk(self, df: pd.DataFrame, fundamental: Dict) -> str:
        """评估风险等级"""
        try:
            # 计算波动风险
            volatility_risk = df['close'].pct_change().std() * np.sqrt(252)
            
            # 考虑基本面风险
            fundamental_risk = 1 - fundamental.get('metrics', {}).get('health_score', 0)
            
            # 综合风险评估
            total_risk = (volatility_risk + fundamental_risk) / 2
            
            if total_risk < self.risk_thresholds['low']:
                return '低风险'
            elif total_risk < self.risk_thresholds['medium']:
                return '中等风险'
            else:
                return '高风险'
        except Exception as e:
            self.logger.error(f"评估风险时出错: {str(e)}")
            return '未知'

    def calculate_confidence(self, technical: Dict, fundamental: Dict) -> float:
        """计算分析置信度"""
        try:
            # 技术面置信度
            technical_confidence = technical.get('patterns', {}).get('confidence', 0)
            
            # 基本面置信度
            fundamental_confidence = fundamental.get('metrics', {}).get('confidence', 0)
            
            # 加权平均
            confidence = (technical_confidence + fundamental_confidence) / 2
            
            return round(confidence, 2)
        except Exception as e:
            self.logger.error(f"计算置信度时出错: {str(e)}")
            return 0.0

    def _find_peaks(self, arr: np.ndarray) -> List[int]:
        """查找数组中的峰值点"""
        peaks = []
        for i in range(1, len(arr)-1):
            if arr[i] > arr[i-1] and arr[i] > arr[i+1]:
                peaks.append(i)
        return peaks

    def _calculate_level_strength(self, df: pd.DataFrame, levels: List[float]) -> float:
        """计算支撑阻力位强度"""
        try:
            strengths = []
            for level in levels:
                # 计算价格在该水平附近的次数
                near_level = df['close'].between(level*0.99, level*1.01)
                strength = near_level.sum() / len(df)
                strengths.append(strength)
            
            return np.mean(strengths) if strengths else 0
        except Exception as e:
            self.logger.error(f"计算支撑阻力位强度时出错: {str(e)}")
            return 0.0

    def _analyze_indicators(self, df: pd.DataFrame) -> Dict:
        """分析技术指标组合
        
        综合分析多个技术指标：
        - 趋势指标（MA/MACD/DMI）
        - 动量指标（RSI/KDJ/BOLL）
        - 成交量指标（OBV/PVT）
        
        Returns:
            Dict: 各指标的信号和权重
        """
        try:
            # MACD分析
            macd_signal = 1 if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] else -1
            
            # RSI分析
            rsi = df['rsi'].iloc[-1]
            rsi_signal = 1 if rsi < 30 else (-1 if rsi > 70 else 0)
            
            # KDJ分析
            kdj_signal = 1 if df['k'].iloc[-1] > df['d'].iloc[-1] else -1
            
            # 布林带分析
            bb_position = (df['close'].iloc[-1] - df['bb_middle'].iloc[-1]) / \
                         (df['bb_upper'].iloc[-1] - df['bb_middle'].iloc[-1])
            
            return {
                'macd': {'value': macd_signal, 'weight': 0.3},
                'rsi': {'value': rsi_signal, 'weight': 0.3},
                'kdj': {'value': kdj_signal, 'weight': 0.2},
                'bollinger': {'value': bb_position, 'weight': 0.2}
            }
        except Exception as e:
            self.logger.error(f"分析技术指标时出错: {str(e)}")
            return {}

    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """分析成交量特征
        
        分析内容：
        - 成交量趋势
        - 价格成交量关系
        - 异常成交量
        
        Returns:
            Dict: 成交量分析结果
        """
        try:
            # 成交量趋势
            volume_ma5 = df['volume_ma5'].iloc[-1]
            volume_ma10 = df['volume_ma10'].iloc[-1]
            volume_trend = 1 if volume_ma5 > volume_ma10 else -1
            
            # 价格成交量关系
            price_volume_corr = df['close'].pct_change().corr(df['volume'].pct_change())
            
            # 异常成交量检测
            volume_std = df['volume'].std()
            volume_mean = df['volume'].mean()
            abnormal_volume = df['volume'].iloc[-1] > volume_mean + 2 * volume_std
            
            return {
                'trend': volume_trend,
                'price_correlation': price_volume_corr,
                'abnormal': abnormal_volume,
                'strength': abs(price_volume_corr) * (1 + abnormal_volume)
            }
        except Exception as e:
            self.logger.error(f"分析成交量时出错: {str(e)}")
            return {}

    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """分析波动性特征
        
        分析内容：
        - 历史波动率
        - 相对波动率
        - 波动趋势
        
        Returns:
            Dict: 波动性分析结果
        """
        try:
            # 计算日波动率
            returns = df['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)
            
            # 计算相对波动率（与20日相比）
            current_vol = returns.tail(20).std()
            prev_vol = returns.iloc[-40:-20].std()
            rel_volatility = current_vol / prev_vol if prev_vol != 0 else 1
            
            # 波动率趋势
            vol_trend = 1 if current_vol > prev_vol else -1
            
            return {
                'annual_volatility': volatility,
                'relative_volatility': rel_volatility,
                'trend': vol_trend,
                'risk_level': 'high' if volatility > 0.3 else 'medium' if volatility > 0.2 else 'low'
            }
        except Exception as e:
            self.logger.error(f"分析波动性时出错: {str(e)}")
            return {}

    def _analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """分析动量特征
        
        分析内容：
        - RSI动量
        - MACD动量
        - 价格动量
        
        Returns:
            Dict: 动量分析结果
        """
        try:
            # RSI动量
            rsi = df['rsi'].iloc[-1]
            rsi_momentum = (rsi - 50) / 50  # 归一化到[-1, 1]
            
            # MACD动量
            macd_momentum = df['macd_hist'].iloc[-1] / df['close'].iloc[-1]  # 相对于价格的动量
            
            # 价格动量（20日）
            price_momentum = (df['close'].iloc[-1] / df['close'].iloc[-20] - 1)
            
            # 综合动量指标
            composite_momentum = (rsi_momentum + macd_momentum + price_momentum) / 3
            
            return {
                'rsi_momentum': rsi_momentum,
                'macd_momentum': macd_momentum,
                'price_momentum': price_momentum,
                'composite': composite_momentum,
                'strength': abs(composite_momentum)
            }
        except Exception as e:
            self.logger.error(f"分析动量时出错: {str(e)}")
            return {}

    def _calculate_technical_score(self, 
                                 trend: Dict, 
                                 pattern: Dict, 
                                 indicator: Dict) -> float:
        """计算技术分析综合得分
        
        Args:
            trend: 趋势分析结果
            pattern: 形态分析结果
            indicator: 指标分析结果
            
        Returns:
            float: 0-100的综合得分
        """
        try:
            # 趋势得分
            trend_score = (trend.get('strength', 0) + 1) * 50  # 转换到0-100
            
            # 形态得分
            pattern_score = pattern.get('confidence', 0) * 100
            
            # 指标得分
            indicator_values = [v['value'] * v['weight'] 
                              for v in indicator.values()]
            indicator_score = (sum(indicator_values) + 1) * 50  # 转换到0-100
            
            # 加权平均
            weights = self.technical_weights
            final_score = (
                trend_score * weights['trend'] +
                pattern_score * weights['pattern'] +
                indicator_score * weights['technical']
            )
            
            return round(min(max(final_score, 0), 100), 2)
        except Exception as e:
            self.logger.error(f"计算技术分析得分时出错: {str(e)}")
            return 0.0

    def _calculate_target_price(self, financial_data: Dict, valuation: Dict) -> Dict:
        """计算目标价格区间
        
        使用多种方法计算目标价：
        1. PE估值法
        2. PB估值法
        3. 历史估值区间
        
        Returns:
            Dict: 包含低、中、高三个目标价
        """
        try:
            current_price = financial_data.get('current_price', 0)
            if not current_price:
                return {'low': 0, 'mid': 0, 'high': 0}
            
            # PE估值法
            pe_target = current_price * (valuation.get('industry_pe', 15) / 
                                       valuation.get('current_pe', 15))
            
            # PB估值法
            pb_target = current_price * (valuation.get('industry_pb', 2) / 
                                       valuation.get('current_pb', 2))
            
            # 历史估值
            hist_high = valuation.get('historical_high', current_price * 1.2)
            hist_low = valuation.get('historical_low', current_price * 0.8)
            
            # 综合目标价
            targets = [pe_target, pb_target, hist_high, hist_low]
            valid_targets = [t for t in targets if t > 0]
            
            if not valid_targets:
                return {'low': current_price * 0.8,
                       'mid': current_price,
                       'high': current_price * 1.2}
            
            return {
                'low': min(valid_targets),
                'mid': sum(valid_targets) / len(valid_targets),
                'high': max(valid_targets)
            }
            
        except Exception as e:
            self.logger.error(f"计算目标价格时出错: {str(e)}")
            return {'low': 0, 'mid': 0, 'high': 0}

    def _analyze_financials(self, financial_data: Dict) -> Dict:
        """分析财务指标
        
        分析内容：
        - 盈利能力（ROE/ROA/毛利率）
        - 运营效率（周转率）
        - 偿债能力（资产负债率）
        - 现金流状况
        """
        try:
            return {
                'profitability': self._analyze_profitability(financial_data),
                'efficiency': self._analyze_efficiency(financial_data),
                'solvency': self._analyze_solvency(financial_data),
                'cash_flow': self._analyze_cash_flow(financial_data),
                'health_score': self._calculate_health_score(financial_data),
                'confidence': self._calculate_confidence_score(financial_data)
            }
        except Exception as e:
            self.logger.error(f"分析财务指标时出错: {str(e)}")
            return {}

    def _analyze_valuation(self, financial_data: Dict) -> Dict:
        """分析估值水平"""
        try:
            # 实现估值分析逻辑
            return {
                'current_pe': financial_data.get('pe', 0),
                'industry_pe': financial_data.get('industry_pe', 0),
                'current_pb': financial_data.get('pb', 0),
                'industry_pb': financial_data.get('industry_pb', 0),
                'historical_high': financial_data.get('historical_high', 0),
                'historical_low': financial_data.get('historical_low', 0)
            }
        except Exception as e:
            self.logger.error(f"分析估值水平时出错: {str(e)}")
            return {}

    def _analyze_growth(self, financial_data: Dict) -> Dict:
        """分析成长性"""
        try:
            # 实现成长性分析逻辑
            return {
                'revenue_growth': financial_data.get('revenue_growth', 0),
                'profit_growth': financial_data.get('profit_growth', 0),
                'market_share_trend': financial_data.get('market_share_trend', 0),
                'industry_position': financial_data.get('industry_position', 0)
            }
        except Exception as e:
            self.logger.error(f"分析成长性时出错: {str(e)}")
            return {}

    def _calculate_sentiment_score(self,
                                 volume: Dict,
                                 volatility: Dict,
                                 momentum: Dict) -> float:
        """计算市场情绪得分"""
        try:
            # 成交量得分
            volume_score = volume.get('strength', 0) * 100
            
            # 波动性得分（反向指标）
            volatility_level = volatility.get('risk_level', 'medium')
            volatility_score = 100 if volatility_level == 'low' else \
                              50 if volatility_level == 'medium' else 0
            
            # 动量得分
            momentum_score = (momentum.get('strength', 0) + 1) * 50
            
            # 加权平均
            weights = {'volume': 0.3, 'volatility': 0.3, 'momentum': 0.4}
            final_score = (
                volume_score * weights['volume'] +
                volatility_score * weights['volatility'] +
                momentum_score * weights['momentum']
            )
            
            return round(min(max(final_score, 0), 100), 2)
        except Exception as e:
            self.logger.error(f"计算情绪得分时出错: {str(e)}")
            return 0.0

    def _calculate_fundamental_score(self, metrics: Dict, valuation: Dict, growth: Dict) -> float:
        """计算基本面得分"""
        try:
            # 获取各个维度的得分
            profitability = metrics.get('profitability', {}).get('score', 0)
            efficiency = metrics.get('efficiency', {}).get('score', 0)
            solvency = metrics.get('solvency', {}).get('score', 0)
            cash_flow = metrics.get('cash_flow', {}).get('score', 0)
            
            # 估值得分（估值越低分数越高）
            pe_ratio = valuation.get('current_pe', 0)
            pb_ratio = valuation.get('current_pb', 0)
            valuation_score = (
                (1 - min(max(pe_ratio/30, 0), 1)) * 0.6 +
                (1 - min(max(pb_ratio/5, 0), 1)) * 0.4
            ) * 100
            
            # 成长性得分
            revenue_growth = growth.get('revenue_growth', 0)
            profit_growth = growth.get('profit_growth', 0)
            growth_score = (
                min(max(revenue_growth/0.3, 0), 1) * 0.5 +
                min(max(profit_growth/0.3, 0), 1) * 0.5
            ) * 100
            
            # 综合得分
            weights = self.fundamental_weights
            
            final_score = (
                profitability * weights['profitability'] +
                efficiency * weights['efficiency'] +
                solvency * weights['solvency'] +
                cash_flow * weights['cash_flow'] +
                valuation_score * weights['valuation'] +
                growth_score * weights['growth']
            )
            
            return round(final_score, 2)
        except Exception as e:
            self.logger.error(f"计算基本面得分时出错: {str(e)}")
            return 0.0

    def _analyze_profitability(self, financial_data: Dict) -> Dict:
        """分析盈利能力指标"""
        try:
            return {
                'roe': financial_data.get('roe', 0),
                'roa': financial_data.get('roa', 0),
                'gross_margin': financial_data.get('gross_margin', 0),
                'net_margin': financial_data.get('net_margin', 0),
                'score': self._calculate_profitability_score(financial_data)
            }
        except Exception as e:
            self.logger.error(f"分析盈利能力时出错: {str(e)}")
            return {}

    def _analyze_efficiency(self, financial_data: Dict) -> Dict:
        """分析运营效率指标"""
        try:
            return {
                'asset_turnover': financial_data.get('asset_turnover', 0),
                'inventory_turnover': financial_data.get('inventory_turnover', 0),
                'receivables_turnover': financial_data.get('receivables_turnover', 0),
                'score': self._calculate_efficiency_score(financial_data)
            }
        except Exception as e:
            self.logger.error(f"分析运营效率时出错: {str(e)}")
            return {}

    def _analyze_solvency(self, financial_data: Dict) -> Dict:
        """分析偿债能力指标"""
        try:
            return {
                'debt_ratio': financial_data.get('debt_ratio', 0),
                'current_ratio': financial_data.get('current_ratio', 0),
                'quick_ratio': financial_data.get('quick_ratio', 0),
                'score': self._calculate_solvency_score(financial_data)
            }
        except Exception as e:
            self.logger.error(f"分析偿债能力时出错: {str(e)}")
            return {}

    def _analyze_cash_flow(self, financial_data: Dict) -> Dict:
        """分析现金流状况"""
        try:
            return {
                'operating_cash_flow': financial_data.get('operating_cash_flow', 0),
                'free_cash_flow': financial_data.get('free_cash_flow', 0),
                'cash_flow_coverage': financial_data.get('cash_flow_coverage', 0),
                'score': self._calculate_cash_flow_score(financial_data)
            }
        except Exception as e:
            self.logger.error(f"分析现金流时出错: {str(e)}")
            return {}

    def _calculate_profitability_score(self, financial_data: Dict) -> float:
        """计算盈利能力得分"""
        try:
            roe = financial_data.get('roe', 0)
            roa = financial_data.get('roa', 0)
            gross_margin = financial_data.get('gross_margin', 0)
            net_margin = financial_data.get('net_margin', 0)
            
            # 简单加权平均
            weights = {'roe': 0.4, 'roa': 0.3, 'gross_margin': 0.2, 'net_margin': 0.1}
            score = (
                min(max(roe/0.15, 0), 1) * weights['roe'] +
                min(max(roa/0.08, 0), 1) * weights['roa'] +
                min(max(gross_margin/0.3, 0), 1) * weights['gross_margin'] +
                min(max(net_margin/0.15, 0), 1) * weights['net_margin']
            ) * 100
            
            return round(score, 2)
        except Exception as e:
            self.logger.error(f"计算盈利能力得分时出错: {str(e)}")
            return 0.0

    def _calculate_efficiency_score(self, financial_data: Dict) -> float:
        """计算运营效率得分"""
        try:
            asset_turnover = financial_data.get('asset_turnover', 0)
            inventory_turnover = financial_data.get('inventory_turnover', 0)
            receivables_turnover = financial_data.get('receivables_turnover', 0)
            
            # 加权平均
            weights = {
                'asset': 0.4,
                'inventory': 0.3,
                'receivables': 0.3
            }
            
            score = (
                min(max(asset_turnover/2, 0), 1) * weights['asset'] +
                min(max(inventory_turnover/6, 0), 1) * weights['inventory'] +
                min(max(receivables_turnover/8, 0), 1) * weights['receivables']
            ) * 100
            
            return round(score, 2)
        except Exception as e:
            self.logger.error(f"计算运营效率得分时出错: {str(e)}")
            return 0.0

    def _calculate_solvency_score(self, financial_data: Dict) -> float:
        """计算偿债能力得分"""
        try:
            debt_ratio = financial_data.get('debt_ratio', 0)
            current_ratio = financial_data.get('current_ratio', 0)
            quick_ratio = financial_data.get('quick_ratio', 0)
            
            # 加权平均
            weights = {
                'debt': 0.4,
                'current': 0.3,
                'quick': 0.3
            }
            
            score = (
                (1 - min(max(debt_ratio/0.7, 0), 1)) * weights['debt'] +
                min(max(current_ratio/2, 0), 1) * weights['current'] +
                min(max(quick_ratio/1, 0), 1) * weights['quick']
            ) * 100
            
            return round(score, 2)
        except Exception as e:
            self.logger.error(f"计算偿债能力得分时出错: {str(e)}")
            return 0.0

    def _calculate_cash_flow_score(self, financial_data: Dict) -> float:
        """计算现金流得分"""
        try:
            operating_cf = financial_data.get('operating_cash_flow', 0)
            free_cf = financial_data.get('free_cash_flow', 0)
            cf_coverage = financial_data.get('cash_flow_coverage', 0)
            
            # 加权平均
            weights = {
                'operating': 0.4,
                'free': 0.3,
                'coverage': 0.3
            }
            
            score = (
                min(max(operating_cf/1e8, 0), 1) * weights['operating'] +
                min(max(free_cf/1e8, 0), 1) * weights['free'] +
                min(max(cf_coverage/1.5, 0), 1) * weights['coverage']
            ) * 100
            
            return round(score, 2)
        except Exception as e:
            self.logger.error(f"计算现金流得分时出错: {str(e)}")
            return 0.0

    def _calculate_health_score(self, financial_data: Dict) -> float:
        """计算财务健康得分"""
        try:
            # 实现财务健康评分逻辑
            return 0.0  # 需要实现具体计算逻辑
        except Exception as e:
            self.logger.error(f"计算财务健康得分时出错: {str(e)}")
            return 0.0

    def _calculate_confidence_score(self, financial_data: Dict) -> float:
        """计算财务指标置信度"""
        try:
            # 实现财务指标置信度计算逻辑
            return 0.0  # 需要实现具体计算逻辑
        except Exception as e:
            self.logger.error(f"计算财务指标置信度时出错: {str(e)}")
            return 0.0

    def _check_head_shoulders(self, df: pd.DataFrame) -> Dict:
        """识别头肩顶/底形态
        
        Args:
            df: OHLCV数据
            
        Returns:
            Dict: {
                'identified': bool,  # 是否识别到形态
                'type': str,         # 'top' 或 'bottom'
                'confidence': float  # 置信度
            }
        """
        try:
            # 简单实现：检查左肩、头部、右肩的相对高度关系
            peaks = self._find_peaks(df['close'].values)
            if len(peaks) < 3:
                return {'identified': False, 'type': None, 'confidence': 0}
            
            # 检查三个连续峰值的相对高度
            for i in range(len(peaks)-2):
                left = df['close'].iloc[peaks[i]]
                head = df['close'].iloc[peaks[i+1]]
                right = df['close'].iloc[peaks[i+2]]
                
                # 头肩顶
                if abs(left - right) / left < 0.1 and head > left and head > right:
                    return {'identified': True, 'type': 'top', 'confidence': 0.8}
                
                # 头肩底
                if abs(left - right) / left < 0.1 and head < left and head < right:
                    return {'identified': True, 'type': 'bottom', 'confidence': 0.8}
            
            return {'identified': False, 'type': None, 'confidence': 0}
        except Exception as e:
            self.logger.error(f"识别头肩形态时出错: {str(e)}")
            return {'identified': False, 'type': None, 'confidence': 0}

    def _check_double_patterns(self, df: pd.DataFrame) -> Dict:
        """识别双重顶/底形态
        
        Args:
            df: OHLCV数据
            
        Returns:
            Dict: {
                'identified': bool,  # 是否识别到形态
                'type': str,         # 'top' 或 'bottom'
                'confidence': float  # 置信度
            }
        """
        try:
            peaks = self._find_peaks(df['close'].values)
            troughs = self._find_peaks(-df['close'].values)
            
            if len(peaks) < 2 or len(troughs) < 2:
                return {'identified': False, 'type': None, 'confidence': 0}
            
            # 检查最后两个峰值
            if len(peaks) >= 2:
                peak1 = df['close'].iloc[peaks[-2]]
                peak2 = df['close'].iloc[peaks[-1]]
                if abs(peak1 - peak2) / peak1 < 0.05:
                    return {'identified': True, 'type': 'top', 'confidence': 0.8}
            
            # 检查最后两个谷值
            if len(troughs) >= 2:
                trough1 = df['close'].iloc[troughs[-2]]
                trough2 = df['close'].iloc[troughs[-1]]
                if abs(trough1 - trough2) / trough1 < 0.05:
                    return {'identified': True, 'type': 'bottom', 'confidence': 0.8}
            
            return {'identified': False, 'type': None, 'confidence': 0}
        except Exception as e:
            self.logger.error(f"识别双重形态时出错: {str(e)}")
            return {'identified': False, 'type': None, 'confidence': 0}

    def _check_triangle_pattern(self, df: pd.DataFrame) -> Dict:
        """识别三角形整理形态
        
        Args:
            df: OHLCV数据
            
        Returns:
            Dict: {
                'identified': bool,  # 是否识别到形态
                'type': str,         # 'ascending', 'descending', 或 'symmetric'
                'confidence': float  # 置信度
            }
        """
        try:
            # 计算最高价和最低价的趋势线
            highs = df['high'].rolling(window=5).max()
            lows = df['low'].rolling(window=5).min()
            
            # 计算趋势线斜率
            high_slope = (highs.iloc[-1] - highs.iloc[-20]) / 20
            low_slope = (lows.iloc[-1] - lows.iloc[-20]) / 20
            
            # 判断三角形类型
            if abs(high_slope) < 0.001 and low_slope > 0:
                return {'identified': True, 'type': 'ascending', 'confidence': 0.7}
            elif high_slope < 0 and abs(low_slope) < 0.001:
                return {'identified': True, 'type': 'descending', 'confidence': 0.7}
            elif high_slope < 0 and low_slope > 0:
                return {'identified': True, 'type': 'symmetric', 'confidence': 0.8}
            
            return {'identified': False, 'type': None, 'confidence': 0}
        except Exception as e:
            self.logger.error(f"识别三角形形态时出错: {str(e)}")
            return {'identified': False, 'type': None, 'confidence': 0}
