# 美股技术面简单分析工具 Alpha v 0.1

## 项目介绍
这是一个基于Python开发的股票纯技术面分析工具，目前主要用于美股市场分析。本工具通过分析多个技术指标，识别价格形态，结合成交量分析来生成交易信号，并以直观的HTML报告形式展示分析结果。

<img width="1114" alt="image" src="https://github.com/user-attachments/assets/8fbe8696-6beb-4955-b072-cd06b221f64c" />

<img width="1114" alt="image" src="https://github.com/user-attachments/assets/e71bbbb5-6bac-4cb5-96a2-cfb4b2444fee" />

<img width="1114" alt="image" src="https://github.com/user-attachments/assets/47cb66b3-3027-44ae-a002-99d162ca022a" />


## 核心功能

### 1. 技术指标分析
- RSI（相对强弱指标）：判断股票是否超买或超卖
- MACD（移动平均线趋同散度）：判断趋势变化和动量
- KDJ（随机指标）：提供超买超卖信号
- 布林带：分析价格波动范围
- 成交量分析：确认价格趋势的有效性

### 2. 形态识别
- 吞没形态：预测趋势反转
- 十字星：表示市场犹豫不决
- 锤子线：潜在的底部反转信号
- 上吊线：潜在的顶部反转信号

### 3. 信号系统
- 多指标交叉验证，确保信号可靠
- 信号可信度评级评分
- 清晰的买入/卖出建议

### 4. 分析报告
- 自动生成HTML格式报告
- 包含图表和详细分析说明
- 支持批量股票分析
  
<img width="1492" alt="image" src="https://github.com/user-attachments/assets/03fab51a-c669-448d-8aee-4f7ae9d38510" />

<img width="1415" alt="image" src="https://github.com/user-attachments/assets/60b1a55b-1a0f-47d5-911c-f67511c656b2" />


## 使用指南

### Windows 系统安装步骤

1. **安装Python环境**
   - 访问 [Python官网](https://www.python.org/downloads/)
   - 下载并安装Python 3.8或更高版本
   - 安装时勾选"Add Python to PATH"

2. **下载项目代码**
   - 点击本页面右上角的绿色"Code"按钮
   - 选择"Download ZIP"
   - 解压下载的文件到本地文件夹

3. **安装依赖包**
   - 打开命令提示符(Win+R输入cmd)
   - 进入项目目录：
     ```bash
     cd 项目所在路径
     ```
   - 安装依赖：
     ```bash
      pip install yfinance pandas numpy pytz plotly jinja2
     ```

4. **运行程序**
   - 在命令提示符中输入：
     ```bash
     python stock_analyzer.py
     ```

### Mac 系统安装步骤

1. **安装Python环境**
   - 打开终端
   - 安装Homebrew（如果没有）：
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
   - 安装Python：
     ```bash
     brew install python
     ```

2. **下载项目代码**
   - 点击本页面右上角的绿色"Code"按钮
   - 选择"Download ZIP"
   - 解压下载的文件

3. **安装依赖包**
   - 打开终端
   - 进入项目目录：
     ```bash
     cd 项目所在路径
     ```
   - 安装依赖：
     ```bash
     pip3 install yfinance pandas numpy pytz plotly jinja2
     ```

4. **运行程序**
   - 在终端中输入：
     ```bash
     source venv/bin/activate 
     python3 stock_analyzer.py
    
     ```
 - 或者在终端中输入，执行main.py,这是另一个快速分析结果：
  ```bash
     source venv/bin/activate 
     python3 main.py
    
     ```

## 常见问题解答

### 1. 如何输入股票代码？
- 直接输入股票代码，如：AAPL, GOOGL
- 支持同时分析多个股票（最多10个）
- 股票代码之间用空格分隔

### 2. 在哪里查看分析结果？
- 分析完成后会自动在reports文件夹下生成HTML报告
- 使用浏览器打开HTML文件即可查看详细分析

### 3. 报错怎么办？
- 确保网络连接正常
- 检查股票代码是否正确
- 确认是否在美股交易时间运行
- 查看logs文件夹下的日志文件获取详细错误信息

## 使用建议
1. 建议在美股交易时段运行，获取最新数据
2. 定期更新Python和依赖包
3. 分析结果仅供参考，请结合其他因素做出投资决策

## 注意事项
1. 本工具使用Yahoo Finance的数据，可能存在延迟
2. 分析结果仅供参考，不构成投资建议
3. 投资有风险，入市需谨慎

## 问题反馈
如果使用中遇到问题，欢迎提交Issue或Pull Request。

## 免责声明
本工具仅供学习和研究使用，不构成任何投资建议和风险控制依据。投资者应当对自己的投资决策负责。市场有风险，投资需谨慎。
