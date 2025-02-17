# TradeMind美股技术面简单分析工具 Alpha v 0.2

## 重要声明
1. 本工具99%的代码由Cursor自动生成，Coding模型Claude3.5，当然也可以用别的。对我来说，更像个赛博念经的，负责规划设计调试。
2. 本工具的分析结果仅供参考，仅代表我不成熟的策略设计思路，所以不构成任何投资建议和风险控制依据。
3. 本工具完全开源、免费、无论是Clone、再开发甚至商业化我都不反对，但必须遵守FSF的GPLv3许可证协议。
4. 后续其他二次开发版本和我无关，我亦不承担任何责任，本代码仓库仅供学习研究。
5. 市场有风险，投资需谨慎，成熟的交易者不会把决策简单归因于信息差或者技术操作，投资是修行。
---
## 更新日志

### 2025年2月16日更新
- 我已经着手开始/dev分支的开发，所以/main分支可能会停留在当前版本，仅维护自选股列表，如果算法有改进的话，我会及时同步策略、模型和回测系统，让它更有用一点；
- /dev的基本架构如下：

<img width="680" alt="image" src="https://github.com/user-attachments/assets/2b31ed30-a242-4bf0-a78e-ddb7bb2b64cf" />



如果你对新的架构感兴趣，可以Fork /dev，然后按照这个思路独立开发，🙏🙏
- 我已经把目前的/main主分支的程序Release了一个版本出来，可以直接下载部署使用，[戳这里下载](https://github.com/yagami1997/TradeMind/releases/tag/Trademind)。

### 2025年2月11日更新
- 解决了MACD值显示错误的算法BUG，修复了KDJ算法错误，解决了一个不重要的告警提示；
- 重新优化了回测系统，显示回测结果，并且在报告的最后详细说明参数，策略和回测指标；
- 重新大幅度优化了K线形态特征的判定，优化了显示效果；
- 更新了股票决策的算法，目前操作结论偏积极，决策偏向布林带和RSI，这是我个人的偏好，大家可以根据自己偏好调整算法；
- 改进了HTML的显示方式，色彩搭配，采用紧凑型卡片显示更多的个股技术信息和操作指南，命令行分析完成之后，自动打开HTML报告，无需手动；
- 优化改进了其他问题，提高了分析速度；
- ⚠️项目目录中main.py是个更简单的快速遍历股票程序，我会重新思考Main程序的功能，架构和体现方式，目前不推荐使用该程序分析股票。主要推荐使用stock_analyzer.py。请在Shell下执行如下命令：（MacOS请开启Shell虚拟化：source venv/bin/activate）
 
 ```Shell下执行命令
python stock_analyzer.py
 ```
---

## 项目介绍
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
- HTTP 客户端库(2.X版本和yfinance0.2.53不兼容，所以只能用1.26.6)
urllib3==1.26.6
- 处理 HTML 和 XML 编码的库
webencodings==0.5.1
- Yahoo Finance 数据获取库，用于获取股票市场数据
yfinance==0.2.53
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

- 关注项目更新，及时同步最新代码

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
