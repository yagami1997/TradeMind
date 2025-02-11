# 美股技术面简单分析工具 Alpha v 0.2


## 重要声明
1. 本工具99%的代码由Cursor自动生成，我仅做了少量的调整和优化，以及增加了一些注释和说明。
2. 本工具的分析结果仅供参考，不构成任何投资建议和风险控制依据。
3. 本工具完全开源、免费、无论是Clone、再开发甚至商业化我都不反对。
4. 后续其他二次开发版本和我无关，我亦不承担任何责任，本代码仓库仅供学习研究。
5. 市场有风险，投资需谨慎，成熟的交易者不会把决策简单归因于信息差或者技术操作，投资是修行。

## 更新日志

### 2025年2月11日更新

<img width="1224" alt="image" src="https://github.com/user-attachments/assets/a0d29ad1-31aa-4745-afca-15dfcbe72c92" />


- 解决了MACD值显示错误的算法BUG，修复了KDJ算法错误，解决了一个不重要的告警提示；
- 更新了股票决策的算法，目前操作结论偏积极，决策偏向布林带和RSI，这是我个人的偏好，大家可以根据自己偏好调整算法；
- 改进了HTML的显示方式，色彩搭配，采用大型卡片显示个股信息和操作指南，命令行分析完成之后，自动打开HTML报告，无需手动；
- 优化改进了其他问题，提高了分析速度；


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
- 自动生成HTML格式报告，未来会支持PDF格式
- 包含图表和详细分析说明
- 支持批量股票分析
  
<img width="1492" alt="image" src="https://github.com/user-attachments/assets/03fab51a-c669-448d-8aee-4f7ae9d38510" />

<img width="1415" alt="image" src="https://github.com/user-attachments/assets/60b1a55b-1a0f-47d5-911c-f67511c656b2" />


## 使用指南

### 环境要求
- Python 3.8 或更高版本
- pip 包管理工具
- 稳定的网络连接（访问 Yahoo Finance）

### Windows 系统安装步骤

1. **安装 Python**
   - 访问 [Python官网](https://www.python.org/downloads/)
   - 下载并安装 Python 3.8 或更高版本
   - 安装时勾选 "Add Python to PATH"

2. **下载项目**
   - 克隆或下载本项目到本地
   - 解压文件（如果是下载的 ZIP）

3. **安装依赖包**
   - 打开命令提示符 (Win + R，输入 cmd)
   - 进入项目目录：
     ```bash
     cd 项目所在路径
     ```
   - 安装所有依赖：
     ```bash
     pip install -r requirements.txt
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
   - 安装虚拟化环境
     ```bash
     python3 -m venv venv  #创建虚拟化环境
     source venv/bin/activate
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
     pip3 install -r requirements.txt

     ```

4. **运行程序**
    #确保安装了Venv虚拟化环境之后，先激活虚拟化，再运行程序

   - 在终端中输入：
     ```bash
     source venv/bin/activate 
     python stock_analyzer.py
    
     ```
  - 或者在终端中输入，执行main.py，这是另一个快速分析结果：
    ```bash
     source venv/bin/activate 
     python main.py
     
     ```

### 主要依赖包说明
- **yfinance**: Yahoo Finance 数据获取
- **pandas**: 数据处理和分析
- **numpy**: 数值计算
- **pandas_ta**: 技术分析指标库
- **scipy**: 科学计算
- **ib-insync**: Interactive Brokers API 接口
- **schedule**: 定时任务调度


### 可能遇到的问题和解决方案

1. **安装依赖失败**
   ```bash
   # 如果安装失败，可以尝试更新 pip
   # Windows:
   python -m pip install --upgrade pip
   # Mac:
   pip3 install --upgrade pip
   
   # 然后重新安装依赖
   pip install -r requirements.txt
   ```

2. **lxml 安装问题**
   - Windows: 可能需要安装 Visual C++ Build Tools
   - Mac: 可能需要安装 Xcode Command Line Tools
     ```bash
     xcode-select --install
     ```

3. **数据获取超时**
   - 检查网络连接
   - 确保能够访问 Yahoo Finance
   - 考虑使用代理服务器

## 常见问题解答

### 1. 如何输入股票代码？
- 直接输入股票代码，如：AAPL, GOOGL
- 支持同时分析多个股票（最多10个）
- 股票代码之间用空格分隔

### 2. 在哪里查看分析结果？
- 分析完成后会自动在reports文件夹下生成HTML报告，使用浏览器打开HTML文件即可查看详细分析
- 如果你对HTML报告形式，样式，色彩不满意，可以在stock_analyzer.py中修改，不会改代码就让Cursor帮你改
- 当然了，Cursor也可以帮你输出PDF格式的报告，也可以分目录分时间的输出，看你的想象力了


### 3. 报错怎么办？
- 确保网络连接正常
- 检查股票代码是否正确
- 确认是否在美股交易时间运行
- 查看logs文件夹下的日志文件获取详细错误信息

## 使用建议
1. 建议在美股交易时段运行，获取最新数据
2. 定期更新Python和依赖包
3. 分析结果仅供参考，请结合其他因素做出投资决策

### 更新说明
- 建议定期更新依赖包：
  ```bash
  pip install --upgrade -r requirements.txt
  ```
- 关注项目更新，及时同步最新代码

### 注意事项
1. 首次运行可能需要较长时间下载依赖包
2. 确保安装的 Python 版本兼容所有依赖
3. 如遇到 SSL 证书问题，请确保系统时间正确
4. 建议在虚拟环境中运行项目

## 问题反馈
如果使用中遇到问题，欢迎提交Issue或Pull Request。

## 免责声明
本工具仅供学习和研究使用，不构成任何投资建议和风险控制依据。该工具可能会深度行业研究员，公司研究员和注重价值投资的个人投资者提供价值。但是，无论如何，投资者应当对自己的投资决策独立负责。

最后强调：市场有风险，投资需谨慎，不要轻信任何信息，要有自己的独立价值体系和判断能力。
