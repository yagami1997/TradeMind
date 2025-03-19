// WatchlistEditor - 现代化的股票列表编辑器
class WatchlistEditor {
    constructor() {
        this.state = {
            watchlists: new Map(), // 使用 Map 存储分组和股票
            groupOrder: [], // 分组顺序
            selectedStocks: new Set(), // 选中的股票
            isDragging: false,
            hasUnsavedChanges: false
        };
        
        this.init();
    }
    
    init() {
        // 添加自定义样式以确保表格对齐
        this.addCustomStyles();
        this.loadData();
        this.initDragAndDrop();
        this.bindEvents();
    }
    
    // 添加自定义样式
    addCustomStyles() {
        // 创建样式元素
        const style = document.createElement('style');
        style.textContent = `
            .table-stocks {
                table-layout: fixed;
                width: 100%;
                border-collapse: collapse;
            }
            .table-stocks thead {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
            }
            .table-stocks th {
                padding: 10px 8px;
                font-weight: 600;
                color: #495057;
            }
            .table-stocks th:nth-child(1) {
                width: 40px;
                text-align: center;
            }
            .table-stocks th:nth-child(2) {
                width: 40px;
                text-align: center;
            }
            .table-stocks th:nth-child(3) {
                width: 120px;
                text-align: left;
                padding-left: 12px;
            }
            .table-stocks th:nth-child(4) {
                text-align: left;
                padding-left: 12px;
            }
            .table-stocks th:nth-child(5) {
                width: 100px;
                text-align: center;
            }
            .table-stocks td {
                vertical-align: middle;
                padding: 8px;
                border-top: 1px solid #dee2e6;
            }
            .table-stocks td:nth-child(1),
            .table-stocks td:nth-child(2),
            .table-stocks td:nth-child(5) {
                text-align: center;
            }
            .table-stocks td:nth-child(3),
            .table-stocks td:nth-child(4) {
                text-align: left;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                padding-left: 12px;
            }
            .table-stocks tr.selected {
                background-color: rgba(0, 123, 255, 0.1);
            }
            .table-stocks tr:hover {
                background-color: rgba(0, 0, 0, 0.03);
            }
            .table-stocks .drag-handle {
                cursor: move;
                color: #adb5bd;
            }
            .table-stocks .drag-handle:hover {
                color: #6c757d;
            }
            .action-buttons {
                width: 80px;
                display: inline-flex;
                justify-content: center;
            }
            .action-buttons .btn {
                padding: 0.25rem 0.5rem;
            }
            /* 修改删除按钮样式 */
            .delete-stock-btn {
                background-color: #28a745 !important;
                color: white !important;
                border-color: #28a745 !important;
            }
            .delete-stock-btn:hover {
                background-color: #dc3545 !important;
                border-color: #dc3545 !important;
            }
            .delete-group-btn {
                background-color: #28a745 !important;
                color: white !important;
                border-color: #28a745 !important;
            }
            .delete-group-btn:hover {
                background-color: #dc3545 !important;
                border-color: #dc3545 !important;
            }
            .form-check {
                display: flex;
                justify-content: center;
            }
            .watchlist-group .card-header {
                background-color: #f8f9fa;
                padding: 0.75rem 1rem;
            }
            .watchlist-group .group-name {
                font-weight: 600;
                font-size: 1.1rem;
            }
        `;
        
        // 添加到文档头部
        document.head.appendChild(style);
    }
    
    // 加载数据
    async loadData() {
        try {
            // 添加时间戳以防止缓存
            const timestamp = new Date().getTime();
            const response = await fetch(`/api/watchlists?t=${timestamp}`);
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || '加载数据失败');
            
            // 清空现有数据
            this.state.watchlists.clear();
            
            // 使用服务器返回的分组顺序
            this.state.groupOrder = data.groups_order || [];
            console.log("从服务器加载的分组顺序:", this.state.groupOrder);
            
            // 获取服务器返回的股票顺序 (新增)
            const stocks_order = data.stocks_order || {};
            console.log("从服务器加载的股票顺序:", stocks_order);
            
            // 按照服务器返回的顺序初始化数据
            this.state.groupOrder.forEach(groupName => {
                const stocks = data.watchlists[groupName];
                if (stocks) {
                    const stocksMap = new Map();
                    
                    // 新方法：按照服务器提供的股票顺序处理
                    if (stocks_order[groupName]) {
                        // 使用服务器返回的顺序
                        stocks_order[groupName].forEach(code => {
                            if (code in stocks) {
                                stocksMap.set(code, stocks[code]);
                            }
                        });
                        
                        // 检查是否有遗漏的股票（以防万一）
                        Object.entries(stocks).forEach(([code, name]) => {
                            if (!stocksMap.has(code)) {
                                stocksMap.set(code, name);
                            }
                        });
                    } else {
                        // 没有特定顺序，使用Object.entries（可能会排序）
                        Object.entries(stocks).forEach(([code, name]) => {
                            stocksMap.set(code, name);
                        });
                    }
                    
                    // 记录调试信息
                    if (groupName === '指数与ETF') {
                        console.log("加载的'指数与ETF'分组的股票顺序(前5个):", 
                            Array.from(stocksMap.keys()).slice(0, 5));
                    }
                    
                    this.state.watchlists.set(groupName, stocksMap);
                }
            });
            
            // 添加任何遗漏的分组
            Object.keys(data.watchlists).forEach(groupName => {
                if (!this.state.watchlists.has(groupName)) {
                    const stocks = data.watchlists[groupName];
                    const stocksMap = new Map();
                    
                    // 同样使用服务器返回的顺序
                    if (stocks_order[groupName]) {
                        stocks_order[groupName].forEach(code => {
                            if (code in stocks) {
                                stocksMap.set(code, stocks[code]);
                            }
                        });
                        
                        // 检查遗漏的股票
                        Object.entries(stocks).forEach(([code, name]) => {
                            if (!stocksMap.has(code)) {
                                stocksMap.set(code, name);
                            }
                        });
                    } else {
                        Object.entries(stocks).forEach(([code, name]) => {
                            stocksMap.set(code, name);
                        });
                    }
                    
                    this.state.watchlists.set(groupName, stocksMap);
                    this.state.groupOrder.push(groupName);
                }
            });
            
            console.log("数据加载完成，重新初始化拖拽功能");
            this.render();
            this.initDragAndDrop();
        } catch (error) {
            console.error('加载数据失败:', error);
            this.showToast('加载数据失败，请刷新页面重试', 'error');
        }
    }
    
    // 初始化拖拽功能
    initDragAndDrop() {
        // 分组拖拽排序
        new Sortable(document.getElementById('watchlistContainer'), {
            animation: 150,
            handle: '.group-header',
            draggable: '.watchlist-group',
            onEnd: async (evt) => {
                const newOrder = Array.from(document.querySelectorAll('.watchlist-group'))
                    .map(group => group.dataset.group);
                this.state.groupOrder = newOrder;
                this.state.hasUnsavedChanges = true;
                
                // 设置编辑标志
                await this.setEditFlag();
            }
        });
        
        // 为每个分组初始化股票拖拽
        this.state.groupOrder.forEach(groupName => {
            const stocksContainer = document.querySelector(`.watchlist-group[data-group="${groupName}"] tbody`);
            if (stocksContainer) {
                new Sortable(stocksContainer, {
                    animation: 150,
                    handle: '.drag-handle',
                    draggable: 'tr',
                    group: 'stocks',
                    onEnd: async (evt) => {
                        const fromGroup = evt.from.closest('.watchlist-group').dataset.group;
                        const toGroup = evt.to.closest('.watchlist-group').dataset.group;
                        
                        if (fromGroup !== toGroup) {
                            // 处理跨分组移动
                            await this.handleStockMove(evt.item.dataset.symbol, fromGroup, toGroup);
                        } else {
                            // 更新同分组内顺序
                            await this.updateStockOrder(fromGroup);
                        }
                        
                        this.state.hasUnsavedChanges = true;
                    }
                });
            }
        });
    }
    
    // 绑定事件处理
    bindEvents() {
        // 关闭按钮
        document.getElementById('closeEditorBtn').addEventListener('click', () => {
            if (this.state.hasUnsavedChanges) {
                if (confirm('您有未保存的更改，确定要离开吗？')) {
                    window.close();
                }
            } else {
                window.close();
            }
        });
        
        // 添加分组
        document.getElementById('addGroupBtn').addEventListener('click', () => this.addGroup());
        
        // 刷新
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadData());
        
        // 排序分组按钮
        document.getElementById('sortGroupsBtn').addEventListener('click', () => this.showSortGroupsDialog());
        
        // 全部折叠按钮
        document.getElementById('collapseAllBtn').addEventListener('click', () => this.collapseAllGroups());
        
        // 全部展开按钮
        document.getElementById('expandAllBtn').addEventListener('click', () => this.expandAllGroups());
        
        // 保存按钮
        document.getElementById('saveAllBtn').addEventListener('click', () => this.saveChanges());
        
        // 监听页面离开
        window.addEventListener('beforeunload', (e) => {
            if (this.state.hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '您有未保存的更改，确定要离开吗？';
            }
        });
    }
    
    // 渲染界面
    render() {
        const container = document.getElementById('watchlistContainer');
        let html = '';
        
        this.state.groupOrder.forEach(groupName => {
            const stocks = this.state.watchlists.get(groupName);
            if (!stocks) return;
            
            html += `
                <div class="card mb-4 watchlist-group" data-group="${groupName}">
                    <div class="card-header group-header">
                        <div class="d-flex align-items-center justify-content-between">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-grip-vertical drag-handle me-2"></i>
                                <i class="bi bi-chevron-down toggle-group-btn me-2" style="cursor: pointer;"></i>
                                <span class="group-name">${groupName}</span>
                                <span class="badge bg-secondary ms-2">${stocks.size}</span>
                            </div>
                            <div class="btn-group">
                                <button type="button" class="btn btn-sm btn-outline-primary add-stock-btn">
                                    <i class="bi bi-plus-lg"></i> 添加股票
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary rename-group-btn">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button type="button" class="btn btn-sm delete-group-btn">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-hover table-stocks mb-0">
                            <thead>
                                <tr>
                                    <th width="40px" style="text-align: center">
                                        <div class="form-check">
                                            <input type="checkbox" class="form-check-input select-all-stocks" data-group="${groupName}">
                                        </div>
                                    </th>
                                    <th width="40px" style="text-align: center"></th>
                                    <th width="120px" style="text-align: left">代码</th>
                                    <th style="text-align: left">名称</th>
                                    <th width="100px" style="text-align: center">操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.renderStocks(groupName, stocks)}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        this.initDragAndDrop();
        this.bindGroupEvents();
    }
    
    // 渲染股票列表
    renderStocks(groupName, stocks) {
        let html = '';
        
        // 使用Array.from获取股票数组，保持原始顺序
        const stockEntries = Array.from(stocks.entries());
        
        // 不进行任何排序，直接使用Map中的顺序
        stockEntries.forEach(([code, name]) => {
            const isSelected = this.state.selectedStocks.has(`${groupName}:${code}`);
            html += `
                <tr class="stock-row ${isSelected ? 'selected' : ''}" data-symbol="${code}" data-group="${groupName}">
                    <td>
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input stock-checkbox" 
                                   ${isSelected ? 'checked' : ''}>
                        </div>
                    </td>
                    <td>
                        <i class="bi bi-grip-vertical drag-handle"></i>
                    </td>
                    <td>${code}</td>
                    <td>${name}</td>
                    <td>
                        <div class="btn-group btn-group-sm action-buttons">
                            <button type="button" class="btn btn-outline-secondary edit-stock-btn">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="btn delete-stock-btn">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });
        return html;
    }
    
    // 绑定分组相关事件
    bindGroupEvents() {
        // 添加股票按钮
        document.querySelectorAll('.add-stock-btn').forEach(btn => {
            const groupName = btn.closest('.watchlist-group').dataset.group;
            btn.onclick = () => this.addStock(groupName);
        });
        
        // 重命名分组按钮
        document.querySelectorAll('.rename-group-btn').forEach(btn => {
            const groupName = btn.closest('.watchlist-group').dataset.group;
            btn.onclick = () => this.renameGroup(groupName);
        });
        
        // 删除分组按钮
        document.querySelectorAll('.delete-group-btn').forEach(btn => {
            const groupName = btn.closest('.watchlist-group').dataset.group;
            btn.onclick = () => this.deleteGroup(groupName);
        });
        
        // 折叠/展开分组按钮
        document.querySelectorAll('.toggle-group-btn').forEach(btn => {
            const group = btn.closest('.watchlist-group');
            btn.onclick = () => this.toggleGroup(group);
        });
        
        // 股票选择框
        document.querySelectorAll('.stock-checkbox').forEach(checkbox => {
            const row = checkbox.closest('.stock-row');
            const groupName = row.dataset.group;
            const code = row.dataset.symbol;
            checkbox.onchange = () => this.toggleStockSelection(groupName, code);
        });
        
        // 全选框
        document.querySelectorAll('.select-all-stocks').forEach(checkbox => {
            const groupName = checkbox.dataset.group;
            checkbox.onchange = () => this.toggleGroupSelection(groupName, checkbox.checked);
        });
        
        // 编辑股票按钮
        document.querySelectorAll('.edit-stock-btn').forEach(btn => {
            const row = btn.closest('.stock-row');
            const groupName = row.dataset.group;
            const code = row.dataset.symbol;
            btn.onclick = () => this.editStock(groupName, code);
        });
        
        // 删除股票按钮
        document.querySelectorAll('.delete-stock-btn').forEach(btn => {
            const row = btn.closest('.stock-row');
            const groupName = row.dataset.group;
            const code = row.dataset.symbol;
            btn.onclick = () => this.deleteStock(groupName, code);
        });
    }
    
    // 添加设置编辑标志的助手函数
    async setEditFlag() {
        try {
            const editFlagResponse = await fetch('/api/set-watchlist-edit-flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ edited: true })
            });
            
            const editFlagData = await editFlagResponse.json();
            if (editFlagData.success) {
                console.log('成功设置手动编辑标志');
            } else {
                console.warn('设置手动编辑标志失败:', editFlagData.error);
            }
            return editFlagData.success;
        } catch (flagError) {
            console.error('设置手动编辑标志时出错:', flagError);
            return false;
        }
    }
    
    // 更新股票顺序
    async updateStockOrder(groupName) {
        const stocks = this.state.watchlists.get(groupName);
        if (!stocks) return;
        
        const newOrder = new Map();
        const rows = document.querySelectorAll(`.watchlist-group[data-group="${groupName}"] .stock-row`);
        
        // 确保用正确的顺序遍历DOM元素
        rows.forEach(row => {
            const code = row.dataset.symbol;
            if (stocks.has(code)) {
                newOrder.set(code, stocks.get(code));
            }
        });
        
        // 使用新的顺序更新Map
        this.state.watchlists.set(groupName, newOrder);
        this.state.hasUnsavedChanges = true;
        
        // 设置编辑标志
        await this.setEditFlag();
        
        // 记录日志以帮助调试
        console.log(`已更新分组 "${groupName}" 中的股票顺序`);
        console.log(`新顺序中的前3个股票: ${Array.from(newOrder.keys()).slice(0, 3).join(', ')}`);
    }
    
    // 处理股票移动
    async handleStockMove(code, fromGroup, toGroup) {
        const fromStocks = this.state.watchlists.get(fromGroup);
        const toStocks = this.state.watchlists.get(toGroup);
        if (!fromStocks || !toStocks || !fromStocks.has(code)) return;
        
        const name = fromStocks.get(code);
        fromStocks.delete(code);
        toStocks.set(code, name);
        
        // 更新选中状态
        this.state.selectedStocks.delete(`${fromGroup}:${code}`);
        
        this.state.hasUnsavedChanges = true;
        
        // 设置编辑标志
        await this.setEditFlag();
    }
    
    // 添加分组
    async addGroup() {
        const groupName = prompt('请输入新分组名称:');
        if (!groupName || groupName.trim() === '') {
            this.showToast('分组名称不能为空', 'warning');
            return;
        }
        
        if (this.state.watchlists.has(groupName)) {
            this.showToast(`分组 "${groupName}" 已存在`, 'warning');
            return;
        }
        
        this.state.watchlists.set(groupName, new Map());
        this.state.groupOrder.push(groupName);
        this.state.hasUnsavedChanges = true;
        
        // 设置编辑标志
        await this.setEditFlag();
        
        this.render();
        this.showToast(`分组 "${groupName}" 已添加`, 'success');
    }
    
    // 重命名分组
    async renameGroup(oldName) {
        const newName = prompt('请输入新的分组名称:', oldName);
        if (!newName || newName === oldName) return;
        
        if (this.state.watchlists.has(newName)) {
            this.showToast(`分组 "${newName}" 已存在`, 'warning');
            return;
        }
        
        const stocks = this.state.watchlists.get(oldName);
        this.state.watchlists.delete(oldName);
        this.state.watchlists.set(newName, stocks);
        
        const index = this.state.groupOrder.indexOf(oldName);
        if (index !== -1) {
            this.state.groupOrder[index] = newName;
        }
        
        this.state.hasUnsavedChanges = true;
        
        // 设置编辑标志
        await this.setEditFlag();
        
        this.render();
        this.showToast(`分组已重命名为 "${newName}"`, 'success');
    }
    
    // 删除分组
    async deleteGroup(groupName) {
        const stocks = this.state.watchlists.get(groupName);
        if (!stocks) return;
        
        const confirmMessage = stocks.size > 0
            ? `分组 "${groupName}" 包含 ${stocks.size} 个股票，删除分组将同时删除所有股票。确定要删除吗?`
            : `确定要删除分组 "${groupName}" 吗?`;
            
        if (!confirm(confirmMessage)) return;
        
        this.state.watchlists.delete(groupName);
        const index = this.state.groupOrder.indexOf(groupName);
        if (index !== -1) {
            this.state.groupOrder.splice(index, 1);
        }
        
        this.state.hasUnsavedChanges = true;
        
        // 设置编辑标志
        await this.setEditFlag();
        
        this.render();
        this.showToast(`分组 "${groupName}" 已删除`, 'success');
    }
    
    // 添加股票
    async addStock(groupName) {
        const code = prompt('请输入股票代码:');
        if (!code || code.trim() === '') {
            this.showToast('股票代码不能为空', 'warning');
            return;
        }
        
        const stocks = this.state.watchlists.get(groupName);
        if (stocks.has(code)) {
            this.showToast(`股票 ${code} 已存在于该分组`, 'warning');
            return;
        }
        
        const name = prompt('请输入股票名称 (可选):', '');
        stocks.set(code, name || '');
        
        this.state.hasUnsavedChanges = true;
        
        // 设置手动编辑标志
        try {
            const editFlagResponse = await fetch('/api/set-watchlist-edit-flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ edited: true })
            });
            
            const editFlagData = await editFlagResponse.json();
            if (editFlagData.success) {
                console.log('添加股票：成功设置手动编辑标志');
            } else {
                console.warn('添加股票：设置手动编辑标志失败:', editFlagData.error);
            }
        } catch (flagError) {
            console.error('添加股票：设置手动编辑标志时出错:', flagError);
        }
        
        this.render();
        this.showToast(`股票 ${code} 已添加到 "${groupName}"`, 'success');
    }
    
    // 编辑股票
    async editStock(groupName, code) {
        const stocks = this.state.watchlists.get(groupName);
        if (!stocks || !stocks.has(code)) return;
        
        const name = stocks.get(code);
        const newName = prompt('请输入新的股票名称:', name);
        if (newName === null) return;
        
        stocks.set(code, newName);
        this.state.hasUnsavedChanges = true;
        
        // 设置手动编辑标志
        try {
            const editFlagResponse = await fetch('/api/set-watchlist-edit-flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ edited: true })
            });
            
            const editFlagData = await editFlagResponse.json();
            if (editFlagData.success) {
                console.log('编辑股票：成功设置手动编辑标志');
            } else {
                console.warn('编辑股票：设置手动编辑标志失败:', editFlagData.error);
            }
        } catch (flagError) {
            console.error('编辑股票：设置手动编辑标志时出错:', flagError);
        }
        
        this.render();
        this.showToast(`股票 ${code} 已更新`, 'success');
    }
    
    // 删除股票
    async deleteStock(groupName, code) {
        if (!confirm(`确定要删除股票 ${code} 吗?`)) return;
        
        const stocks = this.state.watchlists.get(groupName);
        if (!stocks || !stocks.has(code)) return;
        
        stocks.delete(code);
        this.state.selectedStocks.delete(`${groupName}:${code}`);
        
        this.state.hasUnsavedChanges = true;
        
        // 设置手动编辑标志
        try {
            const editFlagResponse = await fetch('/api/set-watchlist-edit-flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ edited: true })
            });
            
            const editFlagData = await editFlagResponse.json();
            if (editFlagData.success) {
                console.log('删除股票：成功设置手动编辑标志');
            } else {
                console.warn('删除股票：设置手动编辑标志失败:', editFlagData.error);
            }
        } catch (flagError) {
            console.error('删除股票：设置手动编辑标志时出错:', flagError);
        }
        
        this.render();
        this.showToast(`股票 ${code} 已删除`, 'success');
    }
    
    // 切换股票选中状态
    toggleStockSelection(groupName, code) {
        const key = `${groupName}:${code}`;
        if (this.state.selectedStocks.has(key)) {
            this.state.selectedStocks.delete(key);
        } else {
            this.state.selectedStocks.add(key);
        }
        this.render();
    }
    
    // 切换分组全选状态
    toggleGroupSelection(groupName, checked) {
        const stocks = this.state.watchlists.get(groupName);
        if (!stocks) return;
        
        stocks.forEach((name, code) => {
            const key = `${groupName}:${code}`;
            if (checked) {
                this.state.selectedStocks.add(key);
            } else {
                this.state.selectedStocks.delete(key);
            }
        });
        
        this.render();
    }
    
    // 显示分组排序对话框
    showSortGroupsDialog() {
        // 创建对话框
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'sortGroupsDialog';
        modal.setAttribute('tabindex', '-1');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">排序分组</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="list-group" id="sortableGroups">
                            ${this.state.groupOrder.map((groupName, index) => `
                                <div class="list-group-item d-flex align-items-center" data-group="${groupName}">
                                    <i class="bi bi-grip-vertical me-2"></i>
                                    <span>${groupName}</span>
                                    <span class="badge bg-secondary ms-2">
                                        ${this.state.watchlists.get(groupName)?.size || 0}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="saveSortBtn">保存排序</button>
                    </div>
                </div>
            </div>
        `;
        
        // 添加到文档
        document.body.appendChild(modal);
        
        // 初始化排序
        new Sortable(document.getElementById('sortableGroups'), {
            animation: 150,
            handle: '.bi-grip-vertical',
            onEnd: (evt) => {
                // 更新顺序（但不保存，等用户点击保存按钮）
                const newOrder = Array.from(evt.to.children).map(item => item.dataset.group);
                this.tempGroupOrder = newOrder;
            }
        });
        
        // 显示对话框
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // 处理保存按钮点击
        document.getElementById('saveSortBtn').onclick = () => {
            if (this.tempGroupOrder) {
                this.state.groupOrder = this.tempGroupOrder;
                this.state.hasUnsavedChanges = true;
                this.render();
                this.showToast('分组顺序已更新', 'success');
            }
            modalInstance.hide();
        };
        
        // 对话框隐藏后清理
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
            delete this.tempGroupOrder;
        });
    }
    
    // 保存更改
    async saveChanges() {
        const saveBtn = document.getElementById('saveAllBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 保存中...';
        saveBtn.disabled = true;
        
        try {
            // 按照分组顺序构建数据
            const watchlists = {};
            this.state.groupOrder.forEach(groupName => {
                const stocks = this.state.watchlists.get(groupName);
                if (stocks) {
                    // 使用从Map中获取的顺序来构建对象，确保顺序保留
                    const orderedStocks = {};
                    Array.from(stocks.entries()).forEach(([code, name]) => {
                        orderedStocks[code] = name;
                    });
                    
                    watchlists[groupName] = orderedStocks;
                    
                    // 调试日志
                    if (groupName === '指数与ETF') {
                        console.log("保存前'指数与ETF'分组的股票顺序(前5个):", 
                            Array.from(stocks.keys()).slice(0, 5));
                    }
                }
            });
            
            // 添加任何遗漏的分组
            this.state.watchlists.forEach((stocks, groupName) => {
                if (!(groupName in watchlists)) {
                    const orderedStocks = {};
                    Array.from(stocks.entries()).forEach(([code, name]) => {
                        orderedStocks[code] = name;
                    });
                    
                    watchlists[groupName] = orderedStocks;
                    this.state.groupOrder.push(groupName);
                }
            });
            
            // 设置手动编辑标志
            try {
                // 设置手动编辑标志为true
                const editFlagResponse = await fetch('/api/set-watchlist-edit-flag', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ edited: true })
                });
                
                const editFlagData = await editFlagResponse.json();
                if (editFlagData.success) {
                    console.log('成功设置手动编辑标志');
                } else {
                    console.warn('设置手动编辑标志失败:', editFlagData.error);
                }
            } catch (flagError) {
                console.error('设置手动编辑标志时出错:', flagError);
                // 继续保存过程，不阻止
            }
            
            const response = await fetch('/api/watchlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    watchlists,
                    groups_order: this.state.groupOrder
                })
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || '保存失败');
            
            this.state.hasUnsavedChanges = false;
            this.showToast('保存成功', 'success');
            
            // 触发自定义事件，通知主页面刷新数据
            const event = new CustomEvent('watchlistUpdated', { 
                detail: { 
                    watchlists,
                    groups_order: this.state.groupOrder
                }
            });
            document.dispatchEvent(event);
            
            // 在localStorage中标记编辑器已保存
            localStorage.setItem('watchlistEditorSaved', 'true');
            localStorage.setItem('watchlistEditorSavedTime', new Date().getTime());
        } catch (error) {
            console.error('保存失败:', error);
            this.showToast(error.message || '保存失败，请重试', 'error');
        } finally {
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }
    }
    
    // 显示Toast通知
    showToast(message, type = 'info') {
        const container = document.querySelector('.toast-container');
        if (!container) {
            console.error('找不到Toast容器');
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast align-items-center border-0 ${type === 'error' ? 'bg-danger' : type === 'warning' ? 'bg-warning' : type === 'success' ? 'bg-success' : 'bg-info'}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body text-white">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, {
            animation: true,
            autohide: true,
            delay: 3000
        });

        bsToast.show();

        // 监听隐藏事件，移除元素
        toast.addEventListener('hidden.bs.toast', () => {
            container.removeChild(toast);
        });
    }

    // 切换所有分组的展开/折叠状态
    toggleAllGroups(expand = true) {
        const groups = document.querySelectorAll('.watchlist-group');
        groups.forEach(group => {
            const body = group.querySelector('.card-body');
            if (expand) {
                body.style.display = 'block';
                group.querySelector('.group-header i.bi-chevron-up, .group-header i.bi-chevron-down')
                    ?.classList.replace('bi-chevron-up', 'bi-chevron-down');
            } else {
                body.style.display = 'none';
                group.querySelector('.group-header i.bi-chevron-up, .group-header i.bi-chevron-down')
                    ?.classList.replace('bi-chevron-down', 'bi-chevron-up');
            }
        });
    }

    // 切换单个分组的展开/折叠状态
    toggleGroup(groupElement) {
        const body = groupElement.querySelector('.card-body');
        const icon = groupElement.querySelector('.group-header i.bi-chevron-up, .group-header i.bi-chevron-down');
        
        if (body.style.display === 'none') {
            body.style.display = 'block';
            icon?.classList.replace('bi-chevron-up', 'bi-chevron-down');
        } else {
            body.style.display = 'none';
            icon?.classList.replace('bi-chevron-down', 'bi-chevron-up');
        }
    }

    // 折叠所有分组
    collapseAllGroups() {
        const groups = document.querySelectorAll('.watchlist-group');
        groups.forEach(group => {
            const cardBody = group.querySelector('.card-body');
            const icon = group.querySelector('.group-header i.bi-chevron-up, .group-header i.bi-chevron-down');
            
            if (cardBody && icon) {
                cardBody.style.display = 'none';
                icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
            }
        });
    }
    
    // 展开所有分组
    expandAllGroups() {
        const groups = document.querySelectorAll('.watchlist-group');
        groups.forEach(group => {
            const cardBody = group.querySelector('.card-body');
            const icon = group.querySelector('.group-header i.bi-chevron-up, .group-header i.bi-chevron-down');
            
            if (cardBody && icon) {
                cardBody.style.display = 'block';
                icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
            }
        });
    }
}

// 初始化编辑器
document.addEventListener('DOMContentLoaded', () => {
    window.watchlistEditor = new WatchlistEditor();
}); 