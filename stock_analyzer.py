from dataclasses import dataclass
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from pathlib import Path
import logging
from typing import Dict, List, Optional
import json

@dataclass
class TechnicalPattern:
    name: str
    confidence: float
    description: str

class StockAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.setup_paths()
        self.setup_colors()

    def setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/stock_analyzer.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("stock_analyzer")

    def setup_paths(self):
        """设置路径"""
        self.results_path = Path("reports/stocks")
        self.results_path.mkdir(parents=True, exist_ok=True)

    def setup_colors(self):
        """设置颜色主题"""
        self.colors = {
            "primary": "#1a237e",
            "secondary": "#4a148c",
            "success": "#004d40",
            "warning": "#e65100",
            "danger": "#b71c1c",
            "info": "#0d47a1",
            "background": "#fafafa",
            "text": "#263238",
            "card": "#ffffff",
            "border": "#e0e0e0",
            "gradient_start": "#1a237e",
            "gradient_end": "#4a148c"
        }

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]

    def calculate_macd(self, prices: pd.Series) -> tuple:
        """计算MACD指标"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return macd.iloc[-1], signal.iloc[-1], hist.iloc[-1]

    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9) -> tuple:
        """计算KDJ指标"""
        low_min = low.rolling(window=n).min()
        high_max = high.rolling(window=n).max()
        
        rsv = (close - low_min) / (high_max - low_min) * 100
        
        k = pd.Series(index=close.index, dtype='float64')
        d = pd.Series(index=close.index, dtype='float64')
        
        k[0] = 50
        d[0] = 50
        
        for i in range(1, len(close)):
            k[i] = 2/3 * k[i-1] + 1/3 * rsv[i]
            d[i] = 2/3 * d[i-1] + 1/3 * k[i]
        
        j = 3 * k - 2 * d
        
        return k.iloc[-1], d.iloc[-1], j.iloc[-1]

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20) -> tuple:
        """计算布林带"""
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        return upper.iloc[-1], middle.iloc[-1], lower.iloc[-1]

    def identify_patterns(self, high: pd.Series, low: pd.Series, close: pd.Series) -> List[TechnicalPattern]:
        """识别价格形态"""
        patterns = []
        
        # 获取最近的数据
        recent_high = high[-5:]
        recent_low = low[-5:]
        recent_close = close[-5:]
        recent_open = (recent_high + recent_low) / 2  # 简化计算开盘价
        
        # 识别吞没形态
        if (recent_close.iloc[-2] < recent_open.iloc[-2] and
            recent_close.iloc[-1] > recent_open.iloc[-1] and
            recent_close.iloc[-1] > recent_close.iloc[-2] and
            recent_open.iloc[-1] < recent_close.iloc[-2]):
            patterns.append(TechnicalPattern(
                name="吞没形态",
                confidence=0.8,
                description="看多吞没形态"
            ))
            
        # 识别十字星
        body_sizes = abs(recent_close - recent_open)
        shadow_sizes = recent_high - recent_low
        if body_sizes.iloc[-1] < 0.1 * shadow_sizes.iloc[-1]:
            patterns.append(TechnicalPattern(
                name="十字星",
                confidence=0.6,
                description="可能出现反转"
            ))
            
        # 识别锤子线
        if (recent_close.iloc[-1] > recent_open.iloc[-1] and
            (recent_high.iloc[-1] - recent_close.iloc[-1]) < (recent_open.iloc[-1] - recent_low.iloc[-1]) * 0.3):
            patterns.append(TechnicalPattern(
                name="锤子线",
                confidence=0.7,
                description="看多信号"
            ))
            
        # 识别上吊线
        if (recent_close.iloc[-1] < recent_open.iloc[-1] and
            (recent_close.iloc[-1] - recent_low.iloc[-1]) < (recent_high.iloc[-1] - recent_open.iloc[-1]) * 0.3):
            patterns.append(TechnicalPattern(
                name="上吊线",
                confidence=0.7,
                description="看空信号"
            ))

        return patterns

    def analyze_trend(self, prices: pd.Series) -> dict:
        """分析价格趋势"""
        ma_short = prices.rolling(window=20).mean()
        ma_long = prices.rolling(window=50).mean()
        
        # 计算趋势强度
        slope = np.polyfit(range(len(prices[-20:])), prices[-20:], 1)[0]
        trend_strength = abs(slope) / prices.std()
        
        # 判断趋势方向
        if ma_short.iloc[-1] > ma_long.iloc[-1] and slope > 0:
            trend = "上升"
        elif ma_short.iloc[-1] < ma_long.iloc[-1] and slope < 0:
            trend = "下降"
        else:
            trend = "横盘"
            
        return {
            'trend': trend,
            'strength': trend_strength,
            'slope': slope,
            'ma_short': ma_short.iloc[-1],
            'ma_long': ma_long.iloc[-1]
        }

    def calculate_volume_analysis(self, volume: pd.Series) -> dict:
        """分析成交量"""
        volume_ma = volume.rolling(window=20).mean()
        volume_ratio = volume.iloc[-1] / volume_ma.iloc[-1]
        volume_trend = (volume[-5:] > volume_ma[-5:]).sum()
        
        return {
            'volume_ratio': volume_ratio,
            'volume_ma': volume_ma.iloc[-1],
            'volume_trend': volume_trend,
            'volume_increase': volume.iloc[-1] > volume.iloc[-2]
        }

    def analyze_stocks(self, symbols: List[str], names: Optional[Dict[str, str]] = None) -> List[Dict]:
        """主要分析方法"""
        results = []
        for symbol in symbols:
            try:
                name = names.get(symbol, symbol) if names else symbol
                self.logger.info(f"开始分析 {symbol}")
                
                # 获取数据
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")
                
                if hist.empty:
                    self.logger.warning(f"没有获取到 {symbol} 的数据")
                    continue
                
                # 基础计算
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                price_change = ((latest['Close'] / prev['Close']) - 1) * 100
                
                # 计算技术指标
                rsi = self.calculate_rsi(hist['Close'])
                macd, signal_line, hist_macd = self.calculate_macd(hist['Close'])
                k, d, j = self.calculate_kdj(hist['High'], hist['Low'], hist['Close'])
                upper, middle, lower = self.calculate_bollinger_bands(hist['Close'])
                bb_b = (latest['Close'] - lower) / (upper - lower)
                
                # 分析成交量
                volume_analysis = self.calculate_volume_analysis(hist['Volume'])
                
                # 分析趋势
                trend_analysis = self.analyze_trend(hist['Close'])
                
                # 识别形态
                patterns = self.identify_patterns(hist['High'], hist['Low'], hist['Close'])
                
                # 生成信号
                data = {
                    'rsi': rsi,
                    'macd': macd,
                    'macd_signal': signal_line,
                    'k': k,
                    'd': d,
                    'bb_b': bb_b,
                    'volume_analysis': volume_analysis,
                    'trend': trend_analysis,
                    'patterns': patterns
                }
                
                signal, confidence, reasons = self.generate_signal(data)
                
                # 回测分析
                backtest = self.backtest_signals(hist)
                
                # 整合结果
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'price': latest['Close'],
                    'change': price_change,
                    'technical_indicators': {
                        'rsi': rsi,
                        'macd': macd,
                        'signal_line': signal_line,
                        'hist_macd': hist_macd,
                        'k': k,
                        'd': d,
                        'j': j,
                        'bb_b': bb_b
                    },
                    'volume_analysis': volume_analysis,
                    'trend_analysis': trend_analysis,
                    'patterns': patterns,
                    'signal': signal,
                    'confidence': confidence,
                    'reasons': reasons,
                    'backtest': backtest
                })
                
                self.logger.info(f"成功分析 {symbol}")
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错: {str(e)}")
                continue
        
        return results

    def generate_signal(self, data: dict) -> tuple:
        """生成交易信号"""
        signal = "观望"
        confidence = 50
        reasons = []
        
        # RSI 信号
        if data['rsi'] < 30:
            reasons.append("RSI超卖")
            confidence += 10
        elif data['rsi'] > 70:
            reasons.append("RSI超买")
            confidence -= 10
            
        # MACD信号
        if data['macd'] > data['macd_signal']:
            reasons.append("MACD金叉")
            confidence += 10
        elif data['macd'] < data['macd_signal']:
            reasons.append("MACD死叉")
            confidence -= 10
            
        # KDJ信号
        if data['k'] < 20 and data['d'] < 20:
            reasons.append("KDJ超卖")
            confidence += 10
        elif data['k'] > 80 and data['d'] > 80:
            reasons.append("KDJ超买")
            confidence -= 10
            
        # 成交量分析
        if data['volume_analysis']['volume_ratio'] > 1.5:
            reasons.append("成交量显著放大")
            confidence += 5
            
        # 趋势分析
        if data['trend']['trend'] == "上升" and data['trend']['strength'] > 1:
            reasons.append("强势上涨趋势")
            confidence += 10
        elif data['trend']['trend'] == "下降" and data['trend']['strength'] > 1:
            reasons.append("强势下跌趋势")
            confidence -= 10
            
        # 形态分析
        for pattern in data['patterns']:
            reasons.append(f"出现{pattern.description}")
            confidence += pattern.confidence * 10
            
        # 生成最终信号
        if confidence >= 70:
            signal = "强烈买入"
        elif confidence >= 60:
            signal = "建议买入"
        elif confidence <= 30:
            signal = "强烈卖出"
        elif confidence <= 40:
            signal = "建议卖出"
            
        return signal, min(100, max(0, confidence)), reasons

    def backtest_signals(self, hist: pd.DataFrame, lookback_period: int = 60) -> dict:
        """回测历史信号表现"""
        signals = []
        performance = []
        
        for i in range(lookback_period, len(hist)):
            window = hist.iloc[i-lookback_period:i]
            current_price = hist.iloc[i]['Close']
            
            # 计算技术指标
            rsi = self.calculate_rsi(window['Close'])
            macd, signal_line, _ = self.calculate_macd(window['Close'])
            k, d, _ = self.calculate_kdj(window['High'], window['Low'], window['Close'])
            
            # 生成信号
            data = {
                'rsi': rsi,
                'macd': macd,
                'macd_signal': signal_line,
                'k': k,
                'd': d,
                'volume_analysis': self.calculate_volume_analysis(window['Volume']),
                'trend': self.analyze_trend(window['Close']),
                'patterns': self.identify_patterns(window['High'], window['Low'], window['Close'])
            }
            
            signal, confidence, _ = self.generate_signal(data)
            
            signals.append({
                'date': hist.index[i],
                'price': current_price,
                'signal': signal,
                'confidence': confidence
            })
            
            # 计算未来5天收益
            if i + 5 < len(hist):
                future_return = (hist.iloc[i+5]['Close'] - current_price) / current_price * 100
                performance.append({
                    'signal': signal,
                    'confidence': confidence,
                    'return': future_return
                })
        
        # 分析信号表现
        buy_signals = [p for p in performance if "买入" in p['signal']]
        sell_signals = [p for p in performance if "卖出" in p['signal']]
        
        return {
            'buy': {
                'count': len(buy_signals),
                'avg_return': np.mean([p['return'] for p in buy_signals]) if buy_signals else 0,
                'win_rate': sum(1 for p in buy_signals if p['return'] > 0) / len(buy_signals) if buy_signals else 0
            },
            'sell': {
                'count': len(sell_signals),
                'avg_return': np.mean([p['return'] for p in sell_signals]) if sell_signals else 0,
                'win_rate': sum(1 for p in sell_signals if p['return'] < 0) / len(sell_signals) if sell_signals else 0
            },
            'recent_signals': signals[-10:],
            'overall_accuracy': sum(1 for p in performance if 
                                  ("买入" in p['signal'] and p['return'] > 0) or 
                                  ("卖出" in p['signal'] and p['return'] < 0)) / len(performance) if performance else 0
        }

    def generate_html_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        """生成HTML分析报告"""
        timestamp = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d_%H%M')
        filename = f"stock_analysis_{timestamp}.html"
        file_path = self.results_path / filename

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Noto Sans SC', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {self.colors['background']};
                    color: {self.colors['text']};
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 40px;
                    background: linear-gradient(135deg, {self.colors['gradient_start']}, {self.colors['gradient_end']});
                    color: white;
                    border-radius: 15px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                    gap: 25px;
                }}
                .card {{
                    background: {self.colors['card']};
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    transition: all 0.3s ease;
                }}
                .card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .stock-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 2px solid {self.colors['border']};
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .stock-name {{
                    font-size: 1.5em;
                    font-weight: 700;
                    color: {self.colors['primary']};
                }}
                .price-info {{
                    text-align: right;
                }}
                .current-price {{
                    font-size: 1.8em;
                    font-weight: 700;
                    color: {self.colors['primary']};
                }}
                .price-change {{
                    font-size: 1.2em;
                    padding: 5px 10px;
                    border-radius: 5px;
                }}
                .price-change.-up {{
                    color: {self.colors['success']};
                    background: rgba(0,77,64,0.1);
                }}
                .price-change.-down {{
                    color: {self.colors['danger']};
                    background: rgba(183,28,28,0.1);
                }}
                .indicator-group {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .indicator {{
                    background: {self.colors['background']};
                    padding: 10px;
                    border-radius: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .indicator-label {{
                    color: {self.colors['text']};
                    opacity: 0.8;
                }}
                .indicator-value {{
                    font-weight: 500;
                    color: {self.colors['primary']};
                }}
                .signal-section {{
                    margin: 20px 0;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    color: white;
                }}
                .signal-strong-buy {{
                    background: {self.colors['success']};
                }}
                .signal-buy {{
                    background: {self.colors['info']};
                }}
                .signal-hold {{
                    background: {self.colors['warning']};
                }}
                .signal-sell {{
                    background: {self.colors['danger']};
                }}
                .confidence-meter {{
                    height: 6px;
                    background: {self.colors['border']};
                    border-radius: 3px;
                    margin: 15px 0;
                }}
                .confidence-value {{
                    height: 100%;
                    border-radius: 3px;
                    transition: width 0.3s ease;
                }}
                .analysis-section {{
                    margin-top: 20px;
                }}
                .analysis-title {{
                    font-size: 1.2em;
                    font-weight: 500;
                    margin-bottom: 10px;
                    color: {self.colors['primary']};
                }}
                .analysis-content {{
                    background: {self.colors['background']};
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                }}
                .pattern-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
                    border-bottom: 1px solid {self.colors['border']};
                }}
                .pattern-name {{
                    color: {self.colors['primary']};
                    font-weight: 500;
                }}
                .pattern-confidence {{
                    color: {self.colors['secondary']};
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding: 20px;
                    color: {self.colors['text']};
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <p>生成时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="grid">
        """

        for r in results:
            signal_class = (
                "signal-strong-buy" if "强烈买入" in r['signal']
                else "signal-buy" if "建议买入" in r['signal']
                else "signal-sell" if "卖出" in r['signal']
                else "signal-hold"
            )

            html_content += f"""
                    <div class="card">
                        <div class="stock-header">
                            <div class="stock-name">
                                <div>{r['symbol']}</div>
                                <div style="font-size: 0.8em; opacity: 0.8;">{r['name']}</div>
                            </div>
                            <div class="price-info">
                                <div class="current-price">${r['price']:.2f}</div>
                                <div class="price-change {'-up' if r['change'] >= 0 else '-down'}">
                                    {r['change']:+.2f}%
                                </div>
                            </div>
                        </div>

                        <div class="indicator-group">
                            <div class="indicator">
                                <span class="indicator-label">RSI</span>
                                <span class="indicator-value">{r['technical_indicators']['rsi']:.1f}</span>
                            </div>
                            <div class="indicator">
                                <span class="indicator-label">MACD</span>
                                <span class="indicator-value">{r['technical_indicators']['macd']:.3f}</span>
                            </div>
                            <div class="indicator">
                                <span class="indicator-label">KDJ-K</span>
                                <span class="indicator-value">{r['technical_indicators']['k']:.1f}</span>
                            </div>
                            <div class="indicator">
                                <span class="indicator-label">布林带位置</span>
                                <span class="indicator-value">{r['technical_indicators']['bb_b']*100:.1f}%</span>
                            </div>
                        </div>

                        <div class="signal-section {signal_class}">
                            <div style="font-size: 1.3em; font-weight: 500;">{r['signal']}</div>
                            <div style="font-size: 0.9em; margin-top: 5px;">置信度: {r['confidence']}%</div>
                        </div>

                        <div class="confidence-meter">
                            <div class="confidence-value" style="width: {r['confidence']}%; 
                                 background: {self.colors['success'] if r['confidence'] > 50 else self.colors['danger']};">
                            </div>
                        </div>

                        <div class="analysis-section">
                            <div class="analysis-title">趋势分析</div>
                            <div class="analysis-content">
                                <div>趋势: {r['trend_analysis']['trend']}</div>
                                <div>强度: {r['trend_analysis']['strength']:.2f}</div>
                            </div>

                            <div class="analysis-title">形态识别</div>
                            <div class="analysis-content">
                                {self._generate_patterns_html(r['patterns'])}
                            </div>

                            <div class="analysis-title">回测结果</div>
                            <div class="analysis-content">
                                <div>整体准确率: {r['backtest']['overall_accuracy']*100:.1f}%</div>
                                <div>买入信号胜率: {r['backtest']['buy']['win_rate']*100:.1f}%</div>
                                <div>卖出信号胜率: {r['backtest']['sell']['win_rate']*100:.1f}%</div>
                            </div>

                            <div class="analysis-title">分析依据</div>
                            <div class="analysis-content">
                                {'<br>'.join(r['reasons'])}
                            </div>
                        </div>
                    </div>
            """

        html_content += """
                </div>
                <div class="footer">
                    <p>本报告基于技术分析生成，仅供参考。投资有风险，入市需谨慎。</p>
                </div>
            </div>
        </body>
        </html>
        """

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(file_path)

    def _generate_patterns_html(self, patterns: List[TechnicalPattern]) -> str:
        """生成形态识别的HTML内容"""
        if not patterns:
            return "<div>未识别到明显形态</div>"
        
        return "".join([
            f"""
            <div class="pattern-item">
                <span class="pattern-name">{pattern.name}</span>
                <span class="pattern-confidence">置信度: {pattern.confidence*100:.0f}%</span>
            </div>
            """ for pattern in patterns
        ])

if __name__ == "__main__":
    # 创建分析器实例
    analyzer = StockAnalyzer()
    
    try:
        # 提供两个选项
        print("\n股票分析器")
        print("=" * 50)
        print("1. 输入自定义股票代码（不超过10个）")
        print("2. 从配置文件读取股票组合")
        choice = input("\n请选择操作 (1/2): ")
        
        if choice == "1":
            # 自定义输入
            print("\n请输入股票代码，每行一个，最多10个")
            print("输入空行结束")
            symbols = []
            names = {}
            
            while len(symbols) < 10:
                symbol = input().strip().upper()
                if not symbol:
                    break
                    
                name = input(f"请输入 {symbol} 的中文名称 (直接回车使用代码作为名称): ").strip()
                symbols.append(symbol)
                names[symbol] = name if name else symbol
                
            title = "自定义股票分析报告"
            
        elif choice == "2":
            # 从配置文件读取
            config_file = Path("config/watchlists.json")
            if not config_file.exists():
                # 如果配置文件不存在，创建示例文件
                config_dir = Path("config")
                config_dir.mkdir(exist_ok=True)
                
                watchlists_example = {
                    "科技股": {
                        "AAPL": "苹果公司",
                        "GOOGL": "谷歌公司",
                        "MSFT": "微软公司",
                        "AMZN": "亚马逊公司",
                        "META": "Meta公司",
                        "NVDA": "英伟达",
                        "TSLA": "特斯拉"
                    },
                    "中概股": {
                        "BABA": "阿里巴巴",
                        "PDD": "拼多多",
                        "JD": "京东",
                        "BIDU": "百度",
                        "NIO": "蔚来汽车"
                    },
                    "金融股": {
                        "JPM": "摩根大通",
                        "BAC": "美国银行",
                        "GS": "高盛集团",
                        "MS": "摩根士丹利",
                        "C": "花旗集团"
                    }
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(watchlists_example, f, ensure_ascii=False, indent=4)
                print(f"\n已创建示例配置文件：{config_file}")
                
            with open(config_file, 'r', encoding='utf-8') as f:
                watchlists = json.load(f)
                
            print("\n可用的股票组合：")
            for i, group in enumerate(watchlists.keys(), 1):
                print(f"{i}. {group} ({len(watchlists[group])}支股票)")
            print(f"{len(watchlists) + 1}. 分析所有股票")
            
            group_choice = input("\n请选择要分析的组合 (输入编号): ")
            
            if group_choice.isdigit():
                group_idx = int(group_choice)
                if group_idx <= len(watchlists):
                    # 选择特定组合
                    group_name = list(watchlists.keys())[group_idx - 1]
                    symbols = list(watchlists[group_name].keys())
                    names = watchlists[group_name]
                    title = f"{group_name}分析报告"
                else:
                    # 分析所有股票
                    symbols = []
                    names = {}
                    for group_stocks in watchlists.values():
                        symbols.extend(group_stocks.keys())
                        names.update(group_stocks)
                    title = "全市场分析报告"
        else:
            print("无效的选择")
            exit(1)
            
        # 进行分析
        print(f"\n开始分析 {len(symbols)} 支股票...")
        results = analyzer.analyze_stocks(symbols, names)
        
        # 生成报告
        report_path = analyzer.generate_html_report(results, title)
        print(f"\n分析完成！报告已生成：{report_path}")
        
    except Exception as e:
        print(f"程序运行出错：{str(e)}")
