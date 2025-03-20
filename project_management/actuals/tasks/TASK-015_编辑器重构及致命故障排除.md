# TASK-015: 编辑器重构及致命故障排除

## 基本信息

- **任务ID**: TASK-015
- **任务名称**: 编辑器重构及致命故障排除
- **负责人**: Yagami
- **开始日期**: 2025-03-19
- **计划完成日期**: 2025-03-19
- **实际完成日期**: 2025-03-19
- **状态**: ✅ 已完成
- **优先级**: 高
- **难度**: 高
- **预计工时**: 8小时
- **实际工时**: 6小时

## 任务描述

在使用自选股编辑器过程中发现了一个严重的系统故障：JavaScript的`Object.keys()`方法对股票代码进行了自动字母排序，这个问题导致了系统在分析时使用了错误的股票顺序，影响了分析结果的准确性。同时，编辑器中存在大量硬编码的样式和逻辑，需要进行重构以提高代码质量和可维护性。

## 任务目标

1. 修复`Object.keys()`导致的股票自动字母排序问题
2. 实现可靠的股票顺序存储和读取机制
3. 实现分类的拖拽排序功能
4. 实现股票的跨分类拖拽功能
5. 重构编辑器代码，移除硬编码
6. 完善手动编辑状态的锁定机制

## 问题分析

### 1. 致命故障：自动字母排序问题

**问题描述**：
- 使用`Object.keys()`获取股票列表导致自动字母排序
- 分析结果使用了错误的股票顺序
- 用户自定义的分析顺序被破坏

**影响范围**：
- 所有依赖股票顺序的分析功能
- 用户自定义的分析流程
- 技术指标的计算结果

**根本原因**：
- JavaScript的`Object.keys()`方法会自动对键进行字母排序
- 未使用专门的数据结构存储顺序信息
- 缺少顺序验证机制

### 2. 编辑器设计问题

**硬编码问题**：
- 样式和布局硬编码在HTML中
- 事件处理逻辑分散
- 配置项未集中管理

**状态管理问题**：
- 手动编辑状态未正确保存
- 分类顺序未持久化
- 股票顺序未同步

## 解决方案

### 1. 数据结构重设计

```javascript
{
  "watchlists": {
    "科技股": {
      "AAPL": "苹果",
      "MSFT": "微软"
    }
  },
  "groups_order": ["科技股", "医疗股"],
  "stocks_order": {
    "科技股": ["AAPL", "MSFT"],
    "医疗股": ["JNJ", "PFE"]
  },
  "hasBeenManuallyEdited": true
}
```

### 2. 顺序管理实现

```javascript
class OrderManager {
  constructor() {
    this.watchlistData = null;
  }

  // 获取分类顺序
  getGroupsOrder() {
    return this.watchlistData.groups_order || [];
  }

  // 获取特定分类的股票顺序
  getStocksOrder(group) {
    return this.watchlistData.stocks_order[group] || [];
  }

  // 更新分类顺序
  async updateGroupsOrder(newOrder) {
    this.watchlistData.groups_order = newOrder;
    await this.save();
    this.setManuallyEdited(true);
  }

  // 更新股票顺序
  async updateStocksOrder(group, newOrder) {
    this.watchlistData.stocks_order[group] = newOrder;
    await this.save();
    this.setManuallyEdited(true);
  }
}
```

### 3. 拖拽排序实现

```javascript
class DragDropManager {
  constructor(container) {
    this.container = container;
    this.orderManager = new OrderManager();
  }

  // 初始化分类拖拽
  initializeGroupDrag() {
    new Sortable(this.container, {
      group: 'watchlist-groups',
      animation: 150,
      handle: '.group-header',
      onEnd: this.handleGroupReorder.bind(this)
    });
  }

  // 初始化股票拖拽
  initializeStockDrag(groupElement) {
    new Sortable(groupElement.querySelector('.stock-list'), {
      group: 'stocks',
      animation: 150,
      handle: '.drag-handle',
      onEnd: this.handleStockReorder.bind(this)
    });
  }
}
```

### 4. 手动编辑状态管理

```javascript
class EditStateManager {
  constructor() {
    this.edited = false;
  }

  // 设置编辑状态
  async setManuallyEdited(edited) {
    this.edited = edited;
    await this.saveEditState();
    this.updateUI();
  }

  // 保存编辑状态
  async saveEditState() {
    try {
      await fetch('/api/set-watchlist-edit-flag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited: this.edited })
      });
    } catch (error) {
      console.error('保存编辑状态失败:', error);
    }
  }

  // 更新UI状态
  updateUI() {
    const luckyButton = document.querySelector('.lucky-button');
    if (luckyButton) {
      luckyButton.disabled = this.edited;
      luckyButton.title = this.edited ? 
        '已手动编辑列表，不能使用该功能' : 
        '随机选择股票进行分析';
    }
  }
}
```

## 验收标准

1. 股票顺序完全符合用户设定，不会自动排序
2. 分类可以通过拖拽重新排序
3. 股票可以在分类间拖拽移动
4. 所有顺序变更都能正确保存
5. 手动编辑状态正确锁定功能
6. 编辑器代码没有硬编码的样式和逻辑

## 测试结果

1. **顺序保持测试**：
   - 创建多个分类并添加股票 ✅
   - 验证顺序是否保持不变 ✅
   - 刷新页面后验证顺序 ✅

2. **拖拽功能测试**：
   - 分类拖拽排序 ✅
   - 股票跨分类拖拽 ✅
   - 拖拽后的顺序保存 ✅

3. **编辑状态测试**：
   - 手动编辑标记设置 ✅
   - 功能锁定验证 ✅
   - 状态持久化测试 ✅

## 备注

1. 此次重构解决了严重影响分析准确性的排序问题
2. 新的数据结构设计更好地支持了顺序管理
3. 拖拽排序功能提升了用户体验
4. 建议定期检查类似的JavaScript特性导致的潜在问题

*最后更新: 2025-03-19 18:36:48 PDT* 