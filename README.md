# TradeMind Alpha v0.3 重构版

## ⚠️⚠️⚠️重要声明
1. 本工具99%的代码由Cursor自动生成，Coding模型Claude3.5，当然也可以用别的。对我来说，更像个赛博念经的，负责规划设计调试。
2. 本工具的分析结果仅供参考，仅代表我不成熟的策略设计思路，所以不构成任何投资建议和风险控制依据。
3. 本工具完全开源、免费、无论是Clone、再开发甚至商业化我都不反对，但必须遵守GPLv3许可证协议。
4. 后续其他二次开发版本和我无关，我亦不承担任何责任，本代码仓库仅供学习研究。
5. 市场有风险，投资需谨慎，成熟的交易者不会把决策简单归因于信息差或者技术操作，投资是修行。
---
## 更新日志

### 2025年2月28日Dev更新（PST太平洋时间）
⚠️：我知道很多人都讨厌在单位给领导们写日报和周报，但我发现，如果我们不让AI写软件工程控制文档，周报和日报，它们大概率会野马脱缰一样的瞎写，上下文管理极差，所以今天花了好几个小时规范Claude 3.7的行为，形成了相关的控制文件和周报，日报模板，并且用PST时间戳来控制我们所有的开发工作，做到一切工作有迹可循，一切想法都做备忘录。
#### 1. 文档结构优化
- 统一了项目文档管理体系
  * 建立了完整的文档控制体系
  * 规范了文档命名和格式标准
  * 制定了文档更新和维护流程
- 完善了目录结构说明
  * 优化了文档层次结构
  * 增加了快速开始指南
  * 完善了最佳实践说明
- 更新了所有模块的状态标记
  * 明确了文档状态定义
  * 统一了状态标记格式
  * 建立了状态更新机制

#### 2. 项目控制体系建设
- 完善了项目控制文档体系
  * 创建了主控文件、日报和周报模板
  * 规范了时间戳格式和获取方式
  * 建立了文档间的关联机制
- 制定了文档管理规范
  * 明确了更新频率要求
  * 建立了文档审查机制
  * 规范了协作流程
- 增强了安全管理
  * 制定了信息安全规范
  * 建立了访问控制机制
  * 完善了敏感信息处理流程

#### 3. 架构决策记录
- 确认了tech_indicator_calculator.py的位置
- 完善了缓存系统架构说明
- 优化了时间同步管理机制

#### 4. 代码优化
- 优化了market_sources.py的错误处理
- 完善了backtest_manager.py的HTML报告生成
- 清理了未使用的导入

#### 5. 系统集成
- 完善了NTP服务器同步机制
- 优化了项目的时间戳管理
- 集成了文档控制系统
  * 实现了模板自动更新
  * 建立了文档版本控制
  * 优化了文档同步机制

#### 6. 遗留问题
- [ ] 缓存生命周期管理机制待实现
- [ ] 并发处理优化计划待制定
- [ ] 性能瓶颈评估待进行
- [ ] 文档自动化工具开发
  * 时间戳自动更新
  * 模板自动同步
  * 文档格式检查

---

### 🔔2025年2月27日TradeMind Dev进度公告
- 全面重新梳理项目结构和交互逻辑，确定目录树
- 完成核心策略代码的初步开发，设计Main.py主程序的功能
- 确定相关模块的定义和说明，为了维持项目稳定，中期内不打算修改目录结构和已经存在的代码文件名和相关定义
- 当前项目目录树及说明：

#### 🏦TradeMind Dev项目结构

```plaintext
📂 TradeMind/                        # 💹 美股技术面分析系统
├── 📂 core/                         # 🧠 核心模块目录
│   ├── 📜 __init__.py               # 包初始化，导出主要组件
│   ├── 📜 backtest_manager.py       # 回测管理器：控制回测流程和结果分析
│   ├── 📜 config.py                 # 配置管理：全局配置和参数设置
│   ├── 📜 data_manager.py           # 数据管理器：数据获取和缓存控制
│   ├── 📜 data_source.py            # 数据源抽象基类：定义统一数据接口
│   ├── 📜 data_source_factory.py    # 数据源工厂：创建和管理数据源实例
│   ├── 📜 exceptions.py             # 异常定义：统一的错误处理系统
│   ├── 📜 market_calendar.py        # 交易日历：管理交易时间和假期
│   ├── 📜 market_sources.py         # 市场数据源：具体数据源实现
│   ├── 📜 market_types.py           # 市场类型：定义市场和交易所类型
│   ├── 📜 strategy_manager.py       # 策略管理器：策略加载和执行控制
│   └── 📜 technical_analyzer.py     # 技术分析器：实现技术指标计算
│
├── 📂 strategies/                   # ⚡ 交易策略实现
│   ├── 📜 __init__.py               # 策略包初始化
│   ├── 📜 backtester.py             # 回测器核心实现
│   ├── 📜 enhanced_trading_advisor.py  # 增强型交易顾问
│   ├── 📜 stock_analyzer.py         # 股票分析器
│   ├── 📜 advanced_analysis.py      # 高级分析工具
│   └── 📜 tech_indicator_calculator.py # 技术指标计算器
│
├── 📂 utils/                        # 🛠️ 工具函数目录
│   ├── 📜 __init__.py               # 工具包初始化
│   ├── 📜 data_utils.py             # 数据处理工具
│   ├── 📜 time_utils.py             # 时间处理工具
│   └── 📜 math_utils.py             # 数学计算工具
│
├── 📂 config/                       # ⚙️ 配置文件目录
│   ├── 📜 backtest_config.json      # 回测配置
│   ├── 📜 market_config.json        # 市场配置
│   └── 📜 logging_config.json       # 日志配置
│
├── 📂 reports/                      # 📊 报告输出目录
│   ├── 📂 templates/                # 报告模板
│   └── 📂 output/                   # 报告输出
│       ├── 📂 backtest/             # 回测报告
│       └── 📂 analysis/             # 分析报告
│
├── 📂 tests/                        # ✅ 测试目录
│   ├── 📂 unit/                     # 单元测试
│   │   ├── 📜 test_backtester.py    # 回测器测试
│   │   ├── 📜 test_data_manager.py  # 数据管理测试
│   │   └── 📜 test_strategies.py    # 策略测试
│   └── 📂 integration/              # 集成测试
│
├── 📂 results/                      # 📈 结果输出目录
│   ├── 📂 backtest/                 # 回测结果
│   └── 📂 optimization/             # 优化结果
│
├── 📂 logs/                         # 📝 日志目录
│   ├── 📜 backtest.log              # 回测日志
│   └── 📜 trading.log               # 交易日志
│
├── 📂 data/                         # 💾 数据存储目录
│   ├── 📂 raw/                      # 原始数据
│   ├── 📂 processed/                # 处理后数据
│   └── 📂 cache/                    # 缓存数据
│
├── 📂 watchlist/                    # 📋 监视列表目录
│   ├── 📜 us_stocks.json            # 美股监视列表
│   └── 📜 hk_stocks.json            # 港股监视列表
│
├── 🚀 main.py                        # 主程序入口
├── 📜 setup.py                       # 安装配置
├── 📜 requirements.txt               # 依赖列表
├── 📜 README.md                      # 项目说明
└── 📜 LICENSE                        # 许可证文件

```

#### 📌 目录和模块简介：
```plaintext
config/: 存放系统配置文件，如日志、报告模板、API 密钥等。
core/: 包含系统核心功能，如数据管理、技术分析、策略管理和回测等。
strategies/: 存放交易策略、回测引擎和股票分析模块。
data/: 存储缓存数据和下载的市场数据。
logs/: 记录回测、交易和系统运行日志。
reports/: 负责报告生成，包括模板、静态资源和最终输出。
utils/: 常用工具函数，如数据验证、格式化和辅助功能。
tests/: 进行单元测试和集成测试，保证系统稳定性。
main.py: 项目主程序入口，负责系统的整体运行。
```
---
### 2025年2月26日TradeMind Dev进度公告：
- 初步完成了一些代码的重构
- 基本确定了项目框架和目录结构，文件
- 剩下功能待开发

---

### 2025年2月16日TradeMind重构公告

- **从现在开始，我们对系统进行重构**：
  
- 在DEV开发工作基本结束之前，我将不会提交代码和合并到Main，充分测试完成之后，我会和Main合并。

### 核心功能及迭代方向介绍

**📌📌📌核心模块与功能设计**：

**1️⃣ 数据管理模块** (data_manager_yf.py 和 data_manager_ibkr.py)：

**Yahoo Finance 数据管理**：获取股票、ETF、指数等的历史数据。适用于普通用户，支持定时抓取和数据缓存。

**IBKR 数据管理**：提供更高频率的实时数据，支持 股票、期权、期货 等市场数据，适合专业用户的需求。

**2️⃣策略分析模块 (strategy_manager.py 和 technical_indicators.py)**：

包括常用技术指标，如 RSI、SMA、EMA、MACD 等。引入 高级策略分析，支持使用 机器学习、深度学习 进行预测分析，或者通过复杂的 多因子模型 改进策略的效果。

**3️⃣回测系统 (backtester.py)**：

提供资金管理功能（例如 止损、止盈、最大回撤控制、仓位管理 等）。
滑点模拟、交易成本 等影响因素的模拟，使回测结果更真实。
支持 多策略回测，可以选择不同的策略组合进行回测。

**4️⃣报告生成 (reports/)**：

支持生成 HTML/PDF 格式的回测报告，包含详细的 交易信号、策略表现、盈亏统计 等。
可视化回测结果，如 策略收益曲线、资金变化、风险指标（最大回撤、夏普比率等）。

**📌📌📌工作计划**：

**1️⃣数据源选择**：在 main.py 中提供一个简单的界面，让用户选择 Yahoo Finance 或 IBKR 数据源。

**2️⃣优化回测**：改进回测模型，增加 风险控制 和 交易成本。支持回测时的 滑点模拟 和 实际交易模拟，让回测结果更贴近实际情况。

**3️⃣技术分析模型**：加入更多的技术指标，并支持基于 机器学习 的策略模型，可以动态调整交易信号。

**4️⃣系统集成和测试**：完成 IBKR Gateway 和 Yahoo Finance 的数据接入。测试不同策略在 回测系统 中的表现，并对回测报告进行多次优化。


---


## 🔔旧版项目介绍（TradeMind Alpha v0.2）

这是一个基于Python开发的股票纯技术面分析工具，目前主要用于美股市场分析。本工具通过分析多个技术指标，识别价格形态，结合成交量分析来生成交易信号，并以直观的HTML报告形式展示分析结果。

<img width="1114" alt="image" src="https://github.com/user-attachments/assets/64b79263-c7fe-4291-b942-5774fd445770" />

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

### 4. 回测系统
- 使用Pandas + NumPy这个最简单的组合做回测框架；
- 回测系统支持多股票，多参数，多策略回测；
- 回测系统支持多种指标，如：RSI，MACD，KDJ，布林带，成交量等；
- 回测系统支持多种策略，如：金叉买入，死叉卖出，金叉买入，死叉卖出等；
- 回测系统支持多种参数，如：RSI，MACD，KDJ，布林带，成交量等；

### 5. 自动化HTML分析报告
- 自动生成HTML格式报告，未来会支持PDF格式；
- 包含图表和详细分析说明；
- 支持批量股票分析；
  
<img width="1242" alt="image" src="https://github.com/user-attachments/assets/f4b90186-2ff1-4221-87ce-d3cae4573e28" />
<img width="1228" alt="image" src="https://github.com/user-attachments/assets/a55a7d55-fa63-4e65-a167-45dd1a319a29" />
<img width="1226" alt="image" src="https://github.com/user-attachments/assets/f94c6cec-3581-4702-a186-5b8a51d715c5" />
<img width="1229" alt="image" src="https://github.com/user-attachments/assets/31ac852c-d907-4f2a-b165-439e190fe92f" />
<img width="1021" alt="image" src="https://github.com/user-attachments/assets/55e61df4-be2b-4f3f-896c-6a8b3ac2842a" />

---
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
- 用于处理操作系统中的文件路径
appdirs==1.4.4
- Python 的网页解析库，用于提取网页数据
beautifulsoup4==4.13.3
- 提供 SSL/TLS 证书验证功能
certifi==2025.1.31
- 字符编码检测库
charset-normalizer==3.4.1
- 事件驱动编程库
eventkit==1.0.3
- 不可变字典实现
frozendict==2.4.6
- HTML 和 XML 文件解析器
html5lib==1.1
- Interactive Brokers Python API 的异步封装库，用于股票交易
ib-insync==0.9.86
- 国际化域名支持库
idna==3.10
- XML 和 HTML 处理库，性能优秀
lxml==5.3.1
- Python 多任务处理库
multitasking==0.0.11
- 解决 Jupyter 中的异步嵌套问题
nest-asyncio==1.6.0
- 数值计算库，提供多维数组支持
numpy==2.0.2
- 数据分析处理库，提供 DataFrame 数据结构
pandas==2.2.3
- 基于 Pandas 的技术分析指标库，用于金融市场分析
pandas_ta==0.3.14b0
- 简单而小巧的 ORM 数据库框架
peewee==3.17.9
- 日期时间处理工具库
python-dateutil==2.9.0.post0
- 时区处理库
pytz==2025.1
- HTTP 请求库
requests==2.32.3
- 任务调度库
schedule==1.2.2
- 科学计算库
scipy==1.13.1
- Python 2 和 3 兼容性工具库
six==1.17.0
- beautifulsoup4 的依赖库
soupsieve==2.6
- 类型提示扩展库
typing_extensions==4.12.2
- HTTP 客户端库(2.X版本和yfinance0.2.54不兼容，只能用1.26.6)
urllib3==1.26.6
- 处理 HTML 和 XML 编码的库
webencodings==0.5.1
- Yahoo Finance 数据获取库，用于获取股票市场数据
yfinance==0.2.54
- 进度条显示库，用于显示循环进度
tqdm==4.67.1


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

### 依赖库更新说明
- 建议定期更新依赖包，建议用下列指令更新：
 - 安装 pur
 ```bash
pip install pur 
 ```
  - 更新 requirements.txt
 ```bash
pur -r requirements.txt 
```

- pur 是一个专门用于更新 requirements.txt 文件的 Python 工具。下面是用法：

 - 只更新指定的包
```bash
pur django pytest -r requirements.txt
```
  - 预览会更新什么（不实际更新）
```bash
pur --dry-run -r requirements.txt
```
  - 强制更新到最新版本（忽略版本限制
```bash
pur --force -r requirements.txt
```

  - 更新时保存备份
```bash
pur --backup -r requirements.txt
```
  - 遇到程序出现依赖错误怎么办，例如如下错误：
```bash
245 - yfinance - ERROR - NVDA: No price data found, symbol may be delisted (period=1y)
```
  - 解决方法，使用pip手动升级对应的依赖，一般即可解决问题，如果实在解决不了问题，把错误提示发给Cursor，按照引导Debug：
```bash
pip install --upgrade yfinance
```


### 注意事项
1. 首次运行可能需要较长时间下载依赖包
2. 确保安装的 Python 版本兼容所有依赖
3. 如遇到 SSL 证书问题，请确保系统时间正确
4. 建议在虚拟环境中运行项目

## 问题反馈
如果使用中遇到问题，欢迎提交Issue或Pull Request。

## 免责声明
本工具仅供学习和研究使用，不构成任何投资建议和风险控制依据。该工具可能会对行业研究员，公司研究员和注重价值投资的个人投资者提供价值。但是，无论如何，投资者应当对自己的投资决策独立负责。

最后强调：市场有风险，投资需谨慎，不要轻信任何信息，要有自己的独立价值体系和判断能力。

##  GPLv3 许可证（GNU 通用公共许可证）声明

本项目采用 **GPLv3 许可证** - 详情请参见 [LICENSE](LICENSE) 文件。下面是我的声明：

- 我本身是 [理查德·斯托曼](https://www.stallman.org/) 的粉丝和 **FSF** 的资深赞助会员，在 [MIT 许可证](https://opensource.org/licenses/MIT) 和 [GPLv3 许可证](https://www.gnu.org/licenses/gpl-3.0.html) 的选择上，我希望采用[自由软件基金会 (FSF)](https://www.fsf.org/)
的方式处理许可证问题。希望大家遵守 **GPLv3** 条款，开源你们的成果，并且沿用 **GPLv3** 协议，让更多的人从中受益。
  
- 我在标准 **GPLv3** 许可证的末尾追加了一段遵循协议的免责声明，全文如下：（本项目特指：[TradeMind](https://github.com/yagami1997/TradeMind)）
```bash
This project  is licensed under the GNU General Public License v3.0 (GPL-3.0). This software is provided 'as-is' without any warranty of any kind, express or implied, including but not limited to the warranties of merchantability or fitness for a particular purpose. In no event will the authors or copyright holders be liable for any damages.
```
**中文含义为：**
```bash
本项目采用 GNU 通用公共许可证 v3.0 (GPL-3.0) 许可。本软件按“现状”提供，不提供任何形式的明示或暗示的保证，包括但不限于适销性或特定用途适用性的保证。在任何情况下，作者或版权持有者均不对任何损害负责。
```
- 我已经可以预感到很多大佬沿用这个思路，可以开发出更强更完善的系统造福散户，谢谢你们！🙏🙏🙏
  
---
<p align="right">
  <em>“In this cybernetic realm, we shall ultimately ascend to digital rebirth，Long live the Free Software Movement!”</em><br>
 — <strong>Yagami</strong><br>
  <span style="font-size: 14px; color: #888;">2025-02-11</span>
</p>
