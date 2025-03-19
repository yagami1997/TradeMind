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
        this.loadData();
        this.initDragAndDrop();
        this.bindEvents();
    }
    
    // 加载数据
    async loadData() {
        try {
            const response = await fetch('/api/watchlists');
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || '加载数据失败');
            
            // 清空现有数据
            this.state.watchlists.clear();
            
            // 使用服务器返回的分组顺序
            this.state.groupOrder = data.groups_order || [];
            
            // 按照服务器返回的顺序初始化数据
            this.state.groupOrder.forEach(groupName => {
                const stocks = data.watchlists[groupName];
                if (stocks) {
                    const stocksMap = new Map();
                    // 使用 Object.entries 保持股票顺序
                    Object.entries(stocks).forEach(([code, name]) => {
                        stocksMap.set(code, name);
                    });
                    this.state.watchlists.set(groupName, stocksMap);
                }
            });
            
            // 添加任何遗漏的分组
            Object.keys(data.watchlists).forEach(groupName => {
                if (!this.state.watchlists.has(groupName)) {
                    const stocks = data.watchlists[groupName];
                    const stocksMap = new Map();
                    Object.entries(stocks).forEach(([code, name]) => {
                        stocksMap.set(code, name);
                    });
                    this.state.watchlists.set(groupName, stocksMap);
                    this.state.groupOrder.push(groupName);
                }
            });
            
            this.render();
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
            onEnd: (evt) => {
                const newOrder = Array.from(document.querySelectorAll('.watchlist-group'))
                    .map(group => group.dataset.group);
                this.state.groupOrder = newOrder;
                this.state.hasUnsavedChanges = true;
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
                    onEnd: (evt) => {
                        const fromGroup = evt.from.closest('.watchlist-group').dataset.group;
                        const toGroup = evt.to.closest('.watchlist-group').dataset.group;
                        
                        if (fromGroup !== toGroup) {
                            // 处理跨分组移动
                            this.handleStockMove(evt.item.dataset.symbol, fromGroup, toGroup);
                        } else {
                            // 更新同分组内顺序
                            this.updateStockOrder(fromGroup);
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
        
        // 导入股票
        document.getElementById('importStocksBtn').addEventListener('click', () => this.showImportDialog());
        
        // 分组排序
        document.getElementById('sortGroupsBtn').addEventListener('click', () => this.showSortGroupsDialog());
        
        // 折叠全部
        document.getElementById('collapseAllBtn').addEventListener('click', () => this.toggleAllGroups(false));
        
        // 展开全部
        document.getElementById('expandAllBtn').addEventListener('click', () => this.toggleAllGroups(true));
        
        // 保存更改
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
                                <button type="button" class="btn btn-sm btn-outline-danger delete-group-btn">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-hover table-stocks mb-0">
                            <thead>
                                <tr>
                                    <th width="40px">
                                        <div class="form-check">
                                            <input type="checkbox" class="form-check-input select-all-stocks" data-group="${groupName}">
                                        </div>
                                    </th>
                                    <th width="40px"></th>
                                    <th>代码</th>
                                    <th>名称</th>
                                    <th width="100px">操作</th>
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
        stocks.forEach((name, code) => {
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
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-secondary edit-stock-btn">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="btn btn-outline-danger delete-stock-btn">
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
    
    // 处理股票移动
    handleStockMove(code, fromGroup, toGroup) {
        const fromStocks = this.state.watchlists.get(fromGroup);
        const toStocks = this.state.watchlists.get(toGroup);
        if (!fromStocks || !toStocks || !fromStocks.has(code)) return;
        
        const name = fromStocks.get(code);
        fromStocks.delete(code);
        toStocks.set(code, name);
        
        // 更新选中状态
        this.state.selectedStocks.delete(`${fromGroup}:${code}`);
        
        this.state.hasUnsavedChanges = true;
    }
    
    // 更新股票顺序
    updateStockOrder(groupName) {
        const stocks = this.state.watchlists.get(groupName);
        if (!stocks) return;
        
        const newOrder = new Map();
        const rows = document.querySelectorAll(`.watchlist-group[data-group="${groupName}"] .stock-row`);
        rows.forEach(row => {
            const code = row.dataset.symbol;
            if (stocks.has(code)) {
                newOrder.set(code, stocks.get(code));
            }
        });
        
        this.state.watchlists.set(groupName, newOrder);
        this.state.hasUnsavedChanges = true;
    }
    
    // 显示导入对话框
    showImportDialog() {
        // 获取对话框元素
        const modal = document.getElementById('importDialog');
        if (!modal) {
            console.error('找不到导入对话框元素');
            return;
        }

        // 更新分组下拉列表
        const targetGroup = modal.querySelector('#targetGroup');
        targetGroup.innerHTML = '<option value="">创建新分组</option>';
        this.state.groupOrder.forEach(groupName => {
            targetGroup.innerHTML += `<option value="${groupName}">${groupName}</option>`;
        });

        // 监听分组选择变化
        targetGroup.onchange = () => {
            const newGroupContainer = modal.querySelector('#newGroupNameContainer');
            newGroupContainer.style.display = targetGroup.value === '' ? 'block' : 'none';
        };

        // 处理导入按钮点击
        const startImportBtn = modal.querySelector('#startImportBtn');
        const stockInput = modal.querySelector('#stockInput');
        
        startImportBtn.onclick = async () => {
            const codes = stockInput.value.trim().split(/[\n,，\s]+/).filter(code => code);
            if (!codes.length) {
                this.showToast('请输入股票代码', 'warning');
                return;
            }

            const selectedGroup = targetGroup.value;
            const newGroupName = modal.querySelector('#newGroupName')?.value?.trim();

            if (!selectedGroup && !newGroupName) {
                this.showToast('请选择分组或输入新分组名称', 'warning');
                return;
            }

            const groupName = selectedGroup || newGroupName;

            // 如果是新分组，先创建
            if (!selectedGroup) {
                if (this.state.watchlists.has(groupName)) {
                    this.showToast(`分组 "${groupName}" 已存在`, 'warning');
                    return;
                }
                this.state.watchlists.set(groupName, new Map());
                this.state.groupOrder.push(groupName);
            }

            // 获取目标分组的股票列表
            const stocks = this.state.watchlists.get(groupName);

            // 导入股票
            let addedCount = 0;
            let duplicateCount = 0;

            for (const code of codes) {
                if (stocks.has(code)) {
                    duplicateCount++;
                    continue;
                }
                stocks.set(code, '');  // 暂时使用空名称，后续可以添加验证和获取名称的功能
                addedCount++;
            }

            // 关闭对话框
            bootstrap.Modal.getInstance(modal).hide();

            // 清空输入
            stockInput.value = '';
            targetGroup.value = '';
            if (newGroupName) {
                modal.querySelector('#newGroupName').value = '';
            }

            // 标记有未保存的更改
            this.state.hasUnsavedChanges = true;

            // 重新渲染
            this.render();

            // 显示结果
            this.showToast(
                `成功导入 ${addedCount} 个股票${duplicateCount ? `，${duplicateCount} 个重复已跳过` : ''}`,
                'success'
            );
        };

        // 显示对话框
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
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
                    // 使用 Object.fromEntries 保持股票顺序
                    watchlists[groupName] = Object.fromEntries(Array.from(stocks.entries()));
                }
            });
            
            // 添加任何遗漏的分组
            this.state.watchlists.forEach((stocks, groupName) => {
                if (!(groupName in watchlists)) {
                    watchlists[groupName] = Object.fromEntries(Array.from(stocks.entries()));
                    this.state.groupOrder.push(groupName);
                }
            });
            
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
}

// 初始化编辑器
document.addEventListener('DOMContentLoaded', () => {
    window.watchlistEditor = new WatchlistEditor();
}); 