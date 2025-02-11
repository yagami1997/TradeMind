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
import warnings
import webbrowser
import os

warnings.filterwarnings('ignore', category=RuntimeWarning)

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
        self.results_path = Path("reports/stocks")
        self.results_path.mkdir(parents=True, exist_ok=True)

    def setup_colors(self):
        self.colors = {
            "primary": "#1976D2",         # 主色调：蓝色
            "secondary": "#0D47A1",       # 次要色：深蓝色
            "success": "#2E7D32",         # 成功色：深绿色
            "warning": "#F57F17",         # 警告色：金黄色
            "danger": "#C62828",          # 危险色：深红色
            "info": "#0288D1",            # 信息色：浅蓝色
            "background": "#FFFFFF",       # 背景色：白色
            "text": "#212121",            # 文字色：深灰色
            "card": "#FFFFFF",            # 卡片色：白色
            "border": "#E0E0E0",          # 边框色：浅灰色
            "gradient_start": "#1976D2",   # 渐变开始：蓝色
            "gradient_end": "#0D47A1",     # 渐变结束：深蓝色
            "strong_buy": "#00796B",       # 强烈买入：深青绿色
            "buy": "#26A69A",             # 买入：青绿色
            "strong_sell": "#D32F2F",      # 强烈卖出：深红色
            "sell": "#EF5350",            # 卖出：红色
            "neutral": "#FFA000",          # 观望：琥珀色
            "name_tag": "#E3F2FD",        # 股票名称标签：极浅蓝色
            "highlight": "#E3F2FD",        # 高亮背景：极浅蓝色
            "tag_text": "#FFFFFF",         # 标签文字：白色
            "advice_bg": "#FAFAFA",        # 建议背景：浅灰色
            "card_shadow": "rgba(0,0,0,0.1)", # 卡片阴影
            "card_border": "#E0E0E0"       # 卡片边框：浅灰色
        }

    def calculate_macd(self, prices: pd.Series) -> tuple:
        prices = pd.to_numeric(prices, errors='coerce')
        exp1 = prices.ewm(span=12, adjust=False, min_periods=12).mean()
        exp2 = prices.ewm(span=26, adjust=False, min_periods=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
        hist = macd - signal
        macd = macd.fillna(0)
        signal = signal.fillna(0)
        hist = hist.fillna(0)
        return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])

    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> tuple:
        high = pd.to_numeric(high, errors='coerce')
        low = pd.to_numeric(low, errors='coerce')
        close = pd.to_numeric(close, errors='coerce')
        
        low_list = low.rolling(window=n, min_periods=1).min()
        high_list = high.rolling(window=n, min_periods=1).max()
        rsv = pd.Series(np.zeros(len(close)), index=close.index, dtype='float64')
        
        denominator = high_list - low_list
        rsv = np.where(denominator != 0, 
                      (close - low_list) * 100 / denominator,
                      0)
        
        k = pd.Series(np.zeros(len(close)), index=close.index, dtype='float64')
        k[0] = 50
        for i in range(1, len(close)):
            k[i] = (m1 - 1) * k[i-1] / m1 + rsv[i] / m1
        
        d = pd.Series(np.zeros(len(close)), index=close.index, dtype='float64')
        d[0] = 50
        for i in range(1, len(close)):
            d[i] = (m2 - 1) * d[i-1] / m2 + k[i] / m2
        
        j = 3 * k - 2 * d
        
        k = k.clip(0, 100)
        d = d.clip(0, 100)
        j = j.clip(0, 100)
        
        k = k.fillna(50)
        d = d.fillna(50)
        j = j.fillna(50)
        
        return float(k.iloc[-1]), float(d.iloc[-1]), float(j.iloc[-1])

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return float(100 - (100 / (1 + rs)).iloc[-1])

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20) -> tuple:
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        return float(upper.iloc[-1]), float(middle.iloc[-1]), float(lower.iloc[-1])

    def analyze_stocks(self, symbols: List[str], names: Optional[Dict[str, str]] = None) -> List[Dict]:
        results = []
        total = len(symbols)
        
        for i, symbol in enumerate(symbols, 1):
            try:
                name = names.get(symbol, symbol) if names else symbol
                self.logger.info(f"正在分析 {name} ({symbol}) - {i}/{total}")
                
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1y")
                
                if hist.empty:
                    self.logger.warning(f"无法获取 {symbol} 的历史数据")
                    continue
                
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((current_price - prev_price) / prev_price) * 100
                
                # 计算技术指标
                rsi = self.calculate_rsi(hist['Close'])
                macd, signal, hist_macd = self.calculate_macd(hist['Close'])
                k, d, j = self.calculate_kdj(hist['High'], hist['Low'], hist['Close'])
                bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(hist['Close'])
                
                # 生成交易建议
                advice = self.generate_trading_advice({
                    'rsi': rsi,
                    'macd': {'macd': macd, 'signal': signal, 'hist': hist_macd},
                    'kdj': {'k': k, 'd': d, 'j': j},
                    'bollinger': {'upper': bb_upper, 'middle': bb_middle, 'lower': bb_lower}
                }, current_price)
                
                # 执行回测
                backtest_results = self.backtest_strategy(hist)
                
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'price': current_price,
                    'change': change,
                    'indicators': {
                        'rsi': rsi,
                        'macd': {'macd': macd, 'signal': signal, 'hist': hist_macd},
                        'kdj': {'k': k, 'd': d, 'j': j},
                        'bollinger': {'upper': bb_upper, 'middle': bb_middle, 'lower': bb_lower}
                    },
                    'advice': advice,
                    'backtest': backtest_results
                })
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错: {str(e)}", exc_info=True)
                continue
        
        return results
    
    def generate_trading_advice(self, indicators: Dict, price: float) -> Dict:
        rsi = indicators['rsi']
        macd = indicators['macd']['macd']
        macd_hist = indicators['macd']['hist']
        k = indicators['kdj']['k']
        j = indicators['kdj']['j']
        bb_upper = indicators['bollinger']['upper']
        bb_middle = indicators['bollinger']['middle']
        bb_lower = indicators['bollinger']['lower']
        
        signals = []
        confidence = 0
        
        # RSI信号
        if rsi < 30:
            signals.append("RSI超卖")
            confidence += 20
        elif rsi > 70:
            signals.append("RSI超买")
            confidence -= 20
        
        # KDJ信号
        if k < 20:
            signals.append("KDJ超卖")
            confidence += 20
        elif k > 80:
            signals.append("KDJ超买")
            confidence -= 20
        
        # 布林带信号
        if price <= bb_lower:
            signals.append("触及布林带下轨")
            confidence += 20
        elif price >= bb_upper:
            signals.append("触及布林带上轨")
            confidence -= 20
        
        # MACD信号
        if macd_hist > 0 and macd > 0:
            signals.append("MACD金叉")
            confidence += 15
        elif macd_hist < 0 and macd < 0:
            signals.append("MACD死叉")
            confidence -= 15
        
        # 根据综合信号确定建议和颜色
        if confidence >= 40:
            advice = "强烈买入"
            color = self.colors['strong_buy']
        elif confidence >= 20:
            advice = "建议买入"
            color = self.colors['buy']
        elif confidence <= -40:
            advice = "强烈卖出"
            color = self.colors['strong_sell']
        elif confidence <= -20:
            advice = "建议卖出"
            color = self.colors['sell']
        else:
            advice = "观望"
            color = self.colors['neutral']
        
        return {
            'advice': advice,
            'confidence': abs(confidence),
            'signals': signals,
            'color': color
        }

    def backtest_strategy(self, hist: pd.DataFrame) -> dict:
        trades = []
        positions = []
        last_position = 0
        entry_price = 0
        
        closes = hist['Close']
        highs = hist['High']
        lows = hist['Low']
        
        # RSI计算
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        
        # 布林带计算
        bb_middle = closes.rolling(window=20).mean()
        bb_std = closes.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        # KDJ计算
        low_list = lows.rolling(window=9, min_periods=1).min()
        high_list = highs.rolling(window=9, min_periods=1).max()
        rsv = (closes - low_list) / (high_list - low_list) * 100
        k_series = pd.Series(index=closes.index, dtype='float64')
        d_series = pd.Series(index=closes.index, dtype='float64')
        
        k_series.iloc[0] = 50
        d_series.iloc[0] = 50
        
        for i in range(1, len(closes)):
            k_series.iloc[i] = 2/3 * k_series.iloc[i-1] + 1/3 * rsv.iloc[i]
            d_series.iloc[i] = 2/3 * d_series.iloc[i-1] + 1/3 * k_series.iloc[i]
        
        j_series = 3 * k_series - 2 * d_series
        
        # 生成交易信号
        for i in range(20, len(hist)):
            current_price = closes.iloc[i]
            current_rsi = rsi_series.iloc[i]
            current_k = k_series.iloc[i]
            current_bb_upper = bb_upper.iloc[i]
            current_bb_lower = bb_lower.iloc[i]
            
            # 买入信号：RSI超卖 + 价格触及布林带下轨 + KDJ超卖
            buy_signal = (
                current_rsi < 30 and 
                current_price <= current_bb_lower * 1.01 and
                current_k < 20
            )
            
            # 卖出信号：RSI超买 + 价格触及布林带上轨 + KDJ超买
            sell_signal = (
                current_rsi > 70 and 
                current_price >= current_bb_upper * 0.99 and
                current_k > 80
            )
            
            # 交易执行
            if buy_signal and last_position <= 0:
                entry_price = current_price
                last_position = 1
                positions.append(1)
            elif sell_signal and last_position >= 0:
                if last_position == 1:
                    profit = (current_price - entry_price) / entry_price * 100
                    trades.append(profit)
                entry_price = current_price
                last_position = -1
                positions.append(-1)
        
        # 计算回测结果
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        
        winning_trades = sum(1 for t in trades if t > 0)
        total_trades = len(trades)
        
        return {
            'total_trades': total_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'avg_profit': sum(trades) / len(trades) if trades else 0,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades
        }
    
    def generate_html_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        timestamp = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')
        report_file = self.results_path / f"stock_analysis_{timestamp}.html"
        
        # 生成每个股票的卡片HTML
        stock_cards = []
        for result in results:
            card = f"""
                <div class="stock-card">
                    <div class="stock-header" style="background-color: {result['advice']['color']}">
                        <div class="stock-name">{result['name']} ({result['symbol']})</div>
                    </div>
                    <div class="stock-price">
                        ${result['price']:.2f}
                        <span class="price-change {'positive' if result['change'] > 0 else 'negative'}">
                            {result['change']:+.2f}%
                        </span>
                    </div>
                    <div class="indicators-grid">
                        <div class="indicator-card">
                            <div class="indicator-title">RSI</div>
                            <div class="indicator-value">{result['indicators']['rsi']:.2f}</div>
                        </div>
                        <div class="indicator-card">
                            <div class="indicator-title">MACD</div>
                            <div class="indicator-value">
                                <div>MACD: {result['indicators']['macd']['macd']:.3f}</div>
                                <div>Signal: {result['indicators']['macd']['signal']:.3f}</div>
                                <div>Hist: {result['indicators']['macd']['hist']:.3f}</div>
                            </div>
                        </div>
                        <div class="indicator-card">
                            <div class="indicator-title">KDJ</div>
                            <div class="indicator-value">
                                <div>K: {result['indicators']['kdj']['k']:.2f}</div>
                                <div>D: {result['indicators']['kdj']['d']:.2f}</div>
                                <div>J: {result['indicators']['kdj']['j']:.2f}</div>
                            </div>
                        </div>
                        <div class="indicator-card">
                            <div class="indicator-title">布林带</div>
                            <div class="indicator-value">
                                <div>上轨: {result['indicators']['bollinger']['upper']:.2f}</div>
                                <div>中轨: {result['indicators']['bollinger']['middle']:.2f}</div>
                                <div>下轨: {result['indicators']['bollinger']['lower']:.2f}</div>
                            </div>
                        </div>
                    </div>
                    <div class="advice-section">
                        <div class="advice-tag" style="background-color: {result['advice']['color']}">
                            {result['advice']['advice']} (信心指数: {result['advice']['confidence']}%)
                        </div>
                        <div class="signals-list">
                            {' '.join([f'<span class="signal-tag">{signal}</span>' for signal in result['advice']['signals']])}
                        </div>
                    </div>
                    <div class="backtest-section">
                        <div class="backtest-title">回测结果</div>
                        <div class="backtest-grid">
                            <div class="backtest-item">
                                <div class="backtest-value">{result['backtest']['total_trades']}</div>
                                <div class="backtest-label">总交易次数</div>
                            </div>
                            <div class="backtest-item">
                                <div class="backtest-value">{result['backtest']['win_rate']:.1f}%</div>
                                <div class="backtest-label">胜率</div>
                            </div>
                            <div class="backtest-item">
                                <div class="backtest-value">{result['backtest']['avg_profit']:.2f}%</div>
                                <div class="backtest-label">平均收益</div>
                            </div>
                            <div class="backtest-item">
                                <div class="backtest-value">{result['backtest']['winning_trades']}/{result['backtest']['losing_trades']}</div>
                                <div class="backtest-label">盈/亏次数</div>
                            </div>
                        </div>
                    </div>
                </div>
            """
            stock_cards.append(card)

        # 生成完整的HTML文档
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                    color: {self.colors['text']};
                    line-height: 1.6;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: #f0f7fa;  /* 添加这行，设置容器背景为浅青蓝色 */
                    padding: 30px;         /* 添加内边距 */
                    border-radius: 15px;   /* 添加圆角 */
                    box-shadow: 0 0 20px rgba(0,0,0,0.05);  /* 添加轻微阴影 */
                }}
                
                .header {{
                    background: linear-gradient(135deg, {self.colors['gradient_start']}, {self.colors['gradient_end']});
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px {self.colors['card_shadow']};
                    text-align: center;
                }}
                
                .header h1 {{
                    margin: 0;
                    font-size: 36px;
                    font-weight: 700;
                }}
                
                .timestamp {{
                    font-size: 18px;
                    opacity: 0.9;
                    margin-top: 10px;
                    font-weight: 500;
                }}
                
                .stock-card {{
                    background: #f5f5f5;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px {self.colors['card_shadow']};
                    border: 1px solid {self.colors['card_border']};
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                }}
                
                .stock-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px {self.colors['card_shadow']};
                }}
                
                .stock-header {{
                    padding: 15px 20px;
                    color: white;
                    font-weight: 500;
                    text-align: center;
                }}
                
                .stock-name {{
                    font-size: 20px;
                    font-weight: 600;
                }}
                
                .stock-price {{
                    font-size: 24px;
                    padding: 15px 20px;
                    border-bottom: 1px solid {self.colors['border']};
                    text-align: center;
                    font-weight: 600;
                }}
                
                .price-change {{
                    font-size: 18px;
                    margin-left: 10px;
                    font-weight: 500;
                }}
                
                .price-change.positive {{
                    color: {self.colors['success']};
                }}
                
                .price-change.negative {{
                    color: {self.colors['danger']};
                }}
                
                .indicators-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    padding: 20px;
                    background-color: {self.colors['background']};
                }}
                
                .indicator-card {{
                    background-color: {self.colors['highlight']};
                    padding: 15px;
                    border-radius: 8px;
                }}
                
                .indicator-title {{
                    font-weight: 600;
                    margin-bottom: 10px;
                    color: {self.colors['secondary']};
                    text-align: center;
                }}
                
                .indicator-value {{
                    font-size: 16px;
                    text-align: center;
                }}
                
                .advice-section {{
                    padding: 20px;
                    background-color: {self.colors['advice_bg']};
                    text-align: center;
                }}
                
                .advice-tag {{
                    display: inline-block;
                    padding: 10px 20px;
                    border-radius: 20px;
                    color: white;
                    font-weight: 600;
                    margin-bottom: 10px;
                    font-size: 18px;
                }}
                
                .signals-list {{
                    margin-top: 10px;
                }}
                
                .signal-tag {{
                    display: inline-block;
                    padding: 5px 10px;
                    background-color: {self.colors['info']};
                    color: white;
                    border-radius: 15px;
                    font-size: 14px;
                    margin: 3px;
                }}
                
                .backtest-section {{
                    padding: 20px;
                    background-color: white;
                }}
                
                .backtest-title {{
                    font-weight: 600;
                    margin-bottom: 15px;
                    color: {self.colors['secondary']};
                    text-align: center;
                    font-size: 18px;
                }}
                
                .backtest-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                }}
                
                .backtest-item {{
                    text-align: center;
                    padding: 10px;
                    background-color: {self.colors['highlight']};
                    border-radius: 8px;
                }}
                
                .backtest-value {{
                    font-size: 20px;
                    font-weight: 600;
                    color: {self.colors['secondary']};
                }}
                
                .backtest-label {{
                    font-size: 14px;
                    color: {self.colors['text']};
                    margin-top: 5px;
                }}
                
                .manual-section {{
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    margin-top: 40px;
                    box-shadow: 0 2px 4px {self.colors['card_shadow']};
                }}
                
                .manual-section h2 {{
                    color: {self.colors['secondary']};
                    margin-top: 0;
                    margin-bottom: 20px;
                    font-size: 24px;
                    text-align: center;
                    font-weight: 700;
                }}
                
                .manual-section h3 {{
                    color: {self.colors['primary']};
                    margin-top: 25px;
                    margin-bottom: 15px;
                    font-size: 20px;
                    font-weight: 600;
                }}
                
                .manual-content {{
                    background: {self.colors['highlight']};
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                
                .manual-content h4 {{
                    color: {self.colors['secondary']};
                    margin-top: 15px;
                    margin-bottom: 10px;
                    font-size: 18px;
                }}
                
                .manual-content p {{
                    margin: 10px 0;
                    line-height: 1.6;
                }}
                
                .manual-content ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                
                .manual-content li {{
                    margin: 5px 0;
                }}
                
                .footer-quote {{
                    text-align: center;
                    margin-top: 40px;
                    color: {self.colors['secondary']};
                    font-style: italic;
                    padding: 20px;
                }}
                
                .footer-quote p {{
                    margin: 5px 0;
                    font-size: 16px;
                }}
                
                .highlight {{
                    font-weight: 500;
                    color: {self.colors['primary']};
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <div class="timestamp">生成时间：{datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                
                {''.join(stock_cards)}
                
                <div class="manual-section">
                    <h2>技术分析说明手册</h2>
                    
                    <div class="manual-content">
                        <h3>技术指标解释</h3>
                        
                        <h4>RSI（相对强弱指标）</h4>
                        <p>衡量价格动量的技术指标，取值范围0-100：</p>
                        <ul>
                            <li>RSI > 70：市场可能处于超买状态，股价可能回落</li>
                            <li>RSI < 30：市场可能处于超卖状态，股价可能反弹</li>
                            <li>计算周期：14天</li>
                            <li>参考意义：中短期买卖信号，但需要结合其他指标</li>
                        </ul>

                        <h4>MACD（移动平均线趋同散度）</h4>
                        <p>反映价格趋势变化和动量的指标：</p>
                        <ul>
                            <li>MACD线：12日EMA - 26日EMA</li>
                            <li>Signal线：MACD的9日EMA</li>
                            <li>Histogram：MACD线 - Signal线</li>
                            <li>金叉（买入信号）：MACD线从下向上穿越Signal线</li>
                            <li>死叉（卖出信号）：MACD线从上向下穿越Signal线</li>
                        </ul>

                        <h4>KDJ指标</h4>
                        <p>随机指标的改良版，反映价格走势与超买超卖：</p>
                        <ul>
                            <li>K值：当前价格在近期价格范围内的相对位置</li>
                            <li>D值：K值的移动平均</li>
                            <li>J值：强化反应超买超卖的辅助线</li>
                            <li>K值 > 80：可能超买</li>
                            <li>K值 < 20：可能超卖</li>
                            <li>计算参数：9天周期</li>
                        </ul>

                        <h4>布林带</h4>
                        <p>反映价格波动性的指标，由三条线组成：</p>
                        <ul>
                            <li>中轨：20日移动平均线，反映价格中期趋势</li>
                            <li>上轨：中轨 + 2倍标准差，代表压力位</li>
                            <li>下轨：中轨 - 2倍标准差，代表支撑位</li>
                            <li>价格触及上轨：可能超买</li>
                            <li>价格触及下轨：可能超卖</li>
                        </ul>
                    </div>

                    <div class="manual-content">
                        <h3>交易策略说明</h3>
                        
                        <h4>买入条件（需同时满足）：</h4>
                        <ul>
                            <li>RSI < 30（超卖）</li>
                            <li>价格接近布林带下轨（允许1%误差）</li>
                            <li>KDJ的K值 < 20（超卖）</li>
                            <li>MACD金叉形成或即将形成</li>
                        </ul>

                        <h4>卖出条件（需同时满足）：</h4>
                        <ul>
                            <li>RSI > 70（超买）</li>
                            <li>价格接近布林带上轨（允许1%误差）</li>
                            <li>KDJ的K值 > 80（超买）</li>
                            <li>MACD死叉形成或即将形成</li>
                        </ul>

                        <h4>信心指数说明：</h4>
                        <ul>
                            <li>40%以上：强烈买入/卖出信号</li>
                            <li>20%-40%：建议买入/卖出信号</li>
                            <li>20%以下：观望信号</li>
                        </ul>
                    </div>

                    <div class="manual-content">
                        <h3>回测指标说明</h3>
                        
                        <h4>回测参数：</h4>
                        <ul>
                            <li>回测周期：过去一年（约252个交易日）</li>
                            <li>交易成本：未计入交易费用和滑点</li>
                            <li>持仓时间：根据信号产生持有，直到反向信号出现</li>
                        </ul>

                        <h4>回测指标解释：</h4>
                        <ul>
                            <li><strong>总交易次数</strong>：策略在回测期间产生的完整交易次数（买入+卖出）</li>
                            <li><strong>胜率</strong>：盈利交易占总交易的百分比</li>
                            <li><strong>平均收益</strong>：所有交易的平均收益率（未计年化）</li>
                            <li><strong>盈亏次数</strong>：分别显示盈利交易次数和亏损交易次数</li>
                        </ul>

                        <p class="highlight" style="margin-top: 20px;">
                            注意事项：<br>
                            1. 本策略适合震荡市场，在单边趋势市场中可能表现欠佳<br>
                            2. 建议将此分析作为决策参考之一，结合其他分析方法和市场情况综合判断<br>
                            3. 市场有风险，投资需谨慎，修行在个人！
                        </p>
                    </div>
                </div>
                
                <div class="footer-quote">
                    <p>In this cybernetic realm, we shall ultimately ascend to digital rebirth</p>
                    <p class="highlight">Long live the Free Software Movement!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_file)

if __name__ == "__main__":
    try:
        analyzer = StockAnalyzer()
        
        print("\n📊 股票分析工具")
        print("\n请选择分析模式：")
        print("1. 手动输入股票代码")
        print("2. 从配置文件加载股票组合")
        
        choice = input("\n请输入选项编号 (1 或 2): ")
        
        if choice == "1":
            print("\n请输入股票代码（每行一个，输入空行结束）：")
            print("例如：AAPL")
            
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
            config_file = Path("config/watchlists.json")
            if not config_file.exists():
                config_dir = Path("config")
                config_dir.mkdir(exist_ok=True)
                
                watchlists_example = {
                    "贵金属": {
                        "GLD": "黄金ETF-SPDR",
                        "GC=F": "黄金期货",
                        "IAU": "黄金ETF-iShares"
                    },
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
                    }
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(watchlists_example, f, ensure_ascii=False, indent=4)
                print(f"\n✨ 已创建示例配置文件：{config_file}")
                
            with open(config_file, 'r', encoding='utf-8') as f:
                watchlists = json.load(f)
                
            print("\n📁 可用的股票组合：")
            for i, group in enumerate(watchlists.keys(), 1):
                print(f"{i}. {group} ({len(watchlists[group])}支股票)")
            print(f"{len(watchlists) + 1}. 分析所有股票")
            
            group_choice = input("\n请选择要分析的组合 (输入编号): ")
            
            if group_choice.isdigit():
                group_idx = int(group_choice)
                if group_idx <= len(watchlists):
                    group_name = list(watchlists.keys())[group_idx - 1]
                    symbols = list(watchlists[group_name].keys())
                    names = watchlists[group_name]
                    title = f"{group_name}分析报告"
                elif group_idx == len(watchlists) + 1:
                    symbols = []
                    names = {}
                    for group_stocks in watchlists.values():
                        symbols.extend(group_stocks.keys())
                        names.update(group_stocks)
                    title = "全市场分析报告"
                else:
                    print("❌ 无效的选择")
                    exit(1)
            else:
                print("❌ 无效的输入")
                exit(1)
        else:
            print("❌ 无效的选择")
            exit(1)
            
        print(f"\n🔍 开始分析 {len(symbols)} 支股票...")
        results = analyzer.analyze_stocks(symbols, names)
        
        if results:
            report_path = analyzer.generate_html_report(results, title)
            abs_path = os.path.abspath(report_path)
            
            print(f"\n✨ 分析完成！报告已生成：")
            print(f"📊 报告路径：{abs_path}")
            
            try:
                print("\n🌐 正在尝试自动打开报告...")
                webbrowser.open(f'file://{abs_path}')
                print("✅ 报告已在默认浏览器中打开")
            except Exception as e:
                print(f"⚠️ 无法自动打开报告：{str(e)}")
                print("请手动打开上述路径查看报告")
            
            print("\n📊 简要分析结果：")
            for result in results:
                print(f"\n{result['name']} ({result['symbol']}):")
                print(f"价格: ${result['price']:.2f} ({result['change']:+.2f}%)")
                print(f"RSI: {result['indicators']['rsi']:.2f}")
                print(f"MACD: {result['indicators']['macd']['macd']:.3f}")
                print(f"KDJ: K={result['indicators']['kdj']['k']:.2f}, D={result['indicators']['kdj']['d']:.2f}, J={result['indicators']['kdj']['j']:.2f}")
                print(f"交易建议: {result['advice']['advice']} (信心指数: {result['advice']['confidence']}%)")
                print(f"回测胜率: {result['backtest']['win_rate']:.1f}% (总交易: {result['backtest']['total_trades']}次)")
        else:
            print("\n❌ 没有产生任何分析结果")
        
    except Exception as e:
        print(f"\n❌ 程序运行出错：{str(e)}")
        logging.error(f"程序异常：{str(e)}", exc_info=True)

