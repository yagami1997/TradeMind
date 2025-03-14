# 文档更新检查清单

## 概述
本文档提供了更新项目文档时需要遵循的标准检查清单，确保文档的一致性、准确性和时效性。

## 时间
2025-03-13 20:23:19 PDT

## 时间戳生成
- [ ] 使用`scripts/generate_timestamp.py`生成标准时间戳
  ```bash
  python scripts/generate_timestamp.py
  ```
- [ ] 复制生成的时间戳（格式：YYYY-MM-DD HH:MM:SS TZ）
- [ ] 更新文档顶部的"时间"字段
- [ ] 更新文档底部的"最后更新"时间戳

## 内容更新
- [ ] 确保所有状态标记（✅, ⏳, 🔄, ❌）正确反映当前进度
- [ ] 更新进度百分比（如适用）
- [ ] 添加新的进展记录，包含日期、模块、进展和备注
- [ ] 检查并更新依赖关系
- [ ] 确保所有链接和引用有效

## 格式检查
- [ ] 保持Markdown格式一致性
- [ ] 表格对齐和格式正确
- [ ] 标题层级使用正确
- [ ] 列表格式统一
- [ ] 代码块使用正确的语言标记

## 内容验证
- [ ] 技术术语使用准确
- [ ] 数据和统计信息准确无误
- [ ] 所有任务状态与实际进度一致
- [ ] 检查拼写和语法错误
- [ ] 确保文档间的交叉引用一致

## 最终检查
- [ ] 文档整体结构清晰
- [ ] 内容完整，无遗漏部分
- [ ] 时间戳格式一致
- [ ] 提交前进行最终审阅

## 时间戳格式参考
```
# 完整格式（默认）
python scripts/generate_timestamp.py full
# 输出: 2025-03-13 20:16:03 PDT

# 仅日期
python scripts/generate_timestamp.py date
# 输出: 2025-03-13

# 日期和时间（无时区）
python scripts/generate_timestamp.py datetime
# 输出: 2025-03-13 20:16:03

# 紧凑格式
python scripts/generate_timestamp.py compact
# 输出: 20250313

# 年份和周数
python scripts/generate_timestamp.py week
# 输出: 2025W10
```

---
*最后更新: 2025-03-13 20:23:19 PDT* 