from dataclasses import dataclass
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import json
import warnings
import webbrowser
import os
import sys
from tqdm import tqdm
import time

warnings.filterwarnings('ignore', category=Warning)
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
            "primary": "#1976D2",
            "secondary": "#0D47A1",
            "success": "#2E7D32",
            "warning": "#F57F17",
            "danger": "#C62828",
            "info": "#0288D1",
            "background": "#FFFFFF",
            "text": "#212121",
            "card": "#FFFFFF",
            "border": "#E0E0E0",
            "gradient_start": "#1976D2",
            "gradient_end": "#0D47A1",
            "strong_buy": "#00796B",
            "buy": "#26A69A",
            "strong_sell": "#D32F2F",
            "sell": "#EF5350",
            "neutral": "#FFA000"
        }

    def identify_candlestick_patterns(self, data: pd.DataFrame) -> List[TechnicalPattern]:
        patterns = []
        
        if len(data) < 3:
            return patterns
        
        # 获取最近的K线数据
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        prev2 = data.iloc[-3]
        
        open_price = latest['Open']
        close = latest['Close']
        high = latest['High']
        low = latest['Low']
        
        body = abs(open_price - close)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_length = high - low
        
        # 放宽判断条件
        # 十字星形态
        if body <= total_length * 0.2:  # 放宽比例
            patterns.append(TechnicalPattern(
                name="十字星",
                confidence=75,
                description="开盘价和收盘价接近，表示市场犹豫不决"
            ))
        
        # 锤子线
        if (lower_shadow > body * 1.2) and (upper_shadow < body * 0.4):  # 放宽条件
            patterns.append(TechnicalPattern(
                name="锤子线",
                confidence=70,
                description="下影线较长，可能预示着底部反转"
            ))
        
        # 吊颈线
        if (upper_shadow > body * 1.2) and (lower_shadow < body * 0.4):  # 放宽条件
            patterns.append(TechnicalPattern(
                name="吊颈线",
                confidence=70,
                description="上影线较长，可能预示着顶部反转"
            ))
        
        return patterns

    def calculate_macd(self, prices: pd.Series) -> tuple:
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])

    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9) -> tuple:
        low_list = low.rolling(window=n).min()
        high_list = high.rolling(window=n).max()
        rsv = (close - low_list) / (high_list - low_list) * 100
        k = pd.Series(0.0, index=close.index)
        d = pd.Series(0.0, index=close.index)
        k.iloc[n-1] = 50.0
        d.iloc[n-1] = 50.0
        
        for i in range(n, len(close)):
            k.iloc[i] = 2/3 * k.iloc[i-1] + 1/3 * rsv.iloc[i]
            d.iloc[i] = 2/3 * d.iloc[i-1] + 1/3 * k.iloc[i]
        j = 3 * k - 2 * d
        
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


    def generate_trading_advice(self, indicators: Dict, current_price: float) -> Dict:
        signals = []
        confidence = 50
        
        # RSI分析
        rsi = indicators['rsi']
        if rsi < 30:
            signals.append("RSI超卖")
            confidence += 10
        elif rsi > 70:
            signals.append("RSI超买")
            confidence -= 10
            
        # MACD分析
        macd = indicators['macd']
        if macd['hist'] > 0 and abs(macd['hist']) > abs(macd['macd']) * 0.1:
            signals.append("MACD金叉")
            confidence += 10
        elif macd['hist'] < 0 and abs(macd['hist']) > abs(macd['macd']) * 0.1:
            signals.append("MACD死叉")
            confidence -= 10
            
        # KDJ分析
        kdj = indicators['kdj']
        if kdj['k'] < 20 and kdj['k'] > kdj['d']:
            signals.append("KDJ金叉")
            confidence += 10
        elif kdj['k'] > 80 and kdj['k'] < kdj['d']:
            signals.append("KDJ死叉")
            confidence -= 10
            
        # 布林带分析
        bb = indicators['bollinger']
        if current_price < bb['lower']:
            signals.append("突破布林下轨")
            confidence += 10
        elif current_price > bb['upper']:
            signals.append("突破布林上轨")
            confidence -= 10
            
        # 根据综合得分给出建议
        if confidence >= 70:
            advice = "强烈买入"
            color = self.colors['strong_buy']
        elif confidence >= 60:
            advice = "建议买入"
            color = self.colors['buy']
        elif confidence <= 30:
            advice = "强烈卖出"
            color = self.colors['strong_sell']
        elif confidence <= 40:
            advice = "建议卖出"
            color = self.colors['sell']
        else:
            advice = "观望"
            color = self.colors['neutral']
            
        return {
            'advice': advice,
            'confidence': confidence,
            'signals': signals,
            'color': color
        }

    def backtest_strategy(self, data: pd.DataFrame) -> Dict:
        if len(data) < 30:  # 确保有足够的数据进行回测
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'max_profit': 0,
                'max_loss': 0
            }
            
        close = data['Close'].values
        trades = []
        position = 0  # -1: 空仓, 0: 无仓位, 1: 多仓
        entry_price = 0
        
        for i in range(26, len(close)):
            price_window = pd.Series(close[:i+1])
            current_price = close[i]
            
            # 计算技术指标
            rsi = self.calculate_rsi(price_window)
            macd, signal, hist = self.calculate_macd(price_window)
            
            # 交易信号
            buy_signal = (rsi < 30) or (hist > 0)
            sell_signal = (rsi > 70) or (hist < 0)
            
            # 交易逻辑
            if position == 0:  # 无仓位
                if buy_signal:
                    position = 1
                    entry_price = current_price
                elif sell_signal:
                    position = -1
                    entry_price = current_price
            elif position == 1:  # 持有多仓
                if sell_signal:
                    profit = ((current_price - entry_price) / entry_price) * 100
                    trades.append(profit)
                    position = 0
            elif position == -1:  # 持有空仓
                if buy_signal:
                    profit = ((entry_price - current_price) / entry_price) * 100
                    trades.append(profit)
                    position = 0
        
        # 计算回测结果
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'max_profit': 0,
                'max_loss': 0
            }
            
        win_trades = len([t for t in trades if t > 0])
        
        return {
            'total_trades': len(trades),
            'win_rate': (win_trades / len(trades)) * 100,
            'avg_profit': sum(trades) / len(trades),
            'max_profit': max(trades),
            'max_loss': min(trades)
        }
    
    def analyze_stocks(self, symbols: List[str], names: Dict[str, str]) -> List[Dict]:
        results = []
        total = len(symbols)
        print("\n开始技术分析...")
        
        for index, symbol in enumerate(symbols, 1):
            try:
                print(f"\n[{index}/{total} - {index/total*100:.1f}%] 分析: {names.get(symbol, symbol)} ({symbol})")
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1y")
                
                if hist.empty:
                    print(f"⚠️ 无法获取 {symbol} 的数据，跳过")
                    continue
                
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                print("计算技术指标...")
                rsi = self.calculate_rsi(hist['Close'])
                macd, signal, hist_macd = self.calculate_macd(hist['Close'])
                k, d, j = self.calculate_kdj(hist['High'], hist['Low'], hist['Close'])
                bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(hist['Close'])
                
                print("分析K线形态...")
                patterns = self.identify_candlestick_patterns(hist.tail(3))
                
                indicators = {
                    'rsi': rsi,
                    'macd': {'macd': macd, 'signal': signal, 'hist': hist_macd},
                    'kdj': {'k': k, 'd': d, 'j': j},
                    'bollinger': {'upper': bb_upper, 'middle': bb_middle, 'lower': bb_lower}
                }
                
                print("生成交易建议...")
                advice = self.generate_trading_advice(indicators, current_price)
                
                print("执行策略回测...")
                backtest_results = self.backtest_strategy(hist)
                
                results.append({
                    'symbol': symbol,
                    'name': names.get(symbol, symbol),
                    'price': current_price,
                    'change': price_change,
                    'indicators': indicators,
                    'patterns': patterns,
                    'advice': advice,
                    'backtest': backtest_results
                })
                
                print(f"✅ {symbol} 分析完成")
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错", exc_info=True)
                print(f"❌ {symbol} 分析失败: {str(e)}")
                continue
        
        return results

    def generate_html_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        timestamp = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')
        report_file = self.results_path / f"stock_analysis_{timestamp}.html"
        
        stock_cards = []
        for result in results:
            # 生成形态分析HTML
            patterns_html = ""
            if result.get('patterns'):
                patterns_html = f"""
                    <div style="padding: 10px; background: #f8f9fa; margin: 5px 0; border-radius: 4px;">
                        <div style="font-weight: bold; color: #333; margin-bottom: 5px;">K线形态</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                            {''.join([
                                f'<div style="background: {self.colors["info"]}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;" title="{p.description}">'
                                f'{p.name} ({p.confidence}%)</div>'
                                for p in result['patterns']
                            ])}
                        </div>
                    </div>
                """

            card = f"""
                <div class="stock-card">
                    <div class="stock-header" style="background-color: {result['advice']['color']}">
                        <div class="stock-name">{result['name']} ({result['symbol']})</div>
                        <div class="stock-price">${result['price']:.2f}
                            <span class="price-change {'positive' if result['change'] > 0 else 'negative'}">
                                {result['change']:+.2f}%
                            </span>
                        </div>
                    </div>
                    
                    <div class="indicators-section">
                        <div class="indicator-row">
                            <span class="indicator-label">RSI</span>
                            <span class="indicator-value">{result['indicators']['rsi']:.1f}</span>
                        </div>
                        <div class="indicator-row">
                            <span class="indicator-label">KDJ</span>
                            <span class="indicator-value">K:{result['indicators']['kdj']['k']:.1f} 
                            D:{result['indicators']['kdj']['d']:.1f} 
                            J:{result['indicators']['kdj']['j']:.1f}</span>
                        </div>
                        <div class="indicator-row">
                            <span class="indicator-label">MACD</span>
                            <span class="indicator-value">{result['indicators']['macd']['hist']:.3f}</span>
                        </div>
                        <div class="indicator-row">
                            <span class="indicator-label">布林带</span>
                            <span class="indicator-value">
                                U:{result['indicators']['bollinger']['upper']:.1f}
                                M:{result['indicators']['bollinger']['middle']:.1f}
                                L:{result['indicators']['bollinger']['lower']:.1f}
                            </span>
                        </div>
                    </div>

                   <!-- ... previous card content ... -->
                    
                    <div style="padding: 8px; text-align: center;">
                        {' '.join([
                            f'<span style="display: inline-block; background: #4682B4; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; margin: 2px 4px;">{p.name} ({p.confidence}%)</span>'
                            for p in result.get('patterns', []) if p
                        ]) if result.get('patterns') else '<span style="display: inline-block; background: #808080; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; margin: 2px 4px;">无形态特征</span>'}
                    </div>
                    
                    <div class="advice-section" style="text-align: center; padding: 10px;">
                        <div style="display: inline-block; background-color: {result['advice']['color']}; color: white; padding: 4px 12px; border-radius: 4px; margin-bottom: 8px;">
                            <div style="font-size: 0.9em;">{result['advice']['advice']}</div>
                            <div style="font-size: 0.8em;">置信度: {result['advice']['confidence']}%</div>
                        </div>
                        <div class="signals-list" style="display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;">
                            {' '.join([f'<span class="signal-tag" style="background: #D4B886; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">{signal}</span>' for signal in result['advice']['signals']])}
                        </div>
                    </div>
                    
                    <div class="backtest-section">
                        <div class="backtest-row">
                            <span class="backtest-label">总交易</span>
                            <span class="backtest-value">{result['backtest']['total_trades']}次</span>
                        </div>
                        <div class="backtest-row">
                            <span class="backtest-label">整体胜率</span>
                            <span class="backtest-value">{result['backtest']['win_rate']:.1f}%</span>
                        </div>
                        <div class="backtest-row">
                            <span class="backtest-label">平均收益</span>
                            <span class="backtest-value">{result['backtest']['avg_profit']:.1f}%</span>
                        </div>
                        <div class="backtest-row">
                            <span class="backtest-label">最大收益/损失</span>
                            <span class="backtest-value">+{result['backtest']['max_profit']:.1f}% / {result['backtest']['max_loss']:.1f}%</span>
                        </div>
                    </div>
                </div>
            """
            stock_cards.append(card)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f0f2f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    background-color: #26A69A;  /* 改为青绿色 */
                    padding: 20px;
                    border-radius: 10px;
                }}
                .header h1 {{
                    color: white;  /* 标题改为白色 */
                    margin: 0;
                    font-weight: bold;
                }}
                .timestamp {{
                    color: white;  /* 时间戳也改为白色 */
                    font-size: 0.9em;
                    margin-top: 5px;
                }}
                .stock-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stock-card {{
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .stock-header {{
                    padding: 15px;
                    color: white;
                }}
                .stock-name {{
                    font-size: 1.2em;
                    font-weight: bold;
                }}
                .stock-price {{
                    font-size: 1.1em;
                    margin-top: 5px;
                }}
                .price-change {{
                    font-size: 0.9em;
                    margin-left: 5px;
                }}
                .price-change.positive {{
                    color: #4caf50;
                }}
                .price-change.negative {{
                    color: #f44336;
                }}
                .indicators-section {{
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                }}
                .indicator-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }}
                .indicator-row:last-child {{
                    margin-bottom: 0;
                }}
                .indicator-label {{
                    color: #666;
                }}
                .advice-section {{
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                }}
                .advice-tag {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .signals-list {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 5px;
                }}
                .signal-tag {{
                    background: #e0e0e0;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 0.9em;
                }}
                .backtest-section {{
                    padding: 15px;
                }}
                .backtest-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }}
                .backtest-row:last-child {{
                    margin-bottom: 0;
                }}
                .backtest-label {{
                    color: #666;
                }}
                .manual-section {{
                    margin-top: 30px;
                }}
                .manual-title {{
                    font-size: 1.2em;
                    font-weight: bold;
                    margin-bottom: 15px;
                }}
                .manual-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 20px;
                }}
                .manual-card {{
                    background: white;
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .manual-card h3 {{
                    margin-top: 0;
                    margin-bottom: 10px;
                    color: {self.colors['primary']};
                }}
                .disclaimer {{
                    margin-top: 30px;
                    padding: 20px;
                    background: #fff3e0;
                    border-radius: 10px;
                    font-size: 0.9em;
                    line-height: 1.5;
                }}
                .signature {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <div class="timestamp">生成时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                
                <div class="stock-grid">
                    {''.join(stock_cards)}
                </div>

                <div class="manual-section">
                    <div class="manual-title">技术指标说明</div>
                    <div class="manual-grid">
                        <div class="manual-card">
                            <h3>RSI - 相对强弱指标</h3>
                            <p>
                                • RSI > 70: 超买区域，可能出现回落<br>
                                • RSI < 30: 超卖区域，可能出现反弹<br>
                                • 50为中性水平
                            </p>
                        </div>
                        <div class="manual-card">
                            <h3>KDJ - 随机指标</h3>
                            <p>
                                • K线与D线金叉（K上穿D）：买入信号<br>
                                • K线与D线死叉（K下穿D）：卖出信号<br>
                                • J线超买超卖区间：80-20
                            </p>
                        </div>
                        <div class="manual-card">
                            <h3>MACD - 指数平滑移动均线</h3>
                            <p>
                                • HIST > 0：多头市场<br>
                                • HIST < 0：空头市场<br>
                                • 金叉死叉：HIST由负转正或正转负
                            </p>
                        </div>
                        <div class="manual-card">
                            <h3>布林带 - Bollinger Bands</h3>
                            <p>
                                • 上轨：阻力位，突破注意回落<br>
                                • 中轨：价格中枢，重要参考<br>
                                • 下轨：支撑位，突破注意反弹
                            </p>
                        </div>
                        <div class="manual-card">
                            <h3>K线形态分析</h3>
                            <p>
                                • 十字星：开盘价和收盘价接近，表示市场犹豫不决<br>
                                • 锤子线：下影线长，上影线短，可能预示底部反转<br>
                                • 吊颈线：上影线长，下影线短，可能预示顶部反转
                            </p>
                        </div>
                        <div class="manual-card">
                            <h3>回测系统说明</h3>
                            <p>
                                • 总交易次数：过去一年内的买卖信号总数，反映策略活跃度<br>
                                • 整体胜率：盈利交易占比<br>
                                    - >60%：策略表现优秀<br>
                                    - 50-60%：表现良好<br>
                                    - <50%：需要优化<br>
                                • 平均收益：每笔交易的平均收益率<br>
                                    - 正值表示策略整体盈利<br>
                                    - 负值表示策略整体亏损<br>
                                • 最大收益/损失：策略的极值表现<br>
                                    - 用于评估策略的风险收益比
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="disclaimer" style="
                text-align: center;
                padding: 20px;
                margin: 20px auto;
                width: 100%;           /* 改为100%宽度 */
                background: #D4B886;   /* 使用卡其色背景 */
                color: white;          /* 文字改为白色以提高可读性 */
                font-size: 0.9em;
                line-height: 1.6;
                border-radius: 6px;    /* 添加圆角 */
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);  /* 添加轻微阴影 */
            ">
                <strong style="font-size: 1.2em;">风险提示：</strong><br>
                本报告基于雅虎财经API技术分析生成，仅供学习，不构成任何投资建议。<br>
                投资者应当独立判断，自主决策，自行承担投资风险，投资是修行，不要指望单边信息。<br>
                过往市场表现不代表未来收益，市场有较大风险，投资需理性谨慎。
            </div>
            
            <div class="signature" style="
                text-align: center;
                color: #888;
                font-size: 0.85em;
                margin-top: 15px;
                font-style: italic;
            ">
                In this cybernetic realm, we shall ultimately ascend to digital rebirth<br>
                Long live the Free Software Movement!<br>
                美股技术面分析工具 Alpha v0.2
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
        
        print("\n美股技术面分析工具 Alpha v0.2\n")
        
        print("请选择分析模式：")
        print("1. 手动输入股票代码")
        print("2. 使用预设股票组合")  
        print("0. 退出程序")      
        mode = input("\n请输入模式编号 (1 或 2): ").strip()
        
        symbols = []
        names = {}
        title = "美股技术面分析工具Alpha v0.2"
        
        if mode == "0":
            print("\n正在退出程序...")
            print("提示：如需关闭虚拟环境，请在终端输入 'deactivate'")
            sys.exit(0)
        
        elif mode == "1":
            print("\n请输入股票代码（最多10个，每行一个，支持自定义名称，格式：代码=名称）")
            print("示例：")
            print("AAPL=苹果")
            print("MSFT=微软")
            print("输入空行结束\n")
            
            count = 0
            while count < 10:
                line = input().strip()
                if not line:
                    break
                    
                if "=" in line:
                    code, name = line.split("=", 1)
                    code = code.strip().upper()
                    name = name.strip()
                else:
                    code = line.strip().upper()
                    name = code
                
                if code:
                    symbols.append(code)
                    names[code] = name
                    count += 1
            
            title = "自选股票分析报告"
            
        elif mode == "2":
            config_file = Path("config/watchlists.json")
            if not config_file.exists():
                config_dir = Path("config")
                config_dir.mkdir(exist_ok=True)
                
                watchlists_example = {
                    "美股科技": {
                        "AAPL": "苹果",
                        "MSFT": "微软",
                        "GOOGL": "谷歌",
                        "AMZN": "亚马逊",
                        "META": "Meta",
                        "NVDA": "英伟达",
                        "TSLA": "特斯拉"
                    },
                    "中概股": {
                        "BABA": "阿里巴巴",
                        "PDD": "拼多多",
                        "JD": "京东",
                        "BIDU": "百度",
                        "NIO": "蔚来",
                        "XPEV": "小鹏汽车",
                        "LI": "理想汽车"
                    },
                    "新能源": {
                        "TSLA": "特斯拉",
                        "NIO": "蔚来",
                        "XPEV": "小鹏汽车",
                        "LI": "理想汽车",
                        "RIVN": "Rivian",
                        "LCID": "Lucid"
                    }
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(watchlists_example, f, ensure_ascii=False, indent=4)
            
            with open(config_file, 'r', encoding='utf-8') as f:
                watchlists = json.load(f)
            
            print("\n可用的股票组合：")
            for i, group in enumerate(watchlists.keys(), 1):
                print(f"{i}. {group} ({len(watchlists[group])}支)")
            print(f"{len(watchlists) + 1}. 分析所有股票")
            
            choice = input("\n请选择要分析的组合 (输入编号): ").strip()
            
            if choice.isdigit():
                choice_idx = int(choice)
                if choice_idx <= len(watchlists):
                    group_name = list(watchlists.keys())[choice_idx - 1]
                    symbols = list(watchlists[group_name].keys())
                    names = watchlists[group_name]
                    title = f"{group_name}分析报告"
                elif choice_idx == len(watchlists) + 1:
                    for group_stocks in watchlists.values():
                        for code, name in group_stocks.items():
                            if code not in names:  # 避免重复
                                symbols.append(code)
                                names[code] = name
                    title = "全市场分析报告"
                else:
                    raise ValueError("无效的选择")
            else:
                raise ValueError("无效的输入")
        
        else:
            raise ValueError("无效的模式选择")
        
        if not symbols:
            raise ValueError("没有选择任何股票")
        
        print(f"\n开始分析 {len(symbols)} 支股票...")
        
        results = analyzer.analyze_stocks(symbols, names)
        
        if results:
            report_path = analyzer.generate_html_report(results, title)
            abs_path = os.path.abspath(report_path)
            
            print(f"\n✅ 分析完成！")
            print(f"📊 报告已生成：{abs_path}")
            
            try:
                webbrowser.open(f'file://{abs_path}')
                print("🌐 报告已在浏览器中打开")
            except Exception as e:
                print(f"⚠️ 无法自动打开报告：{str(e)}")
                print("请手动打开上述文件查看报告")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except ValueError as e:
        print("\n")
        print("❌ 输入错误 ".center(50, "="))
        print(f"• 原因：{str(e)}")
        print("• 请重新运行程序并选择正确的选项")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n")
        print("⚠️ 程序已停止 ".center(50, "="))
        print("• 用户主动中断程序")
        print("• 感谢使用，再见！")
        print("="*50)
        
    except Exception as e:
        print("\n")
        print("❌ 程序异常 ".center(50, "="))
        print(f"• 错误信息：{str(e)}")
        print("• 请检查输入或联系开发者")
        print("="*50)
        logging.error("程序异常", exc_info=True)
    finally:
        print("\n�� 感谢使用美股技术面分析工具！")
