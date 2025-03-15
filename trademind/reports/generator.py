"""
TradeMind Lite（轻量版）- 报告生成模块

本模块包含生成分析报告和性能图表的功能。
"""

from typing import Dict, List, Optional, Tuple, Union
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def generate_html_report(results: List[Dict], title: str = "股票分析报告", 
                         output_dir: Optional[Union[str, Path]] = None) -> str:
    """
    生成HTML分析报告
    
    参数:
        results: 分析结果列表
        title: 报告标题
        output_dir: 输出目录，如果为None则使用当前目录下的results文件夹
            
    返回:
        str: HTML报告文件路径
    """
    # 设置输出目录
    if output_dir is None:
        output_dir = Path.cwd() / "results"
    else:
        output_dir = Path(output_dir)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成时间戳和文件名
    la_time = datetime.now(pytz.timezone('America/Los_Angeles'))
    # 判断是否为夏令时
    is_dst = la_time.dst() != timedelta(0)
    tz_suffix = "PDT" if is_dst else "PST"
    
    # 生成文件名时间戳
    timestamp = la_time.strftime('%Y%m%d_%H%M%S')
    # 确保文件名不包含空格
    report_file = output_dir / f"stock_analysis_{timestamp}.html"
    
    # 格式化显示时间
    formatted_time = la_time.strftime(f'%Y-%m-%d %H:%M:%S ({tz_suffix} Time)')
    
    # HTML头部
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header-banner {{
                background-color: #3A7CA5; /* 更重的青蓝色 */
                padding: 30px 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .header-banner h1 {{
                color: white;
                font-weight: 600;
                margin-bottom: 10px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            }}
            .header-banner p {{
                color: rgba(255,255,255,0.9);
                font-size: 16px;
            }}
            .stock-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stock-card {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
                transition: transform 0.3s ease;
            }}
            .stock-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }}
            .stock-header {{
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                text-align: center;
            }}
            .stock-header h3 {{
                margin: 0;
                font-size: 18px;
            }}
            .stock-price {{
                font-size: 16px;
                font-weight: bold;
                margin-top: 5px;
            }}
            .stock-advice {{
                font-size: 14px;
                margin-top: 5px;
            }}
            .stock-body {{
                padding: 15px;
            }}
            .indicator-section {{
                margin-bottom: 15px;
            }}
            .indicators-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }}
            .indicator {{
                background-color: #f5f5f5;
                padding: 8px;
                border-radius: 5px;
            }}
            .indicator-name {{
                font-weight: bold;
                color: #555;
            }}
            .pattern-section {{
                margin-bottom: 15px;
                background-color: #FFE4E1 !important;
                padding: 12px;
                border-radius: 5px;
            }}
            .patterns-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 10px;
            }}
            .pattern-tag {{
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
            }}
            .signals-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 10px;
            }}
            .signal-tag {{
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
            }}
            .signal-buy {{
                background-color: #e8f5e9;
                color: #2e7d32;
            }}
            .signal-sell {{
                background-color: #ffebee;
                color: #c62828;
            }}
            .signal-neutral {{
                background-color: #fff8e1;
                color: #f57f17;
            }}
            .advice-section {{
                margin-bottom: 15px;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 5px;
            }}
            .backtest-results {{
                margin-top: 15px;
            }}
            .backtest-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .backtest-table td {{
                padding: 5px;
                border-bottom: 1px solid #eee;
                font-size: 12px;
            }}
            .backtest-note {{
                margin-top: 10px;
                padding: 10px;
                background-color: #fff8e1;
                border-radius: 5px;
                font-size: 12px;
                color: #555;
            }}
            .backtest-note ul {{
                margin: 5px 0;
                padding-left: 20px;
            }}
            .no-patterns {{
                color: #999;
                font-style: italic;
            }}
            .confidence {{
                font-size: 12px;
                color: #777;
                margin-top: 5px;
            }}
            .manual-card {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 30px;
            }}
            .manual-title {{
                font-weight: 600;
                font-size: 20px;
                margin-bottom: 15px;
                color: #2E8B57;
                border-bottom: 2px solid #88BDBC;
                padding-bottom: 8px;
            }}
            .manual-section {{
                margin-bottom: 15px;
            }}
            .manual-section-title {{
                font-weight: 600;
                margin-bottom: 8px;
                color: #2E8B57;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                margin-bottom: 20px;
                color: #666;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                position: relative;
            }}
            .footer p {{
                margin-bottom: 0;
            }}
            .watermark {{
                color: #9E9E9E; /* 从#e0e0e0改为#9E9E9E，更深的灰色 */
                font-size: 14px;
                font-style: italic;
                text-align: center;
                margin-top: 15px;
                line-height: 1.5;
                font-weight: 400; /* 从300改为400，更粗一些 */
                letter-spacing: 0.5px;
            }}
            .risk-banner {{
                margin-top: 30px;
                padding: 18px 20px;
                background-color: #E8EAF6; /* 深青蓝色背景，呼应整体风格 */
                border-radius: 8px;
                color: #37474F; /* 深青灰色文字 */
                font-size: 14px;
                line-height: 1.6;
                text-align: center; /* 文本居中 */
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .risk-banner h4 {{
                margin-top: 0;
                margin-bottom: 10px;
                color: #1A237E; /* 深蓝色标题 */
                font-weight: 600;
            }}
            .risk-banner p {{
                margin-bottom: 8px;
            }}
            @media (max-width: 768px) {{
                .stock-grid {{
                    grid-template-columns: 1fr;
                }}
                .indicator-section {{
                    height: auto;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-banner">
                <h1>{title}</h1>
                <p>生成时间: {formatted_time}</p>
            </div>
            
            <div class="stock-grid">
    """
    
    # 检查是否有结果数据
    if not results:
        html += """
            </div>
            <div class="no-data">
                <p>没有可用的分析数据</p>
            </div>
        """
    else:
        # 保持原始顺序生成股票卡片
        for result in results:
            # 使用generate_stock_card_html函数生成股票卡片
            card = generate_stock_card_html(result)
            html += card
    
    # HTML尾部 - 添加回测说明
    html += """
            </div>
            
            <div class="manual-card">
                <div class="manual-title">分析方法说明</div>
                
                <div class="manual-section">
                    <div class="manual-section-title">技术指标分析</div>
                    <p>本工具采用多系统量化模型进行技术分析，基于以下权威交易系统：</p>
                    <ul>
                        <li><strong>趋势确认系统</strong> - 基于Dow理论和Appel的MACD原始设计，通过分析价格趋势和动量变化，识别市场主导方向。</li>
                        <li><strong>动量反转系统</strong> - 基于Wilder的RSI和Lane的随机指标，捕捉市场超买超卖状态和潜在反转点。</li>
                        <li><strong>价格波动系统</strong> - 基于Bollinger带和Donchian通道，分析价格波动性和突破模式。</li>
                    </ul>
                </div>
                
                <div class="manual-section">
                    <div class="manual-section-title">交易建议生成</div>
                    <p>交易建议基于多因子模型理论，综合评估各系统信号，置信度表示信号强度：</p>
                    <ul>
                        <li><strong>强烈买入/卖出</strong>: 置信度≥75%或≤25%，表示多个系统高度一致的信号</li>
                        <li><strong>建议买入/卖出</strong>: 置信度在60-75%或25-40%之间，表示系统间存在较强共识</li>
                        <li><strong>观望</strong>: 置信度在40-60%之间，表示系统间信号不明确或相互矛盾</li>
                    </ul>
                </div>
                
                <div class="manual-section">
                    <div class="manual-section-title">回测分析方法</div>
                    <p>回测采用行业标准方法论，包括：</p>
                    <ul>
                        <li><strong>Markowitz投资组合理论</strong> - 科学的风险管理方法，优化资产配置和风险控制</li>
                        <li><strong>Kestner交易系统评估</strong> - 专业的回撤计算和系统性能评估方法</li>
                        <li><strong>Sharpe/Sortino比率</strong> - 标准化风险调整收益指标，衡量策略的风险回报效率</li>
                        <li><strong>Van K. Tharp头寸模型</strong> - 优化资金管理和头寸规模，控制单笔交易风险</li>
                    </ul>
                    
                    <div style="margin-top: 15px; background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #4CAF50;">
                        <p><strong>回测结果为零的说明：</strong></p>
                        <p>当回测结果显示为零时，这并不意味着策略无效，而是表明在当前数据和参数条件下没有产生交易。可能的原因包括：</p>
                        <ul>
                            <li>历史数据量不足（少于50个交易日）</li>
                            <li>策略没有生成买入或卖出信号</li>
                            <li>信号和价格数据不匹配</li>
                            <li>当前参数设置不适合该股票特性</li>
                        </ul>
                        <p>如需更准确的回测结果，请尝试：</p>
                        <ul>
                            <li>使用更长的历史数据（至少6个月）</li>
                            <li>调整技术指标参数以适应特定股票</li>
                            <li>结合多种技术指标和形态分析</li>
                        </ul>
                    </div>
                </div>
                
                <div class="manual-section">
                    <div class="manual-section-title">使用建议</div>
                    <p>本工具提供的分析结果应作为投资决策的参考，而非唯一依据。建议结合基本面分析、市场环境和个人风险偏好综合考量。交易策略的有效性可能随市场环境变化而改变，请定期评估策略表现。</p>
                    <div style="background-color: #FFF3E0; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <strong>免责声明：</strong> 本工具仅供参考，不构成投资建议。投资有风险，入市需谨慎。
                    </div>
                </div>
            </div>
            
            <div class="risk-banner">
                <h4>风险提示:</h4>
                <p>本报告基于雅虎财经API技术分析生成，仅供学习，不构成任何投资建议。</p>
                <p>投资者应当独立判断，自主决策，自行承担投资风险，投资是修行，不要指望单边信息。</p>
                <p>过往市场表现不代表未来收益，市场有较大风险，投资需理性谨慎。</p>
            </div>
            
            <div class="footer">
                <p>TradeMind Lite Beta 0.3.0 © 2025 | <a href="https://github.com/yourusername/trademind" target="_blank">GitHub</a></p>
                <div class="watermark">
                    In this cybernetic realm, we shall ultimately ascend to digital rebirth<br>
                    Long live the Free Software Movement!
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 保存HTML报告
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return str(report_file)


def generate_performance_charts(trades: List[Dict], equity: List[float], 
                               dates: pd.DatetimeIndex, output_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    生成性能图表
    
    参数:
        trades: 交易记录列表
        equity: 权益曲线
        dates: 日期索引
        output_dir: 输出目录，如果为None则使用当前目录下的results/charts文件夹
        
    返回:
        Dict[str, str]: 图表文件路径字典
    """
    # 设置输出目录
    if output_dir is None:
        output_dir = Path.cwd() / "results" / "charts"
    else:
        output_dir = Path(output_dir)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 设置图表样式
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("muted")
    
    # 创建图表文件路径字典
    chart_paths = {}
    
    # 如果没有交易记录，返回空字典
    if not trades or len(equity) < 2:
        return chart_paths
    
    # 1. 绘制权益曲线图
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 创建日期索引
    if len(equity) > len(dates):
        # 如果权益曲线比日期索引长，可能是因为包含了初始资金
        equity_dates = pd.date_range(start=dates[0] - pd.Timedelta(days=1), periods=len(equity), freq='D')
    else:
        equity_dates = dates[-len(equity):]
    
    # 绘制权益曲线
    ax.plot(equity_dates, equity, linewidth=2, color='#1e88e5')
    
    # 添加标题和标签
    ax.set_title('权益曲线', fontsize=16, pad=20)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('资金', fontsize=12)
    
    # 格式化x轴日期
    fig.autofmt_xdate()
    
    # 添加网格线
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 保存图表
    equity_chart_path = output_dir / f"equity_curve_{timestamp}.png"
    plt.tight_layout()
    plt.savefig(equity_chart_path, dpi=100)
    plt.close(fig)
    
    chart_paths['equity_curve'] = str(equity_chart_path)
    
    # 2. 绘制月度收益柱状图
    if trades:
        # 计算月度收益
        monthly_returns = {}
        for trade in trades:
            month_key = trade['exit_date'].strftime('%Y-%m')
            if month_key not in monthly_returns:
                monthly_returns[month_key] = 0
            monthly_returns[month_key] += trade['profit']
        
        # 排序月份
        months = sorted(monthly_returns.keys())
        profits = [monthly_returns[month] for month in months]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 设置柱状图颜色
        colors = ['#43a047' if p > 0 else '#e53935' for p in profits]
        
        # 绘制柱状图
        ax.bar(months, profits, color=colors)
        
        # 添加标题和标签
        ax.set_title('月度收益', fontsize=16, pad=20)
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('收益 ($)', fontsize=12)
        
        # 旋转x轴标签
        plt.xticks(rotation=45)
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # 保存图表
        monthly_chart_path = output_dir / f"monthly_returns_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(monthly_chart_path, dpi=100)
        plt.close(fig)
        
        chart_paths['monthly_returns'] = str(monthly_chart_path)
    
    # 3. 绘制交易类型饼图
    if trades:
        # 统计交易类型
        exit_reasons = {}
        for trade in trades:
            reason = trade['exit_reason']
            if reason not in exit_reasons:
                exit_reasons[reason] = 0
            exit_reasons[reason] += 1
        
        # 绘制饼图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 设置颜色
        colors = sns.color_palette('muted', len(exit_reasons))
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            exit_reasons.values(), 
            labels=exit_reasons.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        
        # 设置字体大小
        plt.setp(autotexts, size=10, weight="bold")
        
        # 添加标题
        ax.set_title('交易平仓原因分布', fontsize=16, pad=20)
        
        # 保存图表
        reasons_chart_path = output_dir / f"exit_reasons_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(reasons_chart_path, dpi=100)
        plt.close(fig)
        
        chart_paths['exit_reasons'] = str(reasons_chart_path)
    
    # 4. 绘制盈亏分布直方图
    if trades:
        # 提取交易盈亏
        profits = [trade['profit'] for trade in trades]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制直方图
        sns.histplot(profits, bins=20, kde=True, color='#1e88e5', ax=ax)
        
        # 添加标题和标签
        ax.set_title('交易盈亏分布', fontsize=16, pad=20)
        ax.set_xlabel('盈亏 ($)', fontsize=12)
        ax.set_ylabel('频率', fontsize=12)
        
        # 添加均值线
        mean_profit = np.mean(profits)
        ax.axvline(mean_profit, color='#e53935', linestyle='--', linewidth=2, 
                  label=f'平均值: ${mean_profit:.2f}')
        
        # 添加图例
        ax.legend()
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 保存图表
        profit_dist_chart_path = output_dir / f"profit_distribution_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(profit_dist_chart_path, dpi=100)
        plt.close(fig)
        
        chart_paths['profit_distribution'] = str(profit_dist_chart_path)
    
    return chart_paths 

def generate_stock_card_html(result: Dict) -> str:
    """生成单个股票卡片的HTML"""
    # 获取股票代码和名称，兼容不同的键名
    stock_code = result.get('stock_code', result.get('symbol', '未知'))
    stock_name = result.get('stock_name', result.get('name', '未知'))
    
    # 处理股价显示，确保最多显示两位小数
    try:
        current_price = float(result.get('last_price', result.get('price', 0)))
        current_price_display = f"{current_price:.2f}"
    except (ValueError, TypeError):
        current_price_display = str(result.get('last_price', result.get('price', 'N/A')))
    
    # 获取价格变化百分比 - 完全重写这部分逻辑
    try:
        # 直接从price_change_pct字段获取
        if 'price_change_pct' in result and result['price_change_pct'] is not None:
            if isinstance(result['price_change_pct'], (int, float)) and not pd.isna(result['price_change_pct']) and not np.isinf(result['price_change_pct']):
                price_change_pct = float(result['price_change_pct'])
                print(f"从price_change_pct字段获取涨跌幅: {price_change_pct:.2f}%")
            else:
                price_change_pct = 0.0
                print(f"price_change_pct字段无效: {result['price_change_pct']}, 使用默认值0.0%")
        # 从change_percent获取
        elif 'change_percent' in result and result['change_percent'] is not None:
            price_change_pct = float(result['change_percent'])
            print(f"从change_percent字段获取涨跌幅: {price_change_pct:.2f}%")
        # 从price_change和prev_close计算
        elif 'price_change' in result and 'prev_close' in result and result['prev_close'] is not None and float(result['prev_close']) > 0:
            price_change = float(result['price_change'])
            prev_close = float(result['prev_close'])
            price_change_pct = (price_change / prev_close) * 100
            print(f"从price_change和prev_close计算涨跌幅: {price_change_pct:.2f}%")
        # 从change字段获取
        elif 'change' in result and result['change'] is not None and isinstance(result['change'], (int, float)):
            price_change_pct = float(result['change'])
            print(f"从change字段获取涨跌幅: {price_change_pct:.2f}%")
        else:
            # 尝试从当前价格和前一天收盘价计算
            if 'price' in result and 'prev_close' in result and result['prev_close'] is not None and float(result['prev_close']) > 0:
                current = float(result['price'])
                prev = float(result['prev_close'])
                price_change_pct = ((current - prev) / prev) * 100
                print(f"从price和prev_close计算涨跌幅: {price_change_pct:.2f}%")
            else:
                price_change_pct = 0.0
                print("无法获取涨跌幅数据，使用默认值0.0%")
    except Exception as e:
        price_change_pct = 0.0
        print(f"处理涨跌幅时出错: {str(e)}，使用默认值0.0%")
    
    # 确保价格变化百分比不是NaN或无穷大
    if pd.isna(price_change_pct) or np.isinf(price_change_pct):
        price_change_pct = 0.0
        print("涨跌幅为NaN或无穷大，使用默认值0.0%")
    
    # 设置价格变化的颜色和符号 - 使用美股市场习惯（红跌绿涨）
    if price_change_pct > 0.001:  # 使用小阈值避免浮点误差
        price_change_color = "#4CAF50"  # 绿色（美股市场上涨用绿色）
        price_change_symbol = "▲"
    elif price_change_pct < -0.001:  # 使用小阈值避免浮点误差
        price_change_color = "#F44336"  # 红色（美股市场下跌用红色）
        price_change_symbol = "▼"
    else:
        price_change_color = "#757575"  # 灰色
        price_change_symbol = "■"
    
    print(f"最终涨跌幅: {price_change_pct:.2f}%, 颜色: {price_change_color}, 符号: {price_change_symbol}")
    
    # 获取建议，使用get方法避免KeyError
    advice = result.get('advice', {})
    advice_text = advice.get('advice', advice.get('type', '观望'))
    confidence = advice.get('confidence', 50)
    # 使用get方法获取explanation，避免KeyError
    explanation = advice.get('explanation', '')
    
    # 根据建议设置背景颜色和文本
    if '强烈买入' in advice_text:
        header_bg = '#008000'  # 强烈买入 - 深绿色
        advice_text = '强烈买入'
        advice_bg = '#008000'
        advice_color = 'white'
    elif '买入' in advice_text:
        header_bg = '#00FF00'  # 买入 - 鲜绿色
        advice_text = '买入'
        advice_bg = '#00FF00'
        advice_color = 'black'  # 鲜绿色背景配深色文字更易读
    elif '观望偏多' in advice_text:
        header_bg = '#32CD32'  # 观望偏多 - 酸橙绿
        advice_text = '观望偏多'
        advice_bg = '#32CD32'
        advice_color = 'white'
    elif '观望偏空' in advice_text:
        header_bg = '#FF6347'  # 观望偏空 - 番茄红
        advice_text = '观望偏空'
        advice_bg = '#FF6347'
        advice_color = 'white'
    elif '卖出' in advice_text:
        header_bg = '#FF0000'  # 卖出 - 红色
        advice_text = '卖出'
        advice_bg = '#FF0000'
        advice_color = 'white'
    elif '强烈卖出' in advice_text:
        header_bg = '#8B0000'  # 强烈卖出 - 深红色
        advice_text = '强烈卖出'
        advice_bg = '#8B0000'
        advice_color = 'white'
    else:
        header_bg = '#F4A460'  # 观望 - 沙褐色
        advice_text = '观望'
        advice_bg = '#F4A460'
        advice_color = 'white'
    
    # 处理技术指标 - 确保正确获取和显示
    indicators = result.get('indicators', {})
    
    # 处理RSI指标
    rsi_value = indicators.get('rsi')
    rsi_display = f"{rsi_value:.1f}" if isinstance(rsi_value, (int, float)) and not pd.isna(rsi_value) else "N/A"
    
    # 处理KDJ指标 - 确保正确获取嵌套结构
    kdj_data = {}
    if 'kdj' in indicators and isinstance(indicators['kdj'], dict):
        kdj_data = indicators['kdj']
    elif 'kdj' in indicators and isinstance(indicators['kdj'], (list, tuple)) and len(indicators['kdj']) >= 3:
        kdj_data = {'k': indicators['kdj'][0], 'd': indicators['kdj'][1], 'j': indicators['kdj'][2]}
    
    if kdj_data:
        k_value = kdj_data.get('k')
        d_value = kdj_data.get('d')
        j_value = kdj_data.get('j')
        
        k_display = f"{k_value:.1f}" if isinstance(k_value, (int, float)) and not pd.isna(k_value) else "N/A"
        d_display = f"{d_value:.1f}" if isinstance(d_value, (int, float)) and not pd.isna(d_value) else "N/A"
        j_display = f"{j_value:.1f}" if isinstance(j_value, (int, float)) and not pd.isna(j_value) else "N/A"
        
        kdj_html = f"K: {k_display} | D: {d_display} | J: {j_display}"
    else:
        kdj_html = "N/A"
    
    # 处理MACD指标 - 确保正确获取嵌套结构
    macd_data = {}
    if 'macd' in indicators and isinstance(indicators['macd'], dict):
        macd_data = indicators['macd']
    elif 'macd' in indicators and isinstance(indicators['macd'], (list, tuple)) and len(indicators['macd']) >= 3:
        macd_data = {'macd': indicators['macd'][0], 'signal': indicators['macd'][1], 'hist': indicators['macd'][2]}
    
    if macd_data:
        macd_value = macd_data.get('macd')
        signal_value = macd_data.get('signal')
        hist_value = macd_data.get('hist')
        
        macd_display = f"{macd_value:.3f}" if isinstance(macd_value, (int, float)) and not pd.isna(macd_value) else "N/A"
        signal_display = f"{signal_value:.3f}" if isinstance(signal_value, (int, float)) and not pd.isna(signal_value) else "N/A"
        hist_display = f"{hist_value:.3f}" if isinstance(hist_value, (int, float)) and not pd.isna(hist_value) else "N/A"
        
        macd_html = f"MACD: {macd_display} | Signal: {signal_display} | Hist: {hist_display}"
    else:
        macd_html = "N/A"
    
    # 处理布林带 - 确保正确获取嵌套结构
    bollinger_data = {}
    if 'bollinger' in indicators and isinstance(indicators['bollinger'], dict):
        bollinger_data = indicators['bollinger']
    elif 'bollinger' in indicators and isinstance(indicators['bollinger'], (list, tuple)) and len(indicators['bollinger']) >= 3:
        bollinger_data = {'upper': indicators['bollinger'][0], 'middle': indicators['bollinger'][1], 'lower': indicators['bollinger'][2]}
    
    if bollinger_data:
        upper = bollinger_data.get('upper')
        middle = bollinger_data.get('middle')
        lower = bollinger_data.get('lower')
        
        upper_display = f"{upper:.2f}" if isinstance(upper, (int, float)) and not pd.isna(upper) else "N/A"
        middle_display = f"{middle:.2f}" if isinstance(middle, (int, float)) and not pd.isna(middle) else "N/A"
        lower_display = f"{lower:.2f}" if isinstance(lower, (int, float)) and not pd.isna(lower) else "N/A"
        
        bollinger_html = f"上轨: {upper_display} | 中轨: {middle_display} | 下轨: {lower_display}"
    else:
        bollinger_html = "N/A"
    
    # 获取K线形态 - 严格区分K线形态和技术指标信号
    patterns = result.get('patterns', [])
    pattern_html = ""
    
    # 严格筛选K线形态，排除任何可能的技术指标信号
    if patterns and len(patterns) > 0:
        has_valid_patterns = False
        for pattern in patterns:
            if isinstance(pattern, dict):
                pattern_name = pattern.get('name', '')
                pattern_confidence = pattern.get('confidence', '')
                # 严格确保这是一个K线形态而不是技术指标信号
                if pattern_name and not any(keyword in pattern_name.lower() for keyword in ['macd', 'rsi', 'kdj', 'bollinger', '零轴', '金叉', '死叉', '超买', '超卖']):
                    has_valid_patterns = True
                    # 根据形态类型设置不同的底色
                    bg_color = "#DEB887"  # 默认中性振荡信号用#DEB887
                    
                    # 积极信号用#3CB371
                    if any(keyword in pattern_name for keyword in ["看涨", "启明星", "晨星", "锤子", "反转", "上升"]):
                        bg_color = "#3CB371"
                    # 悲观信号用#F08080
                    elif any(keyword in pattern_name for keyword in ["看跌", "黄昏星", "暮星", "吊颈", "下降"]):
                        bg_color = "#F08080"
                    # 中性信号用#DEB887
                    elif any(keyword in pattern_name for keyword in ["十字星", "平头", "震荡"]):
                        bg_color = "#DEB887"
                    
                    pattern_html += f'<div style="display: inline-block; margin: 2px; padding: 5px 10px; background-color: {bg_color} !important; color: #333; border-radius: 4px; font-size: 13px;">{pattern_name} ({pattern_confidence}%)</div>'
        
        if not has_valid_patterns:
            pattern_html = '<div style="text-align: center; font-style: italic; color: #555; background-color: #FFE4E1 !important; padding: 8px; border-radius: 4px; border: 1px dashed #E8D4D1;">无明显K线形态</div>'
    else:
        pattern_html = '<div style="text-align: center; font-style: italic; color: #555; background-color: #FFE4E1 !important; padding: 8px; border-radius: 4px; border: 1px dashed #E8D4D1;">无明显K线形态</div>'
    
    # 获取信号 - 严格筛选技术指标信号
    signals = []
    if result.get('signals'):
        signals = result['signals']
    elif result.get('advice', {}).get('signals'):
        signals = result['advice']['signals']
    else:
        signals = []  # 如果没有信号，使用空列表作为默认值
    
    # 生成信号标签HTML - 使用更清晰的配色方案
    signals_html = ""
    for signal in signals:
        # 严格筛选技术指标信号
        if any(keyword in signal.lower() for keyword in ['macd', 'rsi', 'kdj', 'bollinger', '零轴', '金叉', '死叉', '超买', '超卖']):
            if "买入" in signal or "看涨" in signal or "零轴以上" in signal or "金叉" in signal or "超卖" in signal:
                # 买入/看涨信号 - 使用柔和的绿色
                signal_bg = "#E8F5E9"  # 非常浅的绿色背景
                signal_color = "#2E7D32"  # 深绿色文字
                signal_border = "#A5D6A7"  # 浅绿色边框
            elif "卖出" in signal or "看跌" in signal or "零轴以下" in signal or "死叉" in signal or "超买" in signal:
                # 卖出/看跌信号 - 使用柔和的红色
                signal_bg = "#FFEBEE"  # 非常浅的红色背景
                signal_color = "#C62828"  # 深红色文字
                signal_border = "#EF9A9A"  # 浅红色边框
            else:
                # 中性信号 - 使用柔和的灰色
                signal_bg = "#F5F5F5"  # 非常浅的灰色背景
                signal_color = "#616161"  # 深灰色文字
                signal_border = "#E0E0E0"  # 浅灰色边框
            
            signals_html += f'<span style="display: inline-block; margin: 2px; padding: 3px 8px; background-color: {signal_bg}; color: {signal_color}; border: 1px solid {signal_border}; border-radius: 4px; font-size: 12px;">{signal}</span>'
    
    # 获取回测结果
    backtest = result.get('backtest', {})
    
    # 构建股票卡片HTML - 明确区分K线形态和技术指标
    stock_card_html = f"""
    <div class="stock-card" style="border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <div class="stock-header" style="background-color: {header_bg}; padding: 12px 15px; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 18px;">{stock_name} ({stock_code})</h3>
                <div style="text-align: right;">
                    <div class="stock-price" style="font-size: 18px; font-weight: bold;">${current_price_display}</div>
                    <div style="color: {price_change_color}; font-size: 14px;">{price_change_symbol} {price_change_pct:.2f}%</div>
                </div>
            </div>
        </div>
        <div class="stock-body" style="padding: 12px;">
            <div style="background-color: #FFE4E1; padding: 12px; border-radius: 5px; margin-bottom: 12px;">
                <h4 style="margin-top: 0; margin-bottom: 8px; color: #424242; border-bottom: 1px solid #E8D4D1; padding-bottom: 4px; font-size: 15px;">K线形态分析</h4>
                <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 8px; font-size: 14px; margin-bottom: 10px;">
                    {pattern_html}
                </div>
            </div>
            
            <div class="indicator-section" style="background-color: #f0f7ff; padding: 12px; border-radius: 5px; margin-bottom: 12px;">
                <h4 style="margin-top: 0; margin-bottom: 8px; color: #1565c0; border-bottom: 1px solid #bbdefb; padding-bottom: 4px; font-size: 15px;">技术指标分析</h4>
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px; align-items: center; font-size: 14px;">
                    <div style="font-weight: bold;">RSI (14日)</div>
                    <div style="text-align: right;">{rsi_display}</div>
                    
                    <div style="font-weight: bold;">KDJ (9日)</div>
                    <div style="text-align: right;">{kdj_html}</div>
                    
                    <div style="font-weight: bold;">MACD (12,26,9)</div>
                    <div style="text-align: right;">{macd_html}</div>
                    
                    <div style="font-weight: bold;">布林带 (20日)</div>
                    <div style="text-align: right;">{bollinger_html}</div>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; justify-content: center;">
                    {signals_html}
                </div>
            </div>
            
            <div class="advice-section" style="background-color: #f9f9f9; padding: 12px; border-radius: 5px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                    <div style="background-color: {advice_bg}; color: {advice_color}; padding: 6px 18px; font-weight: bold; border-radius: 5px; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        {advice_text}
                    </div>
                    <div style="margin-left: 12px; font-size: 15px; font-weight: bold;">
                        置信度: {confidence}%
                    </div>
                </div>
                {f'<p>{explanation}</p>' if explanation else ''}
            </div>
            
            <div class="backtest-results" style="background-color: #fff8e1; padding: 12px; border-radius: 5px;">
                <h4 style="margin-top: 0; margin-bottom: 8px; color: #f57f17; border-bottom: 1px solid #ffe0b2; padding-bottom: 4px; font-size: 15px;">回测结果</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">总交易次数</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('total_trades', 0)}</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">胜率</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('win_rate', 0)}%</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">平均收益</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">${backtest.get('avg_profit', 0)}</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">盈亏比</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('profit_factor', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">最大收益</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">${backtest.get('max_profit', 0)}</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">最大亏损</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">${backtest.get('max_loss', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">最大回撤</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('max_drawdown', 0)}%</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">连续亏损次数</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('consecutive_losses', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">平均持仓天数</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('avg_hold_days', 0)}</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2;">总收益率</td>
                        <td style="padding: 4px; border-bottom: 1px solid #ffe0b2; text-align: right;">{backtest.get('final_return', 0)}%</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;">Sharpe比率</td>
                        <td style="padding: 4px; text-align: right;">{backtest.get('sharpe_ratio', 0):.2f}</td>
                        <td style="padding: 4px;">Sortino比率</td>
                        <td style="padding: 4px; text-align: right;">{backtest.get('sortino_ratio', 0):.2f}</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
    """
    
    return stock_card_html 