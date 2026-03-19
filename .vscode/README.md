# VS Code Python 开发环境配置指南

本项目的 VS Code 配置已完整优化，支持以下开发工作流。

## 📋 配置文件清单

| 文件 | 用途 |
|-----|------|
| `.vscode/settings.json` | Pylance 分析、代码格式化、Linting、测试 |
| `.vscode/launch.json` | 调试配置（主程序、CLI、Web、测试） |
| `.vscode/extensions.json` | 推荐的 VS Code 扩展 |
| `.pylintrc` | Pylint 详细配置 |

## 🚀 快速开始

### 1. 安装推荐扩展
```bash
# 在 VS Code 中：
# Cmd+Shift+X 打开扩展商店
# 点击 "推荐" 标签页，一键安装所有推荐扩展
```

### 2. 验证环境
```bash
# VS Code 终端中运行：
python --version         # 应显示 Python 3.13.12
python -c "import rich"  # 应无错误
pytest --version        # 应显示 pytest 版本
```

## 🔍 主要功能说明

### 代码分析（Pylance）
- ✅ 自动导入解析，支持 venv 中的所有包
- ✅ 类型检查模式：`standard`（平衡）
- ✅ 自动路径扫描：`trademind/` 和 `tests/`

### 代码格式化
- ✅ 格式化器：**Black**（保存时自动触发）
- ✅ Import 排序：**Python isort** 集成
- ✅ 行长限制：120 字符（一起看 .pylintrc）

### Linting
- ✅ **Pylint** 启用，检查常见问题
- ✅ 禁用的规则：docstring、protected-access 等（可在 .pylintrc 调整）
- ✅ 输出级别：`information` / `warning` / `error`

### 测试框架
- ✅ **pytest** 集成（含 pytest-cov 支持）
- ✅ 快捷调试：
  - `F5` - 运行当前测试文件
  - 侧边栏 Test Explorer 快速运行/调试

### 调试器
- ✅ 8 个预配置的启动配置：
  1. **主程序（trademind）** - 默认入口
  2. **CLI 模式** - 命令行界面
  3. **Web 模式** - Flask 服务（localhost:3336）
  4. **运行当前文件** - 灵活调试
  5. **pytest 全部测试** - 批量测试调试
  6. **pytest 当前文件** - 单文件测试
  7. **pytest 集成测试** - 只测 integration 目录
  8. **Attach 调试器** - 附加到已运行的进程

## 🎯 常用快捷键

| 快捷键 | 功能 |
|-------|------|
| `Cmd+Shift+D` | 打开调试面板 |
| `F5` | 启动/继续调试 |
| `F10` | 单步执行（Step Over） |
| `F11` | 步入函数（Step Into） |
| `Shift+F11` | 步出函数（Step Out） |
| `Cmd+Shift+B` | 运行任务（如指定的话） |
| `Cmd+Shift+P` → `Python: Lint` | 手动运行 Lint |
| `Cmd+Shift+P` → `Format Document` | 格式化当前文件 |

## 📝 调试工作流示例

### 调试主程序
1. `Cmd+Shift+D` 打开调试面板
2. 选择 **"Python: 主程序(trademind)"**
3. `F5` 启动，在代码行号处点击设置断点
4. 程序停在断点时可在调试控制台查看变量

### 调试测试
1. 打开 `tests/integration/test_end_to_end.py`
2. `Cmd+Shift+D` 选择 **"Python: pytest (当前文件)"**
3. `F5` 运行，失败时自动停止
4. 在 Debug Console 检查堆栈跟踪

### 调试 Web 服务
1. `Cmd+Shift+D` 选择 **"Python: Web 模式 (3336)"**
2. `F5` 启动，服务运行在 http://127.0.0.1:3336
3. 在代码中设置断点，浏览器访问时触发
4. 在 Debug Console 查看请求信息

## 🔧 常见问题排查

### 导入错误波浪线仍然存在？
```bash
# 1. 重新加载 VS Code 窗口：
Cmd+Shift+P → "Reload Window"

# 2. 手动清理 Pylance 缓存：
rm -rf "/Users/kinglee/Library/Application Support/Code/User/workspaceStorage"

# 3. 验证 Python 路径：
# 左下角 Python 版本显示器 → 选择 ./venv/bin/python
```

### Pylint 找不到包？
```bash
# .vscode/settings.json 已配置 extraPaths，如仍有问题：
# 1. 确认虚拟环境激活：
source venv/bin/activate
pip list | grep rich

# 2. 在 .pylintrc [MASTER] 下添加：
init-hook='import sys; sys.path.insert(0, "/Users/kinglee/Documents/Projects/Trading/TradeMind")'
```

### 调试器不停止在断点？
```bash
# 确保调试配置中 "justMyCode" 为 false（已默认设置）
# 如需调试第三方库，在 launch.json 对应配置改为：
"justMyCode": false
```

## 📦 环境管理

### 激活虚拟环境（终端）
```bash
source venv/bin/activate    # macOS/Linux
# 或
.\venv\Scripts\activate     # Windows
```

### 安装新包
```bash
# 方式 1: 直接 pip（会自动激活）
pip install 包名

# 方式 2: 从 requirements.txt
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 更新快速路径
```bash
# Freeze 当前环境（用于备份）
pip freeze > requirements-current.txt

# 只升级 pip
python -m pip install --upgrade pip
```

## 🎓 进阶配置

### 启用类型检查（可选）
在 `.vscode/settings.json` 改：
```json
"python.analysis.typeCheckingMode": "strict"
```
更严格的类型检查，适合大型项目。

### 自定义 Black 配置（可选）
在项目根目录创建 `pyproject.toml`：
```toml
[tool.black]
line-length = 100
target-version = ['py313']
```

### 启用 Mypy 类型检查（可选）
```bash
# 1. 安装
pip install mypy

# 2. 在 settings.json 添加：
"python.linting.mypyEnabled": true,
"python.linting.mypyPath": "/Users/kinglee/Documents/Projects/Trading/TradeMind/venv/bin/mypy"
```

## 📞 需要帮助？

- **Pylance 官方文档**：https://github.com/microsoft/pylance-release
- **Pytest 文档**：https://docs.pytest.org/
- **Black 文档**：https://black.readthedocs.io/
- **Pylint 规则列表**：https://pylint.pycqa.org/en/latest/messages/

---

**版本**: 2026-03-19  
**Python**: 3.13.12  
**虚拟环境**: `/Users/kinglee/Documents/Projects/Trading/TradeMind/venv`
