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

# 忽略特定警告
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
            "primary": "#1976D2",      # 主色调：深邃蓝色
            "secondary": "#673AB7",     # 次要色：高贵紫色
            "success": "#2E7D32",       # 成功色：深绿色
            "warning": "#F57F17",       # 警告色：金黄色
            "danger": "#C62828",        # 危险色：深红色
            "info": "#0097A7",          # 信息色：青色
            "background": "#F5F5F5",    # 背景色：浅灰色
            "text": "#212121",          # 文字色：深灰色
            "card": "#FFFFFF",          # 卡片色：白色
            "border": "#E0E0E0",        # 边框色：浅灰色
            "gradient_start": "#00695c", # 渐变开始：深青绿色
            "gradient_end": "#00897b",   # 渐变结束：浅青绿色
            "strong_buy": "#00C853",     # 强烈买入：翠绿色
            "buy": "#4CAF50",           # 买入：绿色
            "strong_sell": "#D50000",    # 强烈卖出：鲜红色
            "sell": "#F44336",          # 卖出：红色
            "neutral": "#FF9800",        # 观望：橙色
            "name_tag": "#E3F2FD",      # 股票名称标签：浅蓝色
            "highlight": "#FFF3E0",      # 高亮背景：暖色
            "tag_text": "#FFFFFF",       # 标签文字：白色
            "advice_bg": "#FAFAFA"       # 建议背景：淡灰色
        }

    def calculate_macd(self, prices: pd.Series) -> tuple:
        """计算MACD指标"""
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
        """
        计算KDJ指标
        :param high: 最高价序列
        :param low: 最低价序列
        :param close: 收盘价序列
        :param n: RSV计算周期，默认9
        :param m1: K值平滑因子，默认3
        :param m2: D值平滑因子，默认3
        :return: (K值, D值, J值)
        """
        high = pd.to_numeric(high, errors='coerce')
        low = pd.to_numeric(low, errors='coerce')
        close = pd.to_numeric(close, errors='coerce')
        
        # 计算RSV
        low_list = low.rolling(window=n, min_periods=1).min()
        high_list = high.rolling(window=n, min_periods=1).max()
        rsv = pd.Series(np.zeros(len(close)), index=close.index)
        
        # 避免除数为0
        denominator = high_list - low_list
        rsv = np.where(denominator != 0, 
                       (close - low_list) * 100 / denominator,
                       0)
        
        # 计算K值，使用SMA算法
        k = pd.Series(np.zeros(len(close)), index=close.index)
        k[0] = 50  # 初始值设为50
        for i in range(1, len(close)):
            k[i] = (m1 - 1) * k[i-1] / m1 + rsv[i] / m1
        
        # 计算D值，使用SMA算法
        d = pd.Series(np.zeros(len(close)), index=close.index)
        d[0] = 50  # 初始值设为50
        for i in range(1, len(close)):
            d[i] = (m2 - 1) * d[i-1] / m2 + k[i] / m2
        
        # 计算J值
        j = 3 * k - 2 * d
        
        # 处理可能的极端值
        k = k.clip(0, 100)
        d = d.clip(0, 100)
        j = j.clip(0, 100)
        
        # 填充空值
        k = k.fillna(50)
        d = d.fillna(50)
        j = j.fillna(50)
        
        return float(k.iloc[-1]), float(d.iloc[-1]), float(j.iloc[-1])

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return float(100 - (100 / (1 + rs)).iloc[-1])

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20) -> tuple:
        """计算布林带"""
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        return float(upper.iloc[-1]), float(middle.iloc[-1]), float(lower.iloc[-1])

    def generate_trading_advice(self, indicators, price: float) -> dict:
        """生成交易建议，重点关注布林带和RSI"""
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
        
        # 布林带信号（重要权重）
        bb_position = (price - bb_lower) / (bb_upper - bb_lower) * 100
        if bb_position < 0:
            signals.append("价格低于布林带下轨，超卖明显")
            confidence += 40
        elif bb_position < 20:
            signals.append("价格接近布林带下轨，可能超卖")
            confidence += 30
        elif bb_position > 100:
            signals.append("价格高于布林带上轨，超买明显")
            confidence -= 40
        elif bb_position > 80:
            signals.append("价格接近布林带上轨，可能超买")
            confidence -= 30
        
        # RSI信号（重要权重）
        if rsi < 30:
            signals.append("RSI严重超卖（<30）")
            confidence += 35
        elif rsi < 40:
            signals.append("RSI处于低位")
            confidence += 25
        elif rsi > 70:
            signals.append("RSI严重超买（>70）")
            confidence -= 35
        elif rsi > 60:
            signals.append("RSI处于高位")
            confidence -= 25
        
        # MACD信号（次要权重）
        if macd > 0 and macd_hist > 0:
            signals.append("MACD金叉后上升趋势")
            confidence += 15
        elif macd < 0 and macd_hist < 0:
            signals.append("MACD死叉后下降趋势")
            confidence -= 15
        
        # KDJ信号（次要权重）
        if k < 20 and j < 20:
            signals.append("KDJ超卖区间")
            confidence += 10
        elif k > 80 and j > 80:
            signals.append("KDJ超买区间")
            confidence -= 10
        
        # 生成建议
        if confidence >= 60:
            advice = "强烈买入"
            color = self.colors["strong_buy"]
            description = "多个指标显示极度超卖，建议积极买入"
        elif confidence >= 30:
            advice = "建议买入"
            color = self.colors["buy"]
            description = "指标偏向利好，可以考虑买入"
        elif confidence <= -60:
            advice = "强烈卖出"
            color = self.colors["strong_sell"]
            description = "多个指标显示极度超买，建议及时卖出"
        elif confidence <= -30:
            advice = "建议卖出"
            color = self.colors["sell"]
            description = "指标偏向利空，建议考虑卖出"
        else:
            advice = "观望等待"
            color = self.colors["neutral"]
            description = "指标中性，建议观望等待机会"
        
        return {
            'advice': advice,
            'signals': signals,
            'confidence': abs(confidence),
            'color': color,
            'description': description
        }

    def analyze_stocks(self, symbols: List[str], names: Optional[Dict[str, str]] = None) -> List[Dict]:
        """分析多个股票"""
        results = []
        total = len(symbols)
        
        for i, symbol in enumerate(symbols, 1):
            try:
                name = names.get(symbol, symbol) if names else symbol
                self.logger.info(f"正在分析 {name} ({symbol}) - {i}/{total}")
                
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")
                
                if hist.empty:
                    self.logger.warning(f"未能获取到 {symbol} 的数据")
                    continue
                
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                price = float(latest['Close'])
                price_change = ((price / prev['Close']) - 1) * 100
                
                rsi = self.calculate_rsi(hist['Close'])
                macd, signal_line, hist_macd = self.calculate_macd(hist['Close'])
                k, d, j = self.calculate_kdj(hist['High'], hist['Low'], hist['Close'])
                upper, middle, lower = self.calculate_bollinger_bands(hist['Close'])
                
                indicators = {
                    'rsi': rsi,
                    'macd': {
                        'macd': macd,
                        'signal': signal_line,
                        'hist': hist_macd
                    },
                    'kdj': {
                        'k': k,
                        'd': d,
                        'j': j
                    },
                    'bollinger': {
                        'upper': upper,
                        'middle': middle,
                        'lower': lower
                    }
                }
                
                trading_advice = self.generate_trading_advice(indicators, price)
                
                result = {
                    'symbol': symbol,
                    'name': name,
                    'price': price,
                    'change': price_change,
                    'volume': int(latest['Volume']),
                    'indicators': indicators,
                    'advice': trading_advice
                }
                
                results.append(result)
                print(f"进度: {i}/{total} - 完成分析 {name}")
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错: {str(e)}")
                continue
        
        return results

    def generate_html_report(self, results: List[Dict], title: str = "股票分析报告") -> Path:
        """生成HTML分析报告"""
        timestamp = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')
        report_file = self.results_path / f"stock_analysis_{timestamp}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                    line-height: 1.6;
                    color: {self.colors['text']};
                    background-color: {self.colors['background']};
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding: 30px;
                    background: linear-gradient(135deg, {self.colors['gradient_start']}, {self.colors['gradient_end']});
                    color: white;
                    border-radius: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 300;
                }}
                .stock-card {{
                    background-color: {self.colors['card']};
                    border-radius: 15px;
                    padding: 25px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    transition: transform 0.3s ease;
                }}
                .stock-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                .stock-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding: 15px;
                    background: {self.colors['name_tag']};
                    border-radius: 10px;
                }}
                .stock-name {{
                    font-size: 1.8em;
                    font-weight: 500;
                    color: {self.colors['primary']};
                    padding: 8px 15px;
                    background: linear-gradient(135deg, {self.colors['gradient_start']}, {self.colors['gradient_end']});
                    border-radius: 8px;
                    color: white;
                }}
                .price-info {{
                    text-align: right;
                    background: {self.colors['highlight']};
                    padding: 10px 20px;
                    border-radius: 8px;
                }}
                .price {{
                    font-size: 1.5em;
                    font-weight: 500;
                }}
                .change.positive {{
                    color: {self.colors['success']};
                }}
                .change.negative {{
                    color: {self.colors['danger']};
                }}
                .indicators-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .indicator-card {{
                    background-color: {self.colors['background']};
                    padding: 15px;
                    border-radius: 10px;
                    border: 1px solid {self.colors['border']};
                }}
                .indicator-title {{
                    font-size: 1.1em;
                    font-weight: 500;
                    color: {self.colors['secondary']};
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                    border-bottom: 2px solid {self.colors['border']};
                }}
                .advice-section {{
                    margin-top: 25px;
                    padding: 20px;
                    border-radius: 10px;
                    background-color: var(--advice-bg);
                }}
                .advice-header {{
                    font-size: 1.3em;
                    font-weight: 500;
                    margin-bottom: 15px;
                    padding: 10px;
                    color: white;
                    border-radius: 8px;
                    text-align: center;
                }}
                .signals-list {{
                    list-style: none;
                    padding: 0;
                    margin: 15px 0;
                }}
                .signals-list li {{
                    margin: 8px 0;
                    padding: 8px 12px;
                    background: {self.colors['highlight']};
                    border-radius: 6px;
                }}
                .confidence-meter {{
                    height: 8px;
                    background: #e0e0e0;
                    border-radius: 4px;
                    margin: 15px 0;
                    overflow: hidden;
                }}
                .confidence-value {{
                    height: 100%;
                    border-radius: 4px;
                    transition: width 0.3s ease;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <p>生成时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
        """

        for result in results:
            price_change_class = "positive" if result['change'] >= 0 else "negative"
            price_change_symbol = "+" if result['change'] >= 0 else ""
            advice = result['advice']
            
            html_content += f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-name">
                            {result['name']} ({result['symbol']})
                        </div>
                        <div class="price-info">
                            <div class="price">${result['price']:.2f}</div>
                            <div class="change {price_change_class}">
                                {price_change_symbol}{result['change']:.2f}%
                            </div>
                        </div>
                    </div>
                    
                    <div class="indicators-grid">
                        <div class="indicator-card">
                            <div class="indicator-title">RSI 指标</div>
                            <div class="indicator-value">
                                {result['indicators']['rsi']:.2f}
                                <span class="indicator-analysis">
                                    {' (超买)' if result['indicators']['rsi'] > 70 else ' (超卖)' if result['indicators']['rsi'] < 30 else ''}
                                </span>
                            </div>
                        </div>
                        
                        <div class="indicator-card">
                            <div class="indicator-title">MACD 指标</div>
                            <div class="indicator-value">
                                MACD: {result['indicators']['macd']['macd']:.3f}<br>
                                信号线: {result['indicators']['macd']['signal']:.3f}<br>
                                柱状值: {result['indicators']['macd']['hist']:.3f}
                            </div>
                        </div>
                        
                        <div class="indicator-card">
                            <div class="indicator-title">KDJ 指标</div>
                            <div class="indicator-value">
                                K: {result['indicators']['kdj']['k']:.2f}<br>
                                D: {result['indicators']['kdj']['d']:.2f}<br>
                                J: {result['indicators']['kdj']['j']:.2f}
                            </div>
                        </div>
                        
                        <div class="indicator-card">
                            <div class="indicator-title">布林带</div>
                            <div class="indicator-value">
                                上轨: {result['indicators']['bollinger']['upper']:.2f}<br>
                                中轨: {result['indicators']['bollinger']['middle']:.2f}<br>
                                下轨: {result['indicators']['bollinger']['lower']:.2f}
                            </div>
                        </div>
                    </div>
                    
                    <div class="advice-section" style="background-color: {advice['color']}15;">
                        <div class="advice-header" style="background-color: {advice['color']}">
                            交易建议: {advice['advice']}
                        </div>
                        <div class="advice-content">
                            <p>{advice['description']}</p>
                            <ul class="signals-list">
                                {' '.join(f'<li>{signal}</li>' for signal in advice['signals'])}
                            </ul>
                            <div class="confidence-meter">
                                <div class="confidence-value" 
                                     style="width: {advice['confidence']}%; background-color: {advice['color']}">
                                </div>
                            </div>
                            <div style="text-align: center;">
                                信心指数: {advice['confidence']}%
                            </div>
                        </div>
                    </div>
                </div>
            """

        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file

if __name__ == "__main__":
    analyzer = StockAnalyzer()
    
    try:
        print("\n📊 股票技术分析系统")
        print("=" * 50)
        print("1. 输入自定义股票代码（不超过10个）")
        print("2. 从配置文件读取股票组合")
        choice = input("\n请选择操作 (1/2): ")
        
        if choice == "1":
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
            config_file = Path("config/watchlists.json")
            if not config_file.exists():
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
            
            # 尝试自动打开报告
            try:
                print("\n🌐 正在尝试自动打开报告...")
                webbrowser.open(f'file://{abs_path}')
                print("✅ 报告已在默认浏览器中打开")
            except Exception as e:
                print(f"⚠️ 无法自动打开报告：{str(e)}")
                print("请手动打开路径查看报告")
            
            print("\n📊 简要分析结果：")
            for result in results:
                print(f"\n{result['name']} ({result['symbol']}):")
                print(f"价格: ${result['price']:.2f} ({result['change']:+.2f}%)")
                print(f"RSI: {result['indicators']['rsi']:.2f}")
                print(f"MACD: {result['indicators']['macd']['macd']:.3f}")
                print(f"KDJ: K={result['indicators']['kdj']['k']:.2f}, D={result['indicators']['kdj']['d']:.2f}, J={result['indicators']['kdj']['j']:.2f}")
                print(f"交易建议: {result['advice']['advice']} (信心指数: {result['advice']['confidence']}%)")
        else:
            print("\n❌ 没有产生任何分析结果")
        
    except Exception as e:
        print(f"\n❌ 程序运行出错：{str(e)}")
        logging.error(f"程序异常：{str(e)}", exc_info=True)
        