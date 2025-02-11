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
from tqdm import tqdm
import time

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
        k[n-1] = 50.0
        d[n-1] = 50.0
        
        for i in range(n, len(close)):
            k[i] = 2/3 * k[i-1] + 1/3 * rsv[i]
            d[i] = 2/3 * d[i-1] + 1/3 * k[i]
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
    
    def backtest_strategy(self, data: pd.DataFrame) -> Dict:
        close = data['Close'].values
        high = data['High'].values
        low = data['Low'].values
        
        trades = []
        position = 0  # -1: 空仓, 0: 无仓位, 1: 多仓
        entry_price = 0
        buy_trades = []
        sell_trades = []
        
        # 设置止损止盈参数
        stop_loss = 0.05  # 5%止损
        take_profit = 0.10  # 10%止盈
        
        for i in range(26, len(close)):
            price_window = pd.Series(close[:i+1])
            high_window = pd.Series(high[:i+1])
            low_window = pd.Series(low[:i+1])
            
            current_price = close[i]
            
            # 计算技术指标
            rsi = self.calculate_rsi(price_window)
            macd, signal, hist = self.calculate_macd(price_window)
            k, d, j = self.calculate_kdj(high_window, low_window, price_window)
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(price_window)
            
            # 买入信号
            buy_signal = (
                (rsi < 35) and  # 放宽RSI条件
                ((k < 25 and k > d) or  # 放宽KDJ条件
                 (hist > 0) or  # MACD金叉
                 (current_price < bb_lower))  # 触及布林下轨
            )
            
            # 卖出信号
            sell_signal = (
                (rsi > 65) and  # 放宽RSI条件
                ((k > 75 and k < d) or  # 放宽KDJ条件
                 (hist < 0) or  # MACD死叉
                 (current_price > bb_upper))  # 触及布林上轨
            )
            
            # 先检查止损止盈
            if position != 0:
                profit_pct = ((current_price - entry_price) / entry_price) * 100 if position == 1 else ((entry_price - current_price) / entry_price) * 100
                
                # 触发止损或止盈
                if profit_pct <= -stop_loss * 100 or profit_pct >= take_profit * 100:
                    if position == 1:
                        buy_trades.append(profit_pct)
                    else:
                        sell_trades.append(profit_pct)
                    trades.append(profit_pct)
                    position = 0
                    continue
            
            # 交易信号执行
            if position == 0:  # 无仓位时
                if buy_signal:
                    position = 1
                    entry_price = current_price
                elif sell_signal:
                    position = -1
                    entry_price = current_price
            elif position == 1:  # 持有多仓
                if sell_signal:
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                    trades.append(profit_pct)
                    buy_trades.append(profit_pct)
                    position = -1
                    entry_price = current_price
            elif position == -1:  # 持有空仓
                if buy_signal:
                    profit_pct = ((entry_price - current_price) / entry_price) * 100
                    trades.append(profit_pct)
                    sell_trades.append(profit_pct)
                    position = 1
                    entry_price = current_price
        
        # 回测结束，平掉最后的仓位
        if position != 0:
            profit_pct = ((close[-1] - entry_price) / entry_price) * 100 if position == 1 else ((entry_price - close[-1]) / entry_price) * 100
            trades.append(profit_pct)
            if position == 1:
                buy_trades.append(profit_pct)
            else:
                sell_trades.append(profit_pct)
        
        # 计算统计数据
        total_trades = len(trades)
        if total_trades == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'buy_win_rate': 0,
                'sell_win_rate': 0,
                'avg_profit': 0,
                'max_profit': 0,
                'max_loss': 0
            }
        
        win_trades = len([t for t in trades if t > 0])
        buy_wins = len([t for t in buy_trades if t > 0])
        sell_wins = len([t for t in sell_trades if t > 0])
        
        return {
            'total_trades': total_trades,
            'win_rate': (win_trades / total_trades) * 100 if total_trades > 0 else 0,
            'buy_win_rate': (buy_wins / len(buy_trades)) * 100 if buy_trades else 0,
            'sell_win_rate': (sell_wins / len(sell_trades)) * 100 if sell_trades else 0,
            'avg_profit': sum(trades) / len(trades) if trades else 0,
            'max_profit': max(trades) if trades else 0,
            'max_loss': min(trades) if trades else 0
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
                    'advice': advice,
                    'backtest': backtest_results
                })
                
                print(f"✅ {symbol} 分析完成")
                time.sleep(0.5)  # 添加短暂延迟，让用户能看清进度
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错", exc_info=True)
                print(f"❌ {symbol} 分析失败: {str(e)}")
                continue
        
        return results
    
    def generate_trading_advice(self, indicators: Dict, price: float) -> Dict:
        rsi = indicators['rsi']
        k = indicators['kdj']['k']
        d = indicators['kdj']['d']
        j = indicators['kdj']['j']  # 添加J值
        macd = indicators['macd']['macd']
        signal = indicators['macd']['signal']
        hist = indicators['macd']['hist']
        bb_upper = indicators['bollinger']['upper']
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
        if k < 20 and d < 20 and j < 0:  # 添加J值判断
            signals.append("KDJ超卖")
            confidence += 20
        elif k > 80 and d > 80 and j > 100:  # 添加J值判断
            signals.append("KDJ超买")
            confidence -= 20
        elif k > d and j > k:  # 考虑J值的金叉形态
            signals.append("KDJ金叉")
            confidence += 15
        elif k < d and j < k:  # 考虑J值的死叉形态
            signals.append("KDJ死叉")
            confidence -= 15
        
        # MACD信号
        if macd > signal and hist > 0:
            signals.append("MACD金叉")
            confidence += 15
        elif macd < signal and hist < 0:
            signals.append("MACD死叉")
            confidence -= 15
        
        # 布林带信号
        if price <= bb_lower:
            signals.append("触及布林下轨")
            confidence += 20
        elif price >= bb_upper:
            signals.append("触及布林上轨")
            confidence -= 20
        
        # 生成建议
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

    def generate_html_report(self, results: List[Dict], title: str = "股票分析报告") -> str:
        timestamp = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')
        report_file = self.results_path / f"stock_analysis_{timestamp}.html"
        
        stock_cards = []
        for result in results:
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
                    <div class="advice-section">
                        <div class="advice-tag" style="background-color: {result['advice']['color']}">
                            {result['advice']['advice']} ({result['advice']['confidence']}%)
                        </div>
                        <div class="signals-list">
                            {' '.join([f'<span class="signal-tag">{signal}</span>' for signal in result['advice']['signals']])}
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
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    margin: 0;
                    padding: 15px;
                    background-color: #f0f2f5;
                    color: {self.colors['text']};
                    line-height: 1.4;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 15px;
                    padding: 15px;
                }}
                
                .header {{
                    grid-column: 1 / -1;
                    text-align: center;
                    margin-bottom: 20px;
                    background: #26a69a;  /* 改这里，换成浅青绿色 */
                    color: white;         /* 保持文字为白色 */
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .stock-card {{
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }}
                
                .stock-card:hover {{
                    transform: translateY(-2px);
                }}
                
                .stock-header {{
                    padding: 12px;
                    color: white;
                }}
                
                .stock-name {{
                    font-size: 15px;
                    font-weight: 600;
                }}
                
                .stock-price {{
                    font-size: 16px;
                    font-weight: 700;
                    margin-top: 4px;
                }}
                
                .price-change {{
                    font-size: 13px;
                    margin-left: 5px;
                }}
                
                .positive {{ color: #4caf50; }}
                .negative {{ color: #f44336; }}
                
                .indicators-section {{
                    padding: 10px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #eee;
                }}
                
                .indicator-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 3px 0;
                    font-size: 13px;
                }}
                
                .advice-section {{
                    padding: 10px;
                    text-align: center;
                    background: white;
                }}
                
                .advice-tag {{
                    display: inline-block;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 13px;
                    font-weight: 600;
                    margin-bottom: 5px;
                }}
                
                .signals-list {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 4px;
                    justify-content: center;
                }}
                
                .signal-tag {{
                    background: {self.colors['secondary']};
                    color: white;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 11px;
                }}
                
                .backtest-section {{
                    padding: 10px;
                    background: #f8f9fa;
                    border-top: 1px solid #eee;
                }}
                
                .backtest-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 2px 0;
                    font-size: 12px;
                }}
                
                .manual-section {{
                    grid-column: 1 / -1;
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-top: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .manual-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: {self.colors['primary']};
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid {self.colors['primary']};
                }}
                
                .manual-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                
                .manual-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid {self.colors['primary']};
                }}
                
                .manual-card h3 {{
                    margin: 0 0 10px 0;
                    font-size: 15px;
                    color: {self.colors['secondary']};
                }}
                
                .manual-card p {{
                    margin: 0;
                    font-size: 13px;
                    line-height: 1.6;
                }}
                
                .disclaimer {{
                    grid-column: 1 / -1;
                    text-align: center;
                    margin-top: 20px;
                    padding: 15px;
                    background: #fff3e0;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #f57c00;
                    line-height: 1.6;
                }}
                
                .signature {{
                    grid-column: 1 / -1;
                    text-align: right;
                    margin-top: 20px;
                    font-style: italic;
                    color: {self.colors['secondary']};
                    font-size: 13px;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <div class="timestamp">生成时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                
                {''.join(stock_cards)}

                    <div class="manual-section">
                    <div class="manual-title">技术指标说明</div>
                    <div class="manual-grid">
                        <div class="manual-card">
                            <h3>RSI - 相对强弱指标</h3>
                            <p>• 计算周期：14天<br>
                               • 超买区间：RSI > 70<br>
                               • 超卖区间：RSI < 30<br>
                               • 原理：衡量价格动量，帮助判断超买超卖</p>
                        </div>
                        <div class="manual-card">
                            <h3>MACD - 指数平滑异同移动平均线</h3>
                            <p>• 快线参数：12日EMA<br>
                               • 慢线参数：26日EMA<br>
                               • 信号线：9日EMA<br>
                               • 原理：反映价格趋势的变化和动量</p>
                        </div>
                        <div class="manual-card">
                            <h3>KDJ - 随机指标</h3>
                            <p>• 计算周期：9日<br>
                               • K值：RSV的3日移动平均<br>
                               • D值：K值的3日移动平均<br>
                               • J值：3K-2D<br>
                               • 原理：反映价格的超买超卖和潜在转折点</p>
                        </div>
                        <div class="manual-card">
                            <h3>布林带 - Bollinger Bands</h3>
                            <p>• 中轨：20日移动平均线<br>
                               • 上下轨：中轨±2倍标准差<br>
                               • 原理：反映价格波动性和潜在支撑压力位</p>
                        </div>
                    </div>
                    
                    <div class="manual-title">交易策略说明</div>
                    <div class="manual-grid">
                        <div class="manual-card">
                            <h3>买入条件</h3>
                            <p>• RSI < 30（超卖）<br>
                               • KDJ金叉且K < 20<br>
                               • MACD金叉<br>
                               • 价格触及布林下轨<br>
                               • 满足多个条件增加信心指数</p>
                        </div>
                        <div class="manual-card">
                            <h3>卖出条件</h3>
                            <p>• RSI > 70（超买）<br>
                               • KDJ死叉且K > 80<br>
                               • MACD死叉<br>
                               • 价格触及布林上轨<br>
                               • 满足多个条件增加信心指数</p>
                        </div>
                        <div class="manual-card">
                            <h3>风险控制</h3>
                            <p>• 止损：-5%<br>
                               • 止盈：+10%<br>
                               • 建议仓位：单只股票不超过20%<br>
                               • 注意：高波动性股票应适当提高止损位</p>
                        </div>
                    </div>
                    
                    <div class="manual-title">回测说明</div>
                    <div class="manual-grid">
                        <div class="manual-card">
                            <h3>回测参数</h3>
                            <p>• 周期：过去一年<br>
                               • 交易成本：未计入手续费和滑点<br>
                               • 交易规则：信号出现立即执行<br>
                               • 仓位：满仓进出</p>
                        </div>
                        <div class="manual-card">
                            <h3>统计指标</h3>
                            <p>• 总交易次数：策略产生的交易次数<br>
                               • 胜率：盈利交易占总交易的比例<br>
                               • 平均收益：所有交易的平均收益率<br>
                               • 最大收益/损失：单次交易的最佳和最差表现</p>
                        </div>
                    </div>
                </div>
                
                <div class="disclaimer">
                    <strong>风险提示：</strong><br>
                    本报告基于技术分析生成，仅供参考，不构成任何投资建议。<br>
                    投资者应当独立判断，自主决策，自行承担投资风险。<br>
                    过往表现不代表未来收益，市场有风险，投资需谨慎。
                </div>
                
                <div class="signature">
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
        
        mode = input("\n请输入模式编号 (1 或 2): ").strip()
        
        symbols = []
        names = {}
        title = "股票分析报告"
        
        if mode == "1":
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
    except Exception as e:
        print(f"\n❌ 错误：{str(e)}")
        logging.error(f"程序异常", exc_info=True)
    finally:
        print("\n👋 感谢使用美股技术面分析工具！")


