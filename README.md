# 🚀 TradeMind Lite 轻量版美股技术分析工具 Beta 0.3.4

## ⚠️ 重要声明

1. 本工具99%的代码由Cursor自动生成，Coding模型Claude3.5，当然也可以用别的。对我来说，更像个赛博念经的，负责规划设计调试。
2. Clone下来的源代码包括了所有的程序代码和项目所需的开发文档，测试文档，对于普通用户来说，我稍后会发行Windows/macOS的安装版本。
3. 本工具的分析结果仅供参考，仅代表我不成熟的策略设计思路，所以不构成任何投资建议和风险控制依据。
4. 本工具完全开源、免费、无论是Clone、再开发甚至商业化我都不反对，但必须遵守FSF的GPLv3许可证协议。
5. 后续其他二次开发版本和我无关，我亦不承担任何责任，本代码仓库仅供学习研究。
6. 市场有风险，投资需谨慎，成熟的交易者绝对不会把决策简单归因于信息差或者技术操作，投资是修行。


<details><summary><strong><h4>⚠️ Yahoo Finance API 访问错误解决方案</h4></strong></summary>

## 问题描述
使用 yfinance 库时遇到：
```
yfinance.exceptions.YFRateLimitError: Too Many Requests. Rate limited.
```

## 问题根因
该错误**并非代码问题**，而是 Yahoo Finance 的技术限制：

### 核心技术变化
- **官方 API 已停止**（2017年关闭）
  - 原因：大规模数据滥用，违反数据提供商条款
  - 影响：所有第三方库转为屏幕抓取模式
  
- **反爬虫机制升级**（2025年5月起加强）
  - Cookie 依赖检测：要求先访问网站获取有效Cookie
  - User-Agent 识别：检测非浏览器请求模式
  - 请求频率分析：识别程序化访问行为
  
- **严格频率限制**（每日数百次请求后封IP）
  - IP级别封锁：即使更换API密钥也无效
  - 地域性限制：部分地区访问受到额外限制
  - 动态阈值调整：根据服务器负载动态调整限制

## 解决方案

### 方法一：代理配置（推荐）
将以下域名添加到代理工具的规则集，按照工具要求书写正确规则：
```
*.finance.yahoo.com
finance.yahoo.com
query1.finance.yahoo.com
query2.finance.yahoo.com
```
然后重启代理服务。

### 方法二：代码优化
```python
import yfinance as yf
import time
import random

def fetch_data_with_retry(symbol, max_retries=3):
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(random.uniform(1, 3))
                continue
            else:
                raise e
```

### 方法三：IBKR Gateway API（专业方案）

**前提条件**：需要成为盈透证券（Interactive Brokers）的客户

#### 优势特点
- **数据质量**：机构级别实时数据，无延迟
- **稳定性**：官方API支持，无限制风险
- **覆盖范围**：全球160个市场，36个国家
- **功能完整**：股票、期权、期货、外汇、债券全覆盖

#### 基本使用步骤

1. **开设IBKR账户**
   ```bash
   # 可开设模拟账户用于测试
   # 访问 interactivebrokers.com 注册
   ```

2. **下载并安装客户端**
   ```bash
   # 选择其一：
   # - TWS (Trader Workstation) - 适合初学者，有图形界面
   # - IB Gateway - 轻量级，适合程序化使用
   ```

3. **安装Python API**
   ```bash
   # 从官网下载TWS API (版本9.73+)
   # 或使用第三方库
   pip install ib_insync  # 推荐，更易用
   pip install ibapi      # 官方原生API
   ```

4. **基本代码示例**
   ```python
   from ib_insync import *
   
   # 连接到IB Gateway/TWS
   ib = IB()
   ib.connect('127.0.0.1', 7497, clientId=1)  # 模拟账户
   # ib.connect('127.0.0.1', 7496, clientId=1)  # 真实账户
   
   # 获取股票数据
   contract = Stock('AAPL', 'SMART', 'USD')
   ticker = ib.reqMktData(contract)
   
   # 获取历史数据
   bars = ib.reqHistoricalData(
       contract, 
       endDateTime='', 
       durationStr='1 Y',
       barSizeSetting='1 day',
       whatToShow='TRADES',
       useRTH=True
   )
   
   ib.disconnect()
   ```

#### 配置要点
- **API端口**：模拟账户7497，真实账户7496
- **连接限制**：每秒最多50条消息
- **权限设置**：需在TWS/Gateway中启用API连接

### 替代数据源

#### Alpha Vantage
- **免费额度**：每日25次请求，每分钟5次请求
- **付费计划**：起步价$49.99/月，每分钟75次请求
- **数据覆盖**：股票、外汇、加密货币，支持50+技术指标
- **优势**：文档详细，Python库支持好
- **缺点**：可能存在IP级别限制

#### IEX Cloud（已停止服务）
⚠️ **重要更新**：IEX Cloud已于2024年8月31日停止服务
- **替代方案**：官方推荐迁移至Intrinio（价格较高）

#### Finnhub
- **免费额度**：每分钟60次API调用
- **数据覆盖**：全球股票交易所、10个外汇经纪商、15+加密货币交易所
- **特色功能**：机构级别替代数据、基本面数据
- **优势**：免费额度慷慨，数据质量高，API文档完善
- **适用场景**：概念验证和想法测试

#### Twelve Data
- **免费额度**：每日800次请求
- **数据类型**：实时和历史股票数据
- **覆盖范围**：全球市场支持

#### Polygon.io
- **免费方式**：通过Alpaca经纪商账户免费获取
- **数据质量**：机构级别数据
- **适用对象**：需要高质量数据的专业用户

## 重要提醒
- ✅ **有效**：网络层面解决访问限制
- ❌ **无效**：单纯修改代码逻辑
- 💡 **本质**：解决网络访问问题，非绕过限制

</details>
---

## 📋 项目简介

TradeMind Lite是一个轻量级的美股技术分析工具，专注于技术面分析。它采用多个技术指标和形态识别算法，为投资者提供客观的市场分析和交易建议。本工具特别适合对技术分析感兴趣的个人投资者和研究人员。

## 🧠 Cursor智能辅助开发框架

本项目完全引入我原创开发的 [CursorMind](https://github.com/yagami1997/CursorMind) 智能开发框架进行软件工程管理，这是Cursor辅助开发的最佳实践。CursorMind框架提供了标准化的项目管理结构、文档模板和工作流程，确保开发过程的一致性和可追踪性。通过使用CursorMind，我们实现了：

- 标准化的项目管理和文档体系
- 自动化的时间戳生成和版本控制
- 结构化的决策记录和进度跟踪
- 规范化的代码开发和质量保证流程

这种方法论显著提高了开发效率，减少了沟通成本，并确保了软件质量的一致性。

## 📝 更新日志

### 🚀 2025年5月21日UI颜色优化与ADX修复完成 (Beta 0.3.4)
- **版本升级**: 从Beta 0.3.3升级到Beta 0.3.4
- **UI优化**: 实现股票卡片头部颜色根据推荐等级显示不同颜色
- **分析区域优化**: 修改分析建议区域背景色，更好地与指标区块区分
- **Bug修复**: 修复ADX计算问题，确保结果显示正确值而非固定值。原问题是ADX指标（包括ADX、+DI、-DI值）在某些情况下总是显示固定的默认值（ADX=15.0，+DI=10.0，-DI=10.0）而不是实际计算结果。修复方法是实现多源数据获取逻辑，从result.adx、result.adx_from_report、result.adx_data以及result.trend_analysis等多个可能的数据源中获取有效值，并添加了数据有效性验证，确保只在没有有效计算结果时才使用默认值

### 🚀 2025年5月19日压力位和趋势分析系统完成 (Beta 0.3.3)
- **版本升级**: 从Beta 0.3.2升级到Beta 0.3.3
- **核心功能**: 完成压力位识别和趋势判定系统实现
  - 实现了Fibonacci回调位计算和价格分布密度分析
  - 完成了基于Dow Theory的趋势判定逻辑
  - 实现了ADX趋势强度指标计算与可视化
  - 集成了趋势线自动识别功能
- **界面优化**: 新增个股分析卡片UI，直观展示压力位和趋势状态
- **Bug修复**: 修复了ADX指标在某些情况下显示不正确的问题
- **性能提升**: 优化了分析报告生成性能，提高了处理速度
- **清理优化**: 删除了开发阶段的临时文件和测试脚本
- **决策文档**: [Decision-004](https://github.com/yagami1997/TradeMind/blob/main/project_management/actuals/decisions/decision_004.md) 已完成实施

### 🆕 2025年3月20日开发文档更新决策004和Task016 (Beta 0.3.2)
🔔 **已完成**: 压力位识别和趋势判定系统实现

🏁**技术路线**
1. **Fibonacci回调位**
   - 基于Fibonacci数列（0.236, 0.382, 0.5, 0.618, 0.786）的回调位计算
   - 在主要趋势中寻找高点和低点，计算关键回调位置
   - 被广泛应用于华尔街，具有较强的市场认可度

2. **历史价格分布密度分析**
   - 基于 Market Profile 理论（由 Peter Steidlmayer 开发）
   - 分析价格在不同区域的成交密度
   - 识别高成交量价格区域作为潜在支撑/压力位

3. **移动平均线支撑压力系统**
   - 使用广泛认可的均线系统：MA20、MA50、MA200
   - 基于 Richard Donchian 的移动平均线交易系统理论
   - 将主要均线位置作为动态支撑压力位

#### 🔔有关开发文档指南：
- 📋 [TASK-016: 压力位和趋势分析系统实现](https://github.com/yagami1997/TradeMind/blob/main/project_management/actuals/tasks/TASK-016_%E5%8E%8B%E5%8A%9B%E4%BD%8D%E5%92%8C%E8%B6%8B%E5%8A%BF%E5%88%86%E6%9E%90%E7%B3%BB%E7%BB%9F%E5%AE%9E%E7%8E%B0.md)
- 📝 [Decision-004: 项目决策文档](https://github.com/yagami1997/TradeMind/blob/main/project_management/actuals/decisions/decision_004.md)


### 🆕 2025年3月19日自选股编辑器重构更新 (Beta 0.3.2)

- 将自选股编辑器完全重写，支持行业分类编辑，股票信息编辑等详细功能
- 解决了系统原本对股票排序采用字母排序，和用户自选股列表的根本冲突
- 解决多个致命错误，提升了性能
- 本版本号不变，UX和UI设计告一段落，未来聚焦在指标分析算法和回测模型

### 🆕 2025年3月16日功能重大优化更新 (Beta 0.3.2)

- Web界面新增自选股导入功能，支持自动分类和智能行业分组
- 改进股票代码验证逻辑，增强对指数和ETF的支持
- 优化用户界面交互体验，提升操作流畅度
- 自选股编辑器批量操作功能增强，支持智能跟随选择位置
- 添加股票选择视觉反馈和动画效果，提升用户体验
- 优化批量操作菜单样式，增加固定显示和滚动跟随功能
- 新增自选股用户手动分类功能，拖动分类排序到满意的位置
- 修复多个已知问题，提高系统稳定性
- 本版本标志着系统交互和UI体验的开发告一段落，接下来我们开发的方向是指标分析算法，交易情绪分析，策略输出，基本面主观指标植入和回测模型，修炼内功。


### 🆕 2025年3月15日界面优化更新 (Beta 0.3.1)
- **Web界面主题优化**：优化三个主题（翠影流金、紫岚烟渚、蓝沁云霁）的色彩搭配，提升视觉体验，在Web界面右上角点击主题图标即可一键切换不同风格
- **标题样式统一**：统一"分析股票"和"分析结果"标题样式，优化"最近生成的报告"标题显示
- **卡片样式优化**：改进股票卡片和报告卡片的样式，提高可读性和美观度
- **按钮样式优化**：统一按钮样式和颜色，优化交互效果
- **响应式设计优化**：改进不同屏幕尺寸下的显示效果，提升移动设备体验
- **动态RSI阈值算法**：引入基于ATR的动态RSI阈值调整算法，根据股票波动率自动调整RSI超买超卖阈值，显著提高高波动率股票（如NVDA）的信号质量
- **错误修复**：修复报告生成器KeyError问题、K线形态指标显示问题和Sortino比率显示异常
- **浏览器关闭优化**：改进浏览器关闭事件检测，自动停止服务器并返回主菜单


### 🆕 2025年3月14日重构级更新 (Beta 0.3.0)
- **架构全面重构**：优化代码结构，提升性能，降低内存占用，支持更大规模的股票分析
- **用户界面改进**：全新的命令行和Web查询双界面，更直观的操作流程，支持多级菜单和快捷命令
- **技术指标升级**：引入更精准的算法模型，支持自定义参数和信号阈值设置
- **回测系统增强**：新增多策略组合回测，支持自定义交易规则和风险管理参数
- **报告系统优化**：全新HTML报告设计，更清晰的数据可视化，支持批量报告生成
- **多平台兼容**：全面支持Windows、macOS和Linux系统，提供详细的安装和使用指南
- **错误处理增强**：完善的异常捕获和日志系统，提供详细的故障排除指南
- **文档全面更新**：详尽的使用说明和API文档，帮助用户快速上手和进行二次开发

## ✨ 核心特性

### 📊 技术指标分析
- **RSI指标**: 基于Wilder原始设计，准确识别超买超卖
- **MACD指标**: 采用Appel原创算法，把握趋势动量
- **KDJ指标**: 使用Lane随机指标方法，预测价格转折
- **布林带**: 动态跟踪价格波动区间
- **成交量分析**: 验证价格趋势有效性

### 🎯 智能信号系统
- 多维度交叉验证
- 信号可信度量化评分
- 清晰的操作建议展示

### 🔄 专业回测框架
- 支持多股票组合回测
- 灵活的参数优化系统
- 完整的绩效评估报告

### 📈 可视化报告
- 自动生成HTML分析报告
- 专业的图表展示
- 详尽的分析说明

## 💻 详细安装指南

<details>
<summary><b>Windows 安装步骤</b>（点击展开）</summary>

1. **安装 Python 环境**
   - 访问 [Python官网](https://www.python.org/downloads/windows/)
   - 下载最新的 Python 3.9.x 安装包
   - 运行安装程序，**务必勾选** "Add Python to PATH" 选项
   - 选择"Customize installation"，确保勾选"pip"和"tcl/tk"
   - 完成安装后，打开命令提示符(Win+R 输入cmd)，输入`python --version`验证安装

2. **下载 TradeMind Lite**
   - 方法一: 使用Git (推荐)
     ```bash
     # 安装Git (如果尚未安装)
     # 从 https://git-scm.com/download/win 下载并安装
     
     # 克隆仓库
     git clone https://github.com/yagami1997/TradeMind.git
     cd trademind
     ```
   
   - 方法二: 直接下载
     - 访问项目GitHub页面
     - 点击"Code"按钮，选择"Download ZIP"
     - 解压下载的ZIP文件到合适的位置
     - 使用命令提示符进入解压后的目录

3. **创建虚拟环境 (强烈推荐)**
   ```bash
   # 进入项目目录
   cd path\to\trademind
   
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   venv\Scripts\activate
   
   # 确认激活成功 (命令行前应出现(venv)前缀)
   ```

4. **安装依赖包**
   ```bash
   # 确保pip是最新版本
   python -m pip install --upgrade pip
   
   # 安装所有依赖
   pip install -r requirements.txt
   
   # 验证关键依赖安装
   pip list | findstr pandas
   pip list | findstr numpy
   pip list | findstr yfinance
   ```

5. **首次运行测试**
   ```bash
   # 运行主程序
   python trademind.py
   
   # 如果遇到问题，尝试运行诊断脚本
   python scripts/diagnose.py
   ```
</details>

<details>
<summary><b>macOS 安装步骤</b>（点击展开）</summary>

1. **安装必备工具**
   ```bash
   # 安装Homebrew (如果尚未安装)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # 安装Python
   brew install python@3.9
   
   # 安装Git (如果尚未安装)
   brew install git
   
   # 验证安装
   python3 --version
   git --version
   ```

2. **下载 TradeMind Lite**
   ```bash
   # 克隆仓库
   git clone https://github.com/yagami1997/TradeMind.git
   cd trademind
   ```

3. **创建并激活虚拟环境**
   ```bash
   # 创建虚拟环境
   python3 -m venv venv
   
   # 激活虚拟环境
   source venv/bin/activate
   
   # 确认激活成功 (命令行前应出现(venv)前缀)
   ```

4. **安装依赖包**
   ```bash
   # 更新pip
   pip install --upgrade pip
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 如果lxml安装失败，先安装开发工具
   xcode-select --install
   pip install lxml
   ```

5. **首次运行**
   ```bash
   # 运行主程序
   python trademind.py
   ```
</details>

<details>
<summary><b>Linux (Ubuntu/Debian) 安装步骤</b>（点击展开）</summary>

1. **安装系统依赖**
   ```bash
   # 更新包索引
   sudo apt update
   
   # 安装Python和开发工具
   sudo apt install -y python3.9 python3.9-venv python3-pip git build-essential python3-dev
   
   # 安装图形库依赖 (matplotlib需要)
   sudo apt install -y libfreetype6-dev pkg-config
   
   # 验证安装
   python3.9 --version
   ```

2. **下载项目**
   ```bash
   # 克隆仓库
   git clone https://github.com/yagami1997/TradeMind.git
   cd trademind
   ```

3. **创建并激活虚拟环境**
   ```bash
   # 创建虚拟环境
   python3.9 -m venv venv
   
   # 激活虚拟环境
   source venv/bin/activate
   ```

4. **安装依赖**
   ```bash
   # 更新pip
   pip install --upgrade pip
   
   # 安装依赖
   pip install -r requirements.txt
   ```

5. **运行程序**
   ```bash
   python trademind.py
   ```
</details>

## 📚 详细使用指南

### 🚀 启动与配置

1. **启动程序**
   - 确保已激活虚拟环境
   - 运行主程序: `python trademind.py`
   - 首次运行会创建配置文件和必要的目录结构

2. **主菜单导航**

<div align="center">
   <img src="https://github.com/user-attachments/assets/e2b1dcf3-f0e4-47a5-ae20-26b4f71ac95d" alt="主菜单选项" width="800px"/>
</div>

   - 使用数字键选择功能
   - 按`q`或`Ctrl+C`退出程序
   - 主菜单选项说明:
     - `1` - 命令行模式: 进入命令行快速分析
     - `2` - Web模式: 启动一个虚拟的Web服务器，图形界面操作

### 📈 股票分析流程

<div align="center">
<img width="800" alt="image" src="https://github.com/user-attachments/assets/9ea15bdb-7936-4dce-93e6-c6d6be9fcff1" />
</div>

1. **输入股票代码**
   - 单个股票: 直接输入代码，如 `AAPL`
   - 多个股票: 用空格分隔，如 `AAPL MSFT GOOGL`
   - 支持的格式:
     - 美股: 直接输入代码 (如 `AAPL`)

2. **等待分析完成**

<div align="center">
<img width="800" alt="image" src="https://github.com/user-attachments/assets/17ec3779-7065-4ec2-85ab-3e64ccd248d3" />
</div>

   - 程序会显示进度条
   - 数据获取和处理可能需要几秒到2分钟不等
   - 分析完成后点击查看报告按钮打开HTML报告；或者点击列表里的过往报告查看

### 📊 报告解读指南

<div align="center">
<img width="800" alt="image" src="https://github.com/user-attachments/assets/c4b00dd6-8632-43d4-8f8c-2bf191c0ac43" />
</div>

### 🖌️ 自选股编辑器
<div align="center">
<img width="800" alt="image" src="https://github.com/user-attachments/assets/df1786f7-27d6-47be-9437-57f2623a2220" />
</div>

1. **报告结构**
   - 顶部: 股票基本信息和分析摘要
   - 中部: 技术指标图表和形态识别结果
   - 底部: 交易信号和建议操作

2. **技术指标解读**
   - **RSI**: 
     - 70以上: 超买区域，可能回调
     - 30以下: 超卖区域，可能反弹
     - 50线穿越: 趋势转变信号
   
   - **MACD**:
     - 金叉(DIFF线上穿DEA线): 买入信号
     - 死叉(DIFF线下穿DEA线): 卖出信号
     - 柱状图由负转正: 上涨动能增强
   
   - **KDJ**:
     - K线和D线同时在80以上: 超买
     - K线和D线同时在20以下: 超卖
     - J线极值: 反转信号
   
   - **布林带**:
     - 价格触及上轨: 可能回落
     - 价格触及下轨: 可能反弹
     - 带宽扩大: 波动性增加

3. **信号系统说明**
   - 信号类型: 买入/卖出/观望
   - 建议操作: 具体的交易建议和风险提示

### 🔄 回测系统使用

1. **创建回测任务**
   - 选择股票池: 单个或多个股票
   - 设置时间范围: 开始日期和结束日期
   - 选择策略: 内置策略或自定义策略

2. **配置回测参数**
   - 初始资金: 设置模拟交易的起始资金
   - 交易费用: 设置佣金和滑点
   - 仓位管理: 设置每次交易的资金比例

3. **运行回测**
   - 等待回测完成
   - 查看回测报告和性能指标
   - 分析交易记录和盈亏情况

4. **优化策略**
   - 调整参数重新回测
   - 比较不同参数的回测结果
   - 导出最优参数设置

## ⚙️ 高级功能

### 🛠️ 自定义分析参数

1. **修改技术指标参数**
   ```bash
   # 打开配置文件
   python -m trademind.config --edit indicators
   ```

2. **自定义报告模板**
   ```bash
   # 编辑HTML模板
   python -m trademind.config --edit templates
   ```

3. **设置自动分析计划**
   ```bash
   # 配置定时任务
   python -m trademind.scheduler --setup
   ```

## 🔧 故障排除指南

<details>
<summary><b>安装问题</b>（点击展开）</summary>

1. **Python版本冲突**
   - **症状**: 安装依赖时出现版本不兼容错误
   - **解决方案**:
     ```bash
     # 确认Python版本
     python --version
     
     # 如果不是3.8或更高版本，安装正确版本
     # Windows: 从Python官网下载并安装
     # macOS: brew install python@3.9
     # Linux: sudo apt install python3.9
     
     # 创建新的虚拟环境
     python3.9 -m venv venv_new
     source venv_new/bin/activate  # Linux/Mac
     venv_new\Scripts\activate     # Windows
     
     # 重新安装依赖
     pip install -r requirements.txt
     ```

2. **依赖安装失败**
   - **症状**: `pip install -r requirements.txt` 命令失败
   - **解决方案**:
     ```bash
     # 逐个安装核心依赖
     pip install numpy
     pip install pandas
     pip install matplotlib
     pip install yfinance
     
     # 如果lxml安装失败
     # Windows: 安装Visual C++ Build Tools
     # macOS: xcode-select --install
     # Linux: sudo apt install libxml2-dev libxslt-dev
     
     pip install lxml
     
     # 使用国内镜像源(中国用户)
     pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
     ```

3. **虚拟环境问题**
   - **症状**: 激活虚拟环境失败或找不到命令
   - **解决方案**:
     ```bash
     # Windows
     # 如果提示"无法加载文件 venv\Scripts\activate.ps1，因为在此系统上禁止运行脚本"
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     
     # 如果venv目录损坏，重新创建
     rmdir /s /q venv
     python -m venv venv
     venv\Scripts\activate
     
     # Linux/macOS
     # 如果提示"source: not found"
     bash -c "source venv/bin/activate"
     ```
</details>

<details>
<summary><b>运行时问题</b>（点击展开）</summary>

1. **数据获取失败**
   - **症状**: 程序报错"无法获取股票数据"
   - **解决方案**:
     ```bash
     # 检查网络连接
     ping yahoo.com
     
     # 检查股票代码是否正确
     python -m trademind.tools.verify_ticker AAPL
     
     # 使用代理(如果需要)
     export HTTPS_PROXY=http://your-proxy:port  # Linux/macOS
     set HTTPS_PROXY=http://your-proxy:port     # Windows
     
     # 手动更新yfinance
     pip install --upgrade yfinance
     ```

2. **程序崩溃**
   - **症状**: 程序意外退出或冻结
   - **解决方案**:
     ```bash
     # 运行诊断工具
     python -m trademind.diagnose
     
     # 检查日志文件
     cat logs/error.log  # Linux/macOS
     type logs\error.log # Windows
     
     # 清理缓存
     python -m trademind.tools.clean_cache
     
     # 以调试模式运行
     python -m trademind --debug
     ```

3. **报告生成失败**
   - **症状**: 分析完成但没有生成HTML报告
   - **解决方案**:
     ```bash
     # 检查reports目录权限
     # 确保程序有写入权限
     
     # 手动生成最近的分析报告
     python -m trademind.report --regenerate
     
     # 检查模板文件
     python -m trademind.tools.verify_templates
     ```

4. **性能问题**
   - **症状**: 程序运行缓慢
   - **解决方案**:
     ```bash
     # 减少分析的股票数量
     # 缩短分析周期
     # 关闭不必要的指标
     
     # 清理历史数据
     python -m trademind.tools.cleanup --older-than 30
     ```
</details>

## ❓ 常见问题解答

<details>
<summary><b>基本使用问题</b>（点击展开）</summary>

- **问**: 如何分析多个股票?
  **答**: 在股票代码输入提示处，输入多个代码并用空格分隔，如`AAPL MSFT GOOGL`。最多支持同时分析10个股票。当然我更建议你编辑批量查询列表来方便查询

- **问**: 如何保存分析结果?
  **答**: 分析结果会自动保存在`reports/stocks`目录下，文件名格式为`股票代码_日期时间.html`。您也可以在查看报告时使用浏览器的"另存为"功能保存报告。

- **问**: 程序支持哪些技术指标?
  **答**: 目前支持RSI、MACD、KDJ、布林带、移动平均线、成交量分析等主要技术指标。可以通过配置文件添加更多指标。
</details>

<details>
<summary><b>数据与分析问题</b>（点击展开）</summary>

- **问**: 数据来源是什么?
  **答**: 本程序使用Yahoo Finance API获取股票数据，相对IBKR的数据，YF数据偶尔略有几秒钟延迟。

- **问**: 为什么某些股票无法获取数据?
  **答**: 可能是因为:
  1. 股票代码输入错误
  2. 该股票在Yahoo Finance上不可用
  3. 网络连接问
  4. API访问限制(短时间内请求过多)

- **问**: 技术分析结果准确吗?
  **答**: 技术分析基于历史数据和统计模型，不能保证未来表现。结果仅供参考，不构成投资建议。实际交易决策应结合基本面分析和风险管理。
</details>

<details>
<summary><b>故障排除问题</b>（点击展开）</summary>

- **问**: 程序启动后立即崩溃怎么办?
  **答**: 
  1. 检查Python版本是否兼容(3.8+)
  2. 确认所有依赖都已正确安装
  3. 查看`logs/error.log`文件了解错误详情
  4. 尝试以调试模式运行: `python -m trademind --debug`

- **问**: 分析过程中卡住怎么办?
  **答**: 
  1. 按`Ctrl+C`中断程序
  2. 检查网络连接
  3. 减少同时分析的股票数量
  4. 清理缓存: `python -m trademind.tools.clean_cache`
  5. 重新启动程序

- **问**: 更新后程序无法运行怎么办?
  **答**: 
  1. 更新依赖: `pip install -r requirements.txt --upgrade`
  2. 重置配置: `python -m trademind.config --reset`
  3. 如果问题持续，回滚到之前的版本或查看GitHub上的issue
</details>


## 📄 GPLv3 许可证（GNU 通用公共许可证）声明

本项目采用 **GPLv3 许可证** - 详情请参见 [LICENSE](LICENSE) 文件。下面是我的声明：

- 我在 [MIT 许可证](https://opensource.org/licenses/MIT) 和 [GPLv3 许可证](https://www.gnu.org/licenses/gpl-3.0.html) 的选择上，希望采用[自由软件基金会 (FSF)](https://www.fsf.org/)的方式处理许可证问题。希望大家遵守 **GPLv3** 条款，开源你们的成果，并且沿用 **GPLv3** 协议，让更多的人从中受益。
  
- 我在标准 **GPLv3** 许可证的末尾追加了一段遵循协议的免责声明，全文如下：（本项目特指：[TradeMind](https://github.com/yagami1997/TradeMind)）
```bash
This project is licensed under the GNU General Public License v3.0 (GPL-3.0). This software is provided 'as-is' without any warranty of any kind, express or implied, including but not limited to the warranties of merchantability or fitness for a particular purpose. In no event will the authors or copyright holders be liable for any damages.
```

**中文含义为：**
```bash
本项目采用 GNU 通用公共许可证 v3.0 (GPL-3.0) 许可。本软件按"现状"提供，不提供任何形式的明示或暗示的保证，包括但不限于适销性或特定用途适用性的保证。在任何情况下，作者或版权持有者均不对任何损害负责。
```

- 我已经可以预感到很多大佬沿用这个思路，可以开发出更强更完善的系统造福散户，谢谢你们！🙏🙏🙏
  
---
<p align="right">
  <em>"In this cybernetic realm, we shall ultimately ascend to digital rebirth，Long live the Free Software Movement!"</em><br>
 — <strong>Yagami</strong><br>
  <span style="font-size: 14px; color: #888;">2025-05-19 02:43:19 PDT</span>
</p>
