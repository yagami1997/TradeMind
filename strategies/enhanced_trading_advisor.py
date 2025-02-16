import yfinance as yf
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
import pytz
from typing import Dict, Optional, List

class EnhancedTradingAdvisor:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data = None
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/trader_{self.symbol}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"trader_{self.symbol}")
    
    def fetch_data(self) -> bool:
        """获取股票数据"""
        try:
            ticker = yf.Ticker(self.symbol)
            self.data = ticker.history(period="1y")
            
            if self.data.empty:
                self.logger.error(f"没有获取到 {self.symbol} 的数据")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"获取 {self.symbol} 数据时出错: {str(e)}")
            return False
    
    def calculate_indicators(self) -> bool:
        """计算技术指标，重点关注布林带"""
        try:
            if self.data is None or self.data.empty:
                return False
            
            # 计算布林带（20日）
            self.data['BB_middle'] = self.data['Close'].rolling(window=20).mean()
            std = self.data['Close'].rolling(window=20).std()
            self.data['BB_upper'] = self.data['BB_middle'] + 2 * std
            self.data['BB_lower'] = self.data['BB_middle'] - 2 * std
            
            # 计算布林带宽度和百分比B
            self.data['BB_width'] = (self.data['BB_upper'] - self.data['BB_lower']) / self.data['BB_middle']
            self.data['BB_percent'] = (self.data['Close'] - self.data['BB_lower']) / (self.data['BB_upper'] - self.data['BB_lower'])
            
            # 计算RSI
            delta = self.data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            self.data['RSI'] = 100 - (100 / (1 + rs))
            
            # 计算成交量变化
            self.data['Volume_MA20'] = self.data['Volume'].rolling(window=20).mean()
            self.data['Volume_Ratio'] = self.data['Volume'] / self.data['Volume_MA20']
            
            return True
            
        except Exception as e:
            self.logger.error(f"计算指标时出错: {str(e)}")
            return False
    
    def generate_trading_signal(self) -> Optional[Dict]:
        """基于布林带生成交易信号"""
        try:
            if self.data is None or self.data.empty:
                return None
            
            latest = self.data.iloc[-1]
            prev = self.data.iloc[-2]
            
            # 布林带信号评分
            bb_score = 0
            if latest['Close'] < latest['BB_lower']:
                bb_score = 2  # 超卖
            elif latest['Close'] > latest['BB_upper']:
                bb_score = -2  # 超买
            
            # 布林带宽度变化信号
            bb_width_change = (latest['BB_width'] - prev['BB_width']) / prev['BB_width']
            if bb_width_change > 0.1:
                bb_score += 1  # 波动性增加
            elif bb_width_change < -0.1:
                bb_score -= 1  # 波动性减少
            
            # RSI信号
            rsi_score = 0
            if latest['RSI'] < 30:
                rsi_score = 2
            elif latest['RSI'] > 70:
                rsi_score = -2
            
            # 成交量信号
            volume_score = 0
            if latest['Volume_Ratio'] > 2:
                volume_score = 1
            elif latest['Volume_Ratio'] < 0.5:
                volume_score = -1
            
            # 计算总分
            total_score = bb_score + rsi_score + volume_score
            
            # 生成信号
            signal = "观望"
            if total_score >= 2:
                signal = "买入"
            elif total_score <= -2:
                signal = "卖出"
            
            return {
                "symbol": self.symbol,
                "current_price": latest['Close'],
                "bb_upper": latest['BB_upper'],
                "bb_lower": latest['BB_lower'],
                "bb_percent": latest['BB_percent'],
                "bb_width": latest['BB_width'],
                "rsi": latest['RSI'],
                "volume_ratio": latest['Volume_Ratio'],
                "price_change": ((latest['Close'] / prev['Close']) - 1) * 100,
                "score": total_score,
                "signal": signal
            }
            
        except Exception as e:
            self.logger.error(f"生成交易信号时出错: {str(e)}")
            return None

    def setup_watchlists(self) -> dict:
        """设置观察列表"""
        return {
            "主要指数": [
                "^DJI",     # 道琼斯工业指数
                "^IXIC",    # 纳斯达克综合指数
                "^GSPC",    # 标普500指数
                "^VIX",     # VIX波动率指数
                "^NDX",     # 纳斯达克100指数
                "^RUT"      # 罗素2000
            ],
            "商品ETF": [
                "GLD",      # SPDR黄金ETF
                "IAU",      # iShares黄金ETF
                "USO",      # 原油ETF
                "UCO",      # 2倍做多原油ETF
                "UNG",      # 天然气ETF
                "SLV",      # iShares白银ETF
                "PPLT",     # 铂金ETF
                "PALL",     # 钯金ETF
                "WEAT",     # 小麦ETF
                "CORN",     # 玉米ETF
                "SOYB",     # 大豆ETF
                "DBA"       # 农产品ETF
            ],
            # [之前提供的其他分组...]
        }

def main():
    # 示例使用
    symbol = "AAPL"  # 示例股票代码
    advisor = EnhancedTradingAdvisor(symbol)
    
    if advisor.fetch_data() and advisor.calculate_indicators():
        signal = advisor.generate_trading_signal()
        if signal:
            print(f"分析结果: {signal}")
    else:
        print("分析失败")

if __name__ == "__main__":
    main()