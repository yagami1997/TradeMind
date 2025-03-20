# TASK-014: 自选股导入功能实现

## 基本信息

- **任务ID**: TASK-014
- **任务名称**: 自选股导入功能实现
- **负责人**: Yagami
- **开始日期**: 2025-03-16
- **计划完成日期**: 2025-03-20
- **实际完成日期**: 2025-03-16
- **状态**: ✅ 已完成
- **优先级**: 中
- **难度**: 中
- **预计工时**: 12小时
- **实际工时**: 10小时

## 任务描述

在Web界面上实现优雅的自选股导入功能，允许用户通过界面导入和管理自选股清单，替代当前手动预置的自选股清单方式。需要特别注意Yahoo Finance接口的限制，确保导入的股票代码有效且符合格式要求。同时，优化自选股编辑器的批量操作功能，提升用户体验。

## 任务目标

1. 设计并实现Web界面上的自选股导入功能
2. 支持多种导入方式（如文本输入、CSV上传等）
3. 实现对导入股票代码的验证和错误处理机制
4. 对非美股和非指数基金的股票代码进行适当的排除和提示
5. 确保指数基金的格式符合现有JSON结构要求
6. 实现导入后自动优化并保存watchlists.json文件
7. 提供友好的用户交互和错误反馈机制
8. 优化自选股编辑器的批量操作功能，提升用户体验
9. 实现批量操作菜单的智能位置跟随和滚动固定功能
10. 添加股票选择的视觉反馈和动画效果

## 格式差异分析

### 美股与港股格式差异

1. **美股格式**:
   - 普通股票: 直接使用代码，如 `AAPL`, `MSFT`, `NVDA`
   - 指数: 在导出文件中使用 `.` 前缀，如 `.DJI`, `.IXIC`, `.SPX`, `.VIX`, `.NDX`
   - 期货合约: 使用特殊格式，如 `GCmain`, `NQ2503`, `ES2503`

2. **港股格式**:
   - 使用5位数字代码，前面补0，如 `00700`, `03690`, `09988`
   - 恒生指数使用特殊代码 `800000`
   - 部分股票后缀有标识，如 `-W`, `-S`, `-SW`

3. **Yahoo Finance格式要求**:
   - 美股普通股票: 直接使用代码，如 `AAPL`, `MSFT`
   - 美股指数: 使用 `^` 前缀，如 `^DJI`, `^IXIC`, `^GSPC`, `^VIX`, `^NDX`
   - 港股: 需要添加后缀 `.HK`，如 `0700.HK`, `3690.HK`, `9988.HK`

### 指数格式转换规则

| 导出格式 | Yahoo Finance格式 | 说明 |
|---------|------------------|------|
| `.DJI`  | `^DJI`           | 道琼斯指数 |
| `.IXIC` | `^IXIC`          | 纳斯达克综合指数 |
| `.SPX`  | `^GSPC`          | 标普500指数 |
| `.VIX`  | `^VIX`           | 标普500波动率指数 |
| `.NDX`  | `^NDX`           | 纳斯达克100指数 |
| `800000` | `^HSI`          | 恒生指数 |

### 特殊情况处理

1. **期货合约**: 如 `GCmain`, `NQ2503`, `ES2503` 不支持直接导入，需要排除或提示用户
2. **ADR股票**: 如 `ADDYY`, `KDDIY`, `SFTBY`, `BAESY` 等需要特别标记
3. **特殊字符**: 如 `BRK.A` 中的点号需要保留

## 实现细节

### 前端实现

1. 在Web界面添加"导入自选股"功能入口
2. 设计导入界面，支持以下导入方式：
   - 文本框直接输入（支持多个股票代码，以逗号或换行分隔）
   - CSV文件上传（提供模板下载）
   - 从剪贴板粘贴
3. 实现实时验证功能，在用户输入过程中提供即时反馈
4. 设计预览界面，显示验证结果和可能的错误
5. 提供分类功能，允许用户为导入的股票指定或创建分组
6. 添加市场选择功能，让用户指定导入的是美股还是港股，以便正确处理格式

### 后端实现

1. 开发股票代码验证API，连接Yahoo Finance接口验证股票代码有效性
2. 实现股票信息获取功能，自动补充股票名称和其他元数据
3. 开发错误处理和容错机制：
   - 识别并排除非美股和非指数基金的股票代码
   - 自动修正常见的格式错误（如小写转大写）
   - 处理重复股票代码
4. 实现watchlists.json文件的读取、更新和保存功能
5. 确保指数基金格式符合要求（如^DJI格式）
6. 实现代码格式转换功能：
   - 美股指数: `.DJI` → `^DJI`, `.SPX` → `^GSPC` 等
   - 港股: `00700` → `0700.HK` 等

### 自选股编辑器批量操作功能优化

1. **批量操作菜单位置优化**:
   - 重新设计批量操作菜单的位置逻辑，使其智能跟随用户选择的股票位置
   - 实现批量操作菜单的滚动跟随功能，确保在任何滚动位置都能看到操作菜单
   - 优化批量操作菜单的样式，增加固定显示和突出效果

2. **股票选择视觉反馈**:
   - 添加选中股票的视觉高亮效果
   - 实现选中和取消选中的过渡动画
   - 优化选中状态的显示样式

3. **用户体验改进**:
   - 实现批量操作菜单的响应式设计，适应不同屏幕尺寸
   - 优化批量操作的用户体验流程，减少操作步骤和等待时间
   - 添加操作成功的视觉反馈

### 代码转换算法

```javascript
function convertStockCode(code, market) {
  // 美股指数转换
  const indexMapping = {
    '.DJI': '^DJI',
    '.IXIC': '^IXIC',
    '.SPX': '^GSPC',
    '.VIX': '^VIX',
    '.NDX': '^NDX'
  };
  
  // 处理美股
  if (market === 'US') {
    // 处理指数
    if (code in indexMapping) {
      return indexMapping[code];
    }
    
    // 处理期货合约
    if (code.includes('main') || /\d{4}$/.test(code)) {
      return { valid: false, reason: '期货合约不支持导入' };
    }
    
    // 普通美股代码直接返回
    return code.toUpperCase();
  }
  
  // 处理港股
  if (market === 'HK') {
    // 处理恒生指数
    if (code === '800000') {
      return '^HSI';
    }
    
    // 移除前导零并添加.HK后缀
    return code.replace(/^0+/, '') + '.HK';
  }
  
  return { valid: false, reason: '不支持的市场' };
}
```

### 批量操作菜单位置优化代码

```javascript
// 渲染多选操作栏
function renderMultiSelectActions() {
    // 移除现有的多选操作栏
    const existingActions = document.querySelector('.multi-select-actions');
    if (existingActions) {
        existingActions.remove();
    }
    
    // 如果有选中的股票，显示多选操作栏
    if (selectedStocks.length > 0) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'multi-select-actions';
        
        const selectedCount = document.createElement('span');
        selectedCount.textContent = `已选择 ${selectedStocks.length} 个股票`;
        
        const moveSelectedBtn = document.createElement('button');
        moveSelectedBtn.innerHTML = '<i class="bi bi-arrows-move"></i> 批量移动';
        moveSelectedBtn.onclick = moveSelectedStocks;
        
        const deleteSelectedBtn = document.createElement('button');
        deleteSelectedBtn.innerHTML = '<i class="bi bi-trash"></i> 批量删除';
        deleteSelectedBtn.onclick = deleteSelectedStocks;
        
        const cancelBtn = document.createElement('button');
        cancelBtn.innerHTML = '<i class="bi bi-x-circle"></i> 取消选择';
        cancelBtn.onclick = clearSelection;
        
        actionsDiv.appendChild(selectedCount);
        actionsDiv.appendChild(moveSelectedBtn);
        actionsDiv.appendChild(deleteSelectedBtn);
        actionsDiv.appendChild(cancelBtn);
        
        // 查找所有选中的股票行
        const selectedRows = [];
        selectedStocks.forEach(stock => {
            const row = document.querySelector(`.stock-row[data-group="${stock.group}"][data-code="${stock.code}"]`);
            if (row) selectedRows.push(row);
        });
        
        if (selectedRows.length > 0) {
            // 找到最后一个选中的行
            const lastSelectedRow = selectedRows[selectedRows.length - 1];
            
            // 找到该行所在的分组
            const groupDiv = lastSelectedRow.closest('.watchlist-group');
            if (groupDiv) {
                // 将操作栏插入到分组的顶部
                groupDiv.insertBefore(actionsDiv, groupDiv.firstChild);
                
                // 滚动到操作栏位置
                setTimeout(() => {
                    actionsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
                return;
            }
        }
        
        // 如果没有找到选中的行或分组，则插入到容器顶部
        watchlistContainer.insertBefore(actionsDiv, watchlistContainer.firstChild);
    }
    
    // 更新选中状态
    updateSelectionUI();
}
```

### 容错与交互方案

1. **输入验证**：
   - 实时验证输入的股票代码格式
   - 对不符合格式的代码提供明确的错误提示
   - 支持批量验证，并显示有效/无效代码的数量和详情

2. **错误处理**：
   - 对于无效的股票代码，提供详细的错误原因（如"不存在"、"非美股"等）
   - 对于可能的拼写错误，提供相似股票代码的建议
   - 允许用户选择忽略错误并继续导入有效的股票代码

3. **用户反馈**：
   - 使用颜色编码标识验证状态（绿色=有效，红色=无效，黄色=警告）
   - 提供导入进度和结果的可视化展示
   - 导入完成后显示成功/失败的统计信息

4. **数据保护**：
   - 在覆盖现有自选股列表前提供确认对话框
   - 实现自动备份功能，保存修改前的watchlists.json
   - 提供撤销最近导入的选项

5. **格式转换提示**：
   - 在导入过程中显示格式转换信息，如 `.DJI` → `^DJI`
   - 对于不支持的代码（如期货合约）提供明确的排除原因

## 技术要点

1. 使用异步请求验证股票代码，避免阻塞用户界面
2. 实现节流(throttling)机制，避免向Yahoo Finance API发送过多请求
3. 使用本地缓存存储已验证的股票信息，减少重复验证
4. 确保watchlists.json文件的格式和结构保持一致
5. 实现适当的错误日志记录，便于问题排查
6. 开发代码格式转换库，处理不同市场和数据源的格式差异
7. 使用CSS动画和过渡效果提升用户体验
8. 实现滚动监听功能，确保批量操作菜单在滚动时保持可见
9. 优化DOM操作，提高页面响应速度

## 验收标准

1. 用户能够通过Web界面成功导入自选股清单
2. 系统能够正确验证股票代码，并排除无效代码
3. 导入的自选股清单正确保存到watchlists.json文件
4. 用户界面提供清晰的反馈和错误提示
5. 功能在不同浏览器和设备上表现一致
6. 代码符合项目的编码规范和最佳实践
7. 正确处理美股指数格式转换（`.DJI` → `^DJI` 等）
8. 正确处理港股代码格式（添加`.HK`后缀）
9. 批量操作菜单能够智能跟随用户选择的股票位置
10. 批量操作菜单在滚动时保持可见
11. 选中股票有明显的视觉反馈和动画效果

## 依赖关系

- 需要Yahoo Finance API访问权限
- 依赖现有的Web界面框架
- 需要文件系统写入权限（用于更新watchlists.json）
- 依赖Bootstrap图标库（用于批量操作菜单图标）
- 依赖现有的CSS变量系统（用于主题颜色）

## 风险与缓解措施

1. **风险**：Yahoo Finance API限制或变更
   **缓解**：实现请求缓存和备用数据源

2. **风险**：大量股票代码验证可能导致性能问题
   **缓解**：实现批处理和进度指示器

3. **风险**：文件写入权限问题
   **缓解**：实现适当的错误处理和用户提示

4. **风险**：格式转换错误导致无效代码
   **缓解**：实现转换前后的验证机制，确保转换结果有效

5. **风险**：批量操作菜单在某些浏览器中显示异常
   **缓解**：使用标准CSS属性，避免使用实验性功能

## 备注

- 考虑未来扩展支持其他市场（如A股）的可能性
- 可能需要更新用户文档，说明新功能的使用方法
- 当前仅支持美股和指数基金的导入，港股支持将在未来版本中考虑
- 批量操作功能的优化显著提升了用户体验，特别是在处理大量股票时
- 视觉反馈和动画效果使操作更加直观，减少了用户的认知负担

*最后更新: 2025-03-19 18:46:03 PDT* 