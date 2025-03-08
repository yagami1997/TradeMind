# TradeMind 项目管理指南

本文档提供 TradeMind 项目的管理指南，详细说明项目管理文档的组织结构、命名规范和使用方法。

## 目录结构

```
project_management/
├── PROJECT_MANAGEMENT_GUIDE.md  # 本文件（项目管理指南）
├── control/                  # 项目控制文档
│   ├── MAIN_CONTROL.md       # 项目总纲要（技术架构和开发流程）
│   └── PROJECT_CHARTER.md    # 项目立项计划书（项目管理和进度跟踪）
├── actuals/                  # 实际项目记录
│   └── reports/              # 项目报告
│       ├── daily/            # 日报
│       │   └── daily_report_YYYYMMDD.md
│       └── weekly/           # 周报
│           └── weekly_report_weekN.md
└── templates/                # 文档模板
    ├── daily_report_template.md    # 日报模板
    ├── weekly_report_template.md   # 周报模板
    └── PROJECT_PROGRESS_template.md # 项目进度模板
```

## 文件命名规范

- 日报文件：`daily_report_YYYYMMDD.md`，例如 `daily_report_20250304.md`
- 周报文件：`weekly_report_weekN.md`，例如 `weekly_report_week10.md`
- 控制文档：使用大写字母和下划线，例如 `MAIN_CONTROL.md`

## 时间戳规范

所有文档中的时间戳格式为：`[PST:YYYY-MM-DD HH:mm:ss]`

例如：`[PST:2025-03-07 20:56:23]`

## 文档更新频率

- 日报：每个工作日更新
- 周报：每周末更新
- 项目总纲要：根据需要更新，至少每周一次
- 项目立项计划书：在项目阶段性完成或里程碑达成时更新
- 项目进度文档：每周更新一次

## 项目控制命令

根据 Cursor 规则集，项目中可以使用以下控制命令：

- `[CODE NOW]` - 停止分析，开始编码
- `[FOCUS]` - 限制上下文到指定范围
- `[RESET]` - 清除当前方法并重新开始
- `[DECISION]` - 确定选择并向前推进

## 相关文档

- 项目进度跟踪：[PROJECT_PROGRESS.md](../PROJECT_PROGRESS.md)
- 项目总纲要：[MAIN_CONTROL.md](control/MAIN_CONTROL.md)
- 项目立项计划书：[PROJECT_CHARTER.md](control/PROJECT_CHARTER.md)

## 注意事项

- 所有报告文件应遵循对应的模板格式
- 确保时间戳使用正确的时区（PST）
- 定期更新文档以反映最新的项目状态
- 报告目录下的文件不会被 Git 跟踪，仅用于本地记录

**最后更新：** [PST:2025-03-07 21:00:22] 