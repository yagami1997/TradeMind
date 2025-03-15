# TradeMind Lite 时间戳使用指南

## 概述
本文档提供了在TradeMind Lite项目中正确使用时间戳的指南，确保所有文档中的时间戳格式一致。

## 时间
2025-03-13 20:23:19 PDT

## 时间戳工具

项目提供了两个主要工具来管理时间戳：

1. **generate_timestamp.py** - 生成标准格式的时间戳
2. **update_timestamps.py** - 批量更新所有文档中的时间戳

## 单个时间戳生成

使用`generate_timestamp.py`脚本生成单个时间戳：

```bash
# 生成默认格式的时间戳（完整格式）
python scripts/generate_timestamp.py
# 输出: 2025-03-13 20:16:03 PDT

# 生成特定格式的时间戳
python scripts/generate_timestamp.py date     # 仅日期
python scripts/generate_timestamp.py datetime # 日期和时间（无时区）
python scripts/generate_timestamp.py compact  # 紧凑格式
python scripts/generate_timestamp.py week     # 年份和周数
```

## 批量更新时间戳

使用`update_timestamps.py`脚本批量更新所有文档中的时间戳：

```bash
# 更新所有文档中的时间戳
python scripts/update_timestamps.py
```

这将自动更新以下目录中所有Markdown文件的时间戳：
- project_management/
- project_management/actuals/
- project_management/actuals/tasks/

## 时间戳规范

1. **格式**: 所有时间戳必须使用`YYYY-MM-DD HH:MM:SS TZ`格式
2. **位置**: 
   - 文档顶部的"时间"字段
   - 文档底部的"最后更新"字段
3. **一致性**: 同一文档中的所有时间戳必须一致
4. **时区**: 使用美国太平洋时区（PST/PDT）

## 文档更新流程

1. 编辑文档内容
2. 运行时间戳更新脚本：
   ```bash
   python scripts/update_timestamps.py
   ```
3. 检查更新结果，确保所有文档的时间戳已正确更新
4. 提交更改

## 手动更新单个文档

如果需要手动更新单个文档的时间戳：

1. 生成时间戳：
   ```bash
   python scripts/generate_timestamp.py
   ```
2. 复制生成的时间戳
3. 更新文档顶部的"时间"字段
4. 更新文档底部的"最后更新"字段

## 常见问题

**Q: 为什么需要统一时间戳格式？**  
A: 统一的时间戳格式有助于跟踪文档的更新历史，确保所有团队成员了解文档的最新状态。

**Q: 如果忘记更新时间戳怎么办？**  
A: 可以随时运行`update_timestamps.py`脚本来更新所有文档的时间戳。

**Q: 时间戳工具不工作怎么办？**  
A: 确保已安装所需的Python依赖（pytz），并且脚本具有执行权限。

---
*最后更新: 2025-03-15 01:31:57 PDT* 