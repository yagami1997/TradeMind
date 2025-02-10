import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional

class MarketAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.setup_paths()
        self.setup_watchlists()
        self.setup_brand_colors()
        
    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/market_analyzer.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("market_analyzer")
    
    def setup_paths(self):
        self.results_path = Path("reports")
        self.results_path.mkdir(exist_ok=True)
        
    def setup_watchlists(self):
        try:
            config_path = Path('config') / 'watchlists.json'
            with open(config_path, 'r', encoding='utf-8') as f:
                watchlists_data = json.load(f)
                self.watchlists_data = watchlists_data
                self.watchlists = {}
                for group_name, symbols_dict in watchlists_data.items():
                    self.watchlists[group_name] = list(symbols_dict.keys())
                self.logger.info(f"成功加载观察列表: {len(self.watchlists)}个分组")
        except Exception as e:
            self.logger.error(f"加载观察列表失败: {str(e)}")
            self.watchlists = {}
            
    def setup_brand_colors(self):
        self.colors = {
            "primary": "#2c3e50",
            "secondary": "#95a5a6",
            "success": "#27ae60",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "info": "#3498db",
            "background": "#ecf0f1",
            "text": "#2c3e50"
        }

    def analyze_market(self, group_name: str) -> List[Dict]:
        if group_name not in self.watchlists:
            self.logger.error(f"未找到分组: {group_name}")
            return []
            
        results = []
        symbols = self.watchlists[group_name]
        
        for symbol in symbols:
            try:
                name = self.watchlists_data[group_name].get(symbol, symbol) if hasattr(self, 'watchlists_data') else symbol
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")
                
                if hist.empty:
                    self.logger.warning(f"没有获取到 {symbol} 的数据")
                    continue
                
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                price_change = ((latest['Close'] / prev['Close']) - 1) * 100
                volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
                ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
                ma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
                rsi = self.calculate_rsi(hist['Close'])
                
                bb_middle = hist['Close'].rolling(window=20).mean()
                bb_std = hist['Close'].rolling(window=20).std()
                bb_upper = bb_middle + (bb_std * 2)
                bb_lower = bb_middle - (bb_std * 2)
                
                signal = "观望"
                latest_close = latest['Close']
                if latest_close < bb_lower.iloc[-1] and rsi < 30:
                    signal = "超卖 - 考虑买入"
                elif latest_close > bb_upper.iloc[-1] and rsi > 70:
                    signal = "超买 - 考虑卖出"
                elif latest_close > ma20 and ma20 > ma60:
                    signal = "上升趋势 - 持有"
                elif latest_close < ma20 and ma20 < ma60:
                    signal = "下降趋势 - 谨慎"
                
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'price': latest['Close'],
                    'change': price_change,
                    'volume': latest['Volume'],
                    'volatility': volatility,
                    'ma20': ma20,
                    'ma60': ma60,
                    'rsi': rsi,
                    'signal': signal,
                    'bb_upper': bb_upper.iloc[-1],
                    'bb_lower': bb_lower.iloc[-1],
                    'bb_middle': bb_middle.iloc[-1]
                })
                
                self.logger.info(f"成功分析 {symbol}")
                
            except Exception as e:
                self.logger.error(f"分析 {symbol} 时出错: {str(e)}")
                continue
                
        return results
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]

    def generate_html_report(self, results: List[Dict], group_name: str = "全部标的") -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"market_analysis_{group_name}_{timestamp}.html"
        file_path = self.results_path / filename

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>市场分析报告</title>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Noto Sans SC', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {self.colors['background']};
                    color: {self.colors['text']};
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 40px;
                    background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['info']});
                    color: white;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .card {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }}
                .card:hover {{
                    transform: translateY(-5px);
                }}
                .signal {{
                    padding: 8px 16px;
                    border-radius: 5px;
                    color: white;
                    text-align: center;
                    margin-top: 15px;
                }}
                .signal-buy {{
                    background-color: {self.colors['success']};
                }}
                .signal-sell {{
                    background-color: {self.colors['danger']};
                }}
                .signal-hold {{
                    background-color: {self.colors['secondary']};
                }}
                .signal-warning {{
                    background-color: {self.colors['warning']};
                }}
                .indicator {{
                    margin: 10px 0;
                    display: flex;
                    justify-content: space-between;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    color: {self.colors['secondary']};
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>市场分析报告 - {group_name}</h1>
                    <p>生成时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="grid">
        """

        for r in results:
            signal_class = "signal-hold"
            if "买入" in r['signal']:
                signal_class = "signal-buy"
            elif "卖出" in r['signal']:
                signal_class = "signal-sell"
            elif "谨慎" in r['signal']:
                signal_class = "signal-warning"

            html_content += f"""
                    <div class="card">
                        <h2>{r['symbol']} ({r['name']})</h2>
                        <div class="indicator">
                            <span>价格</span>
                            <span>${r['price']:.2f} ({r['change']:+.2f}%)</span>
                        </div>
                        <div class="indicator">
                            <span>RSI</span>
                            <span>{r['rsi']:.1f}</span>
                        </div>
                        <div class="indicator">
                            <span>波动率</span>
                            <span>{r['volatility']:.1f}%</span>
                        </div>
                        <div class="indicator">
                            <span>MA20/MA60</span>
                            <span>{r['ma20']:.2f}/{r['ma60']:.2f}</span>
                        </div>
                        <div class="signal {signal_class}">
                            {r['signal']}
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

def main():
    analyzer = MarketAnalyzer()
    
    print("\n=== 市场分析工具 ===")
    print("\n可用的选项:")
    print("1. 分析全部标的")
    print("2. 按分组分析")
    
    try:
        choice = int(input("\n请选择操作 (1-2): "))
        
        if choice == 1:
            all_results = []
            total_symbols = sum(len(symbols) for symbols in analyzer.watchlists.values())
            print(f"\n开始分析全部标的 (共 {total_symbols} 个)...")
            
            for group_name in analyzer.watchlists:
                print(f"\n正在分析 {group_name} 分组...")
                results = analyzer.analyze_market(group_name)
                all_results.extend(results)
            
            if all_results:
                report_path = analyzer.generate_html_report(all_results, "全部标的")
                print(f"\n分析报告已生成: {report_path}")
                print(f"成功分析: {len(all_results)}/{total_symbols} 个标的")
            else:
                print("\n没有可分析的数据")
                
        elif choice == 2:
            print("\n可用的分组:")
            groups = list(analyzer.watchlists.keys())
            for i, group_name in enumerate(groups, 1):
                symbol_count = len(analyzer.watchlists[group_name])
                print(f"{i}. {group_name} ({symbol_count} 个标的)")
            
            group_idx = int(input(f"\n请选择分组编号 (1-{len(groups)}): ")) - 1
            
            if 0 <= group_idx < len(groups):
                group_name = groups[group_idx]
                symbol_count = len(analyzer.watchlists[group_name])
                print(f"\n正在分析 {group_name} 分组 (共 {symbol_count} 个标的)...")
                
                results = analyzer.analyze_market(group_name)
                
                if results:
                    report_path = analyzer.generate_html_report(results, group_name)
                    print(f"\n分析报告已生成: {report_path}")
                    print(f"成功分析: {len(results)}/{symbol_count} 个标的")
                else:
                    print("\n没有可分析的数据")
            else:
                print("\n无效的分组编号")
        else:
            print("\n无效的选择")
            
    except ValueError:
        print("\n输入无效，请输入数字")
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n程序出错: {str(e)}")
        logging.error(f"程序出错: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()