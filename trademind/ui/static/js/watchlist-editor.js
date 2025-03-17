/**
 * TradeMind Lite - 股票列表编辑器
 * 
 * 本文件包含股票列表编辑器的前端交互逻辑
 */

// 全局变量
let watchlistData = null;
let selectedStocks = [];
let hasUnsavedChanges = false;
let watchlistContainer = null; // 全局声明watchlistContainer变量
let groupOrder = []; // 保存分组顺序
let hasBeenManuallyEdited = false; // 标记是否已手动编辑过自选股列表

document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化自选股编辑器');
    
    // 初始化选中股票数组
    selectedStocks = [];
    
    // 获取DOM元素
    watchlistContainer = document.getElementById('watchlistContainer'); // 使用全局变量
    const addGroupBtn = document.getElementById('addGroupBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const importStocksBtn = document.getElementById('importStocksBtn');
    const sortGroupsBtn = document.getElementById('sortGroupsBtn');
    const closeEditorBtn = document.getElementById('closeEditorBtn');
    
    // 添加滚动监听，确保多选操作栏在滚动时可见
    window.addEventListener('scroll', function() {
        const actionsBar = document.querySelector('.multi-select-actions');
        if (actionsBar) {
            // 获取当前可见区域的高度
            const viewportHeight = window.innerHeight;
            // 获取操作栏的位置信息
            const barRect = actionsBar.getBoundingClientRect();
            
            // 如果操作栏不在可见区域内，调整其位置
            if (barRect.top < 0 || barRect.bottom > viewportHeight) {
                actionsBar.style.position = 'fixed';
                actionsBar.style.top = '10px';
                actionsBar.style.left = '50%';
                actionsBar.style.transform = 'translateX(-50%)';
                actionsBar.style.width = 'calc(100% - 40px)';
                actionsBar.style.maxWidth = '1200px';
                actionsBar.style.zIndex = '1000';
            } else {
                // 恢复原始样式
                actionsBar.style.position = 'sticky';
                actionsBar.style.top = '10px';
                actionsBar.style.left = '';
                actionsBar.style.transform = '';
                actionsBar.style.width = '';
                actionsBar.style.maxWidth = '';
                actionsBar.style.zIndex = '100';
            }
        }
    });
    
    // 加载股票列表数据
    function loadWatchlistData() {
        // 显示加载中状态
        watchlistContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载股票列表...</p>
            </div>
        `;
        
        // 尝试从页面中获取分组顺序
        const groupsOrderInput = document.getElementById('groupsOrderInput');
        if (groupsOrderInput && groupsOrderInput.value) {
            try {
                const initialGroupOrder = JSON.parse(groupsOrderInput.value);
                if (Array.isArray(initialGroupOrder) && initialGroupOrder.length > 0) {
                    groupOrder = initialGroupOrder;
                    console.log('使用页面中的初始分组顺序:', groupOrder);
                }
            } catch (error) {
                console.error('解析页面中的分组顺序出错:', error);
            }
        }
        
        fetch('/api/watchlists')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`服务器返回错误: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('API返回数据:', data);
                
                // 检查数据格式
                if (data.success && data.watchlists) {
                    // 直接使用API返回的watchlists数据
                    watchlistData = data.watchlists;
                    
                    // 获取手动编辑标志
                    if (data.hasBeenManuallyEdited !== undefined) {
                        hasBeenManuallyEdited = data.hasBeenManuallyEdited;
                        console.log('自选股列表手动编辑状态:', hasBeenManuallyEdited);
                    }
                    
                    // 如果之前没有从页面获取到分组顺序，则使用API返回的
                    if (!groupOrder || groupOrder.length === 0) {
                        // 使用API返回的分组顺序
                        if (data.groups_order && Array.isArray(data.groups_order)) {
                            groupOrder = data.groups_order;
                            console.log('使用API返回的分组顺序:', groupOrder);
                        } else {
                            // 如果API没有返回分组顺序，使用Object.keys()
                            groupOrder = Object.keys(watchlistData);
                            console.log('API没有返回分组顺序，使用Object.keys():', groupOrder);
                        }
                    }
                    
                    // 添加调试信息
                    console.log('最终使用的分组顺序:');
                    groupOrder.forEach((group, index) => {
                        console.log(`${index + 1}. ${group}`);
                    });
                } else {
                    // 如果没有返回预期的数据结构，使用原始数据
                    watchlistData = data;
                    
                    // 如果之前没有从页面获取到分组顺序，则使用Object.keys()
                    if (!groupOrder || groupOrder.length === 0) {
                        // 保存分组顺序
                        groupOrder = Object.keys(watchlistData);
                        console.log('使用原始数据，分组顺序:', groupOrder);
                    }
                    
                    // 添加调试信息
                    console.log('最终使用的分组顺序:');
                    groupOrder.forEach((group, index) => {
                        console.log(`${index + 1}. ${group}`);
                    });
                }
                
                // 检查数据是否为空
                if (!watchlistData || Object.keys(watchlistData).length === 0) {
                    watchlistContainer.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle-fill"></i> 
                            没有找到股票列表数据。请添加一个分组开始使用。
                        </div>
                    `;
                    watchlistData = {};
                    groupOrder = [];
                    return;
                }
                
                renderWatchlist();
            })
            .catch(error => {
                console.error('加载股票列表失败:', error);
                watchlistContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle-fill"></i> 
                        加载股票列表失败: ${error.message}
                        <hr>
                        <p>请检查服务器连接或刷新页面重试。</p>
                    </div>
                `;
                
                // 如果加载失败，初始化一个空的数据结构
                watchlistData = { '默认分组': {} };
                groupOrder = ['默认分组'];
            });
    }
    
    // 渲染股票列表
    function renderWatchlist() {
        if (!watchlistData) return;
        
        console.log('渲染数据:', watchlistData);
        console.log('使用分组顺序:', groupOrder);
        
        // 检查数据格式
        let hasInvalidFormat = false;
        Object.keys(watchlistData).forEach(groupName => {
            const groupStocks = watchlistData[groupName];
            if (typeof groupStocks !== 'object' || Array.isArray(groupStocks)) {
                console.error(`分组 "${groupName}" 的数据格式不正确:`, groupStocks);
                hasInvalidFormat = true;
                // 修复格式
                watchlistData[groupName] = {};
            }
        });
        
        if (hasInvalidFormat) {
            showToast('检测到数据格式不正确，已自动修复', 'warning');
        }
        
        watchlistContainer.innerHTML = '';
        
        // 使用保存的分组顺序
        groupOrder.forEach(groupName => {
            // 确保分组存在
            if (!watchlistData[groupName]) return;
            
            const groupStocks = watchlistData[groupName];
            
            // 创建分组容器
            const groupDiv = document.createElement('div');
            groupDiv.className = 'watchlist-group mb-4';
            
            // 创建分组标题
            const headerDiv = document.createElement('div');
            headerDiv.className = 'group-header';
            
            const groupTitle = document.createElement('h5');
            groupTitle.textContent = groupName;
            
            const editGroupNameBtn = document.createElement('button');
            editGroupNameBtn.className = 'btn btn-sm btn-outline-primary';
            editGroupNameBtn.innerHTML = '<i class="bi bi-pencil"></i> 编辑分组名';
            editGroupNameBtn.onclick = () => editGroupName(groupName);
            
            headerDiv.appendChild(groupTitle);
            headerDiv.appendChild(editGroupNameBtn);
            groupDiv.appendChild(headerDiv);
            
            // 创建股票列表
            const stockListDiv = document.createElement('div');
            stockListDiv.className = 'stock-list';
            
            // 添加股票行
            Object.keys(groupStocks).forEach(stockCode => {
                const stockName = groupStocks[stockCode];
                
                const stockRow = document.createElement('div');
                stockRow.className = 'stock-row';
                stockRow.dataset.group = groupName;
                stockRow.dataset.code = stockCode;
                
                // 添加复选框
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'stock-checkbox';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.onclick = (e) => {
                    e.stopPropagation();
                    toggleStockSelection(e, groupName, stockCode);
                };
                
                checkboxDiv.appendChild(checkbox);
                stockRow.appendChild(checkboxDiv);
                
                // 添加股票代码
                const codeDiv = document.createElement('div');
                codeDiv.className = 'stock-code';
                codeDiv.textContent = stockCode;
                stockRow.appendChild(codeDiv);
                
                // 添加股票名称
                const nameDiv = document.createElement('div');
                nameDiv.className = 'stock-name';
                nameDiv.textContent = stockName || '未知';
                stockRow.appendChild(nameDiv);
                
                // 添加操作按钮
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'actions';
                
                // 编辑按钮
                const editBtn = document.createElement('button');
                editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
                editBtn.title = '编辑';
                editBtn.onclick = (e) => {
                    e.stopPropagation();
                    editStock(groupName, stockCode, stockName);
                };
                
                // 移动按钮
                const moveBtn = document.createElement('button');
                moveBtn.innerHTML = '<i class="bi bi-arrows-move"></i>';
                moveBtn.title = '移动到其他分组';
                moveBtn.onclick = (e) => {
                    e.stopPropagation();
                    moveStock(groupName, stockCode);
                };
                
                // 删除按钮
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
                deleteBtn.title = '删除';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteStock(groupName, stockCode);
                };
                
                actionsDiv.appendChild(editBtn);
                actionsDiv.appendChild(moveBtn);
                actionsDiv.appendChild(deleteBtn);
                stockRow.appendChild(actionsDiv);
                
                // 点击行选择
                stockRow.onclick = (e) => {
                    toggleStockSelection(e, groupName, stockCode);
                };
                
                stockListDiv.appendChild(stockRow);
            });
            
            // 添加"添加股票"按钮
            const addStockRow = document.createElement('div');
            addStockRow.className = 'stock-row add-stock-row';
            
            const addStockBtn = document.createElement('button');
            addStockBtn.className = 'btn btn-sm btn-outline-primary w-100';
            addStockBtn.innerHTML = '<i class="bi bi-plus-circle"></i> 添加股票';
            addStockBtn.onclick = () => addStock(groupName);
            
            addStockRow.appendChild(document.createElement('div')); // 空的复选框位置
            addStockRow.appendChild(document.createElement('div')); // 空的代码位置
            addStockRow.appendChild(addStockBtn);
            addStockRow.appendChild(document.createElement('div')); // 空的操作位置
            
            stockListDiv.appendChild(addStockRow);
            groupDiv.appendChild(stockListDiv);
            
            watchlistContainer.appendChild(groupDiv);
        });
        
        // 添加多选操作栏
        renderMultiSelectActions();
    }
    
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
    
    // 更新选中状态UI
    function updateSelectionUI() {
        document.querySelectorAll('.stock-row').forEach(row => {
            const group = row.dataset.group;
            const code = row.dataset.code;
            
            if (!group || !code) return;
            
            const checkbox = row.querySelector('input[type="checkbox"]');
            if (!checkbox) return;
            
            const isSelected = selectedStocks.some(stock => 
                stock.group === group && stock.code === code);
            
            checkbox.checked = isSelected;
            row.classList.toggle('selected', isSelected);
        });
    }
    
    // 切换股票选中状态
    function toggleStockSelection(event, groupName, stockCode) {
        event.stopPropagation();
        
        // 查找股票在选中列表中的索引
        const index = selectedStocks.findIndex(s => s.group === groupName && s.code === stockCode);
        
        // 获取当前行元素
        const stockRow = document.querySelector(`.stock-row[data-group="${groupName}"][data-code="${stockCode}"]`);
        
        if (index === -1) {
            // 添加到选中列表
            selectedStocks.push({ group: groupName, code: stockCode });
            
            // 添加视觉反馈
            if (stockRow) {
                stockRow.classList.add('selected-stock');
                // 添加选中动画
                stockRow.style.animation = 'pulse 0.5s';
                setTimeout(() => {
                    stockRow.style.animation = '';
                }, 500);
            }
        } else {
            // 从选中列表中移除
            selectedStocks.splice(index, 1);
            
            // 移除视觉反馈
            if (stockRow) {
                stockRow.classList.remove('selected-stock');
                // 添加取消选中动画
                stockRow.style.animation = 'fadeOut 0.3s';
                setTimeout(() => {
                    stockRow.style.animation = '';
                }, 300);
            }
        }
        
        // 更新多选操作栏
        renderMultiSelectActions();
    }
    
    // 添加分组
    function addGroup() {
        const groupName = prompt('请输入新分组名称:');
        if (!groupName) return;
        
        if (watchlistData[groupName]) {
            showToast(`分组 "${groupName}" 已存在`, 'warning');
            return;
        }
        
        watchlistData[groupName] = {};
        hasBeenManuallyEdited = true; // 标记已手动编辑
        hasUnsavedChanges = true; // 标记有未保存的更改
        renderWatchlist();
        showToast(`分组 "${groupName}" 已添加`, 'success');
    }
    
    // 编辑分组名
    function editGroupName(oldName) {
        const newName = prompt('请输入新的分组名称:', oldName);
        if (!newName || newName === oldName) return;
        
        if (watchlistData[newName]) {
            showToast(`分组 "${newName}" 已存在`, 'warning');
            return;
        }
        
        watchlistData[newName] = watchlistData[oldName];
        delete watchlistData[oldName];
        hasBeenManuallyEdited = true; // 标记已手动编辑
        hasUnsavedChanges = true; // 标记有未保存的更改
        renderWatchlist();
        showToast(`分组已重命名为 "${newName}"`, 'success');
    }
    
    // 添加股票
    function addStock(group) {
        const code = prompt('请输入股票代码:');
        if (!code) return;
        
        const name = prompt('请输入股票名称 (可选):');
        
        // 检查是否已存在
        if (watchlistData[group][code]) {
            showToast(`股票 ${code} 已存在于该分组`, 'warning');
            return;
        }
        
        watchlistData[group][code] = name || '';
        hasBeenManuallyEdited = true; // 标记已手动编辑
        hasUnsavedChanges = true; // 标记有未保存的更改
        renderWatchlist();
        showToast(`股票 ${code} 已添加到 "${group}"`, 'success');
    }
    
    // 编辑股票
    function editStock(group, code, name) {
        const newCode = prompt('请输入股票代码:', code);
        if (!newCode) return;
        
        const newName = prompt('请输入股票名称:', name || '');
        
        // 如果代码改变，检查是否已存在
        if (newCode !== code && watchlistData[group][newCode]) {
            showToast(`股票 ${newCode} 已存在于该分组`, 'warning');
            return;
        }
        
        // 如果代码改变，需要删除旧的并添加新的
        if (newCode !== code) {
            delete watchlistData[group][code];
        }
        
        watchlistData[group][newCode] = newName;
        hasBeenManuallyEdited = true; // 标记已手动编辑
        hasUnsavedChanges = true; // 标记有未保存的更改
        renderWatchlist();
        showToast(`股票 ${code} 已更新`, 'success');
    }
    
    // 移动股票
    function moveStock(fromGroup, code) {
        const groups = Object.keys(watchlistData).filter(g => g !== fromGroup);
        if (groups.length === 0) {
            showToast('没有其他分组可移动', 'warning');
            return;
        }
        
        let groupOptions = '';
        groups.forEach(group => {
            groupOptions += `<option value="${group}">${group}</option>`;
        });
        
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">移动股票</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>请选择要将股票 ${code} 移动到的分组:</p>
                        <select class="form-select" id="targetGroupSelect">
                            ${groupOptions}
                        </select>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="confirmMoveBtn">移动</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        document.getElementById('confirmMoveBtn').onclick = function() {
            const targetGroup = document.getElementById('targetGroupSelect').value;
            
            // 检查目标分组是否已存在该股票
            if (watchlistData[targetGroup][code]) {
                showToast(`股票 ${code} 已存在于目标分组`, 'warning');
                modalInstance.hide();
                modal.remove();
                return;
            }
            
            // 移动股票
            const stockName = watchlistData[fromGroup][code];
            watchlistData[targetGroup][code] = stockName;
            delete watchlistData[fromGroup][code];
            
            hasBeenManuallyEdited = true; // 标记已手动编辑
            hasUnsavedChanges = true; // 标记有未保存的更改
            
            modalInstance.hide();
            modal.remove();
            
            renderWatchlist();
            showToast(`股票 ${code} 已移动到 "${targetGroup}"`, 'success');
            
            // 延迟清除选择，让用户能看到移动效果
            setTimeout(() => {
                clearSelection();
            }, 1500);
        };
        
        modal.addEventListener('hidden.bs.modal', function() {
            modal.remove();
        });
    }
    
    // 批量移动股票
    function moveSelectedStocks() {
        if (selectedStocks.length === 0) return;
        
        // 获取所有可能的目标分组
        const allGroups = Object.keys(watchlistData);
        
        let groupOptions = '';
        allGroups.forEach(group => {
            groupOptions += `<option value="${group}">${group}</option>`;
        });
        
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">批量移动股票</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>请选择要将 ${selectedStocks.length} 个股票移动到的分组:</p>
                        <select class="form-select" id="targetGroupSelect">
                            ${groupOptions}
                        </select>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="confirmMoveBtn">移动</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        document.getElementById('confirmMoveBtn').onclick = function() {
            const targetGroup = document.getElementById('targetGroupSelect').value;
            
            // 移动所有选中的股票
            selectedStocks.forEach(stock => {
                // 跳过已经在目标分组的股票
                if (stock.group === targetGroup) return;
                
                // 检查目标分组是否已存在该股票
                if (!watchlistData[targetGroup][stock.code]) {
                    // 移动股票
                    const stockName = watchlistData[stock.group][stock.code];
                    watchlistData[targetGroup][stock.code] = stockName;
                    delete watchlistData[stock.group][stock.code];
                }
            });
            
            hasBeenManuallyEdited = true; // 标记已手动编辑
            hasUnsavedChanges = true; // 标记有未保存的更改
            
            modalInstance.hide();
            modal.remove();
            
            renderWatchlist();
            showToast(`已将选中股票移动到 "${targetGroup}"`, 'success');
            
            // 延迟清除选择，让用户能看到移动效果
            setTimeout(() => {
                clearSelection();
            }, 1500);
        };
        
        modal.addEventListener('hidden.bs.modal', function() {
            modal.remove();
        });
    }
    
    // 删除股票
    function deleteStock(group, code) {
        if (!confirm(`确定要删除股票 ${code} 吗?`)) return;
        
        delete watchlistData[group][code];
        hasBeenManuallyEdited = true; // 标记已手动编辑
        hasUnsavedChanges = true; // 标记有未保存的更改
        renderWatchlist();
        showToast(`股票 ${code} 已删除`, 'success');
    }
    
    // 批量删除股票
    function deleteSelectedStocks() {
        if (selectedStocks.length === 0) return;
        
        if (!confirm(`确定要删除选中的 ${selectedStocks.length} 个股票吗?`)) return;
        
        selectedStocks.forEach(stock => {
            delete watchlistData[stock.group][stock.code];
        });
        
        hasBeenManuallyEdited = true; // 标记已手动编辑
        hasUnsavedChanges = true; // 标记有未保存的更改
        renderWatchlist();
        showToast(`已删除 ${selectedStocks.length} 个股票`, 'success');
        
        // 延迟清除选择，让用户能看到删除效果
        setTimeout(() => {
            clearSelection();
        }, 1500);
    }
    
    // 保存所有修改
    function saveAllChanges() {
        // 显示保存中状态
        const saveBtn = document.getElementById('saveAllBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 保存中...';
        saveBtn.disabled = true;
        
        // 准备要发送的数据，包括手动编辑标志和分组顺序
        const dataToSend = {
            watchlists: watchlistData,
            hasBeenManuallyEdited: hasBeenManuallyEdited,
            groups_order: groupOrder
        };
        
        fetch('/api/watchlists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataToSend)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`服务器返回错误: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showToast('股票列表已保存', 'success');
                hasUnsavedChanges = false;
                
                // 通知主界面刷新下拉框
                try {
                    if (window.opener && !window.opener.closed) {
                        console.log('尝试通知主界面刷新下拉框');
                        if (typeof window.opener.refreshWatchlistDropdown === 'function') {
                            // 如果主界面有刷新函数，则调用它
                            // 创建一个包含分组顺序的对象传递给主页面
                            const dataWithOrder = {
                                watchlists: watchlistData,
                                groups_order: groupOrder
                            };
                            window.opener.refreshWatchlistDropdown(dataWithOrder);
                            console.log('已通知主界面刷新下拉框，并传递分组顺序:', groupOrder);
                            
                            // 确保主页面保存分组顺序
                            if (typeof window.opener.saveGroupsOrder === 'function') {
                                window.opener.saveGroupsOrder(groupOrder);
                                console.log('已通知主界面保存分组顺序');
                            }
                        }
                    }
                } catch (error) {
                    console.error('通知主界面刷新下拉框时出错:', error);
                }
            } else {
                throw new Error(data.error || '保存失败');
            }
        })
        .catch(error => {
            console.error('保存失败:', error);
            showToast('保存失败: ' + error.message, 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        });
    }
    
    // 显示提示消息
    function showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || (() => {
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
            return container;
        })();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    // 导入股票
    function importStocks() {
        // 尝试获取主页面的引用
        try {
            if (window.opener && !window.opener.closed) {
                // 如果有父窗口，尝试在父窗口打开导入模态框
                window.opener.location.href = '/?action=import';
                window.close();
            } else {
                // 如果没有父窗口，直接跳转到主页并打开导入模态框
                window.location.href = '/?action=import';
            }
        } catch (e) {
            // 如果出错，直接跳转到主页并打开导入模态框
            window.location.href = '/?action=import';
        }
    }
    
    // 分组排序功能
    function sortGroups() {
        if (!watchlistData || Object.keys(watchlistData).length <= 1) {
            showToast('至少需要两个分组才能排序', 'warning');
            return;
        }
        
        console.log('当前分组顺序:', groupOrder);
        
        // 创建排序模态框
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'sortGroupsModal'; // 修改为与CSS选择器一致的ID
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">分组排序</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-3">拖动分组调整顺序，排序将影响分组在下拉菜单中的显示顺序。</p>
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle-fill"></i> 提示：按住分组右侧的拖动手柄 <i class="bi bi-grip-vertical"></i> 进行拖动
                        </div>
                        <ul id="sortableGroupList" class="list-group sortable-list">
                            ${groupOrder.map((groupName, index) => `
                                <li class="list-group-item group-item d-flex justify-content-between align-items-center" data-group-name="${groupName}">
                                    <div class="group-name">${groupName}</div>
                                    <div class="drag-handle"><i class="bi bi-grip-vertical"></i></div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="saveGroupOrderBtn">保存排序</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // 初始化拖拽排序
        const sortableList = document.getElementById('sortableGroupList');
        let draggedItem = null;
        let draggedIndex = -1;
        let placeholder = null;
        let lastY = 0;
        let animationFrame = null;
        
        // 创建占位元素
        function createPlaceholder(height) {
            const el = document.createElement('li');
            el.className = 'list-group-item placeholder';
            el.style.height = `${height}px`;
            return el;
        }
        
        // 平滑滚动函数
        function smoothScroll(target, duration) {
            const start = window.pageYOffset;
            const distance = target - start;
            let startTime = null;
            
            function animation(currentTime) {
                if (startTime === null) startTime = currentTime;
                const timeElapsed = currentTime - startTime;
                const progress = Math.min(timeElapsed / duration, 1);
                const ease = progress => 0.5 - 0.5 * Math.cos(progress * Math.PI);
                window.scrollTo(0, start + distance * ease(progress));
                
                if (timeElapsed < duration) {
                    requestAnimationFrame(animation);
                }
            }
            
            requestAnimationFrame(animation);
        }
        
        // 为每个列表项添加拖拽事件
        const listItems = sortableList.querySelectorAll('li');
        listItems.forEach((item, index) => {
            // 拖动手柄添加事件
            const dragHandle = item.querySelector('.drag-handle');
            
            dragHandle.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // 记录初始索引
                draggedItem = item;
                draggedIndex = Array.from(sortableList.children).indexOf(item);
                lastY = e.clientY;
                
                // 获取元素尺寸
                const rect = item.getBoundingClientRect();
                const itemHeight = rect.height;
                
                // 创建占位元素
                placeholder = createPlaceholder(itemHeight);
                
                // 设置拖动样式
                item.classList.add('dragging');
                item.style.width = `${rect.width}px`;
                item.style.height = `${itemHeight}px`;
                item.style.position = 'absolute';
                item.style.zIndex = '1000';
                
                // 计算更靠近左侧的位置
                const containerRect = sortableList.getBoundingClientRect();
                const leftPosition = Math.max(containerRect.left + 20, rect.left - 50); // 向左偏移50px，但不超出容器
                
                item.style.left = `${leftPosition}px`;
                item.style.top = `${rect.top}px`;
                
                // 添加占位元素
                sortableList.insertBefore(placeholder, item);
                
                // 记录鼠标在元素内的相对位置
                const mouseOffsetY = e.clientY - rect.top;
                
                // 自动滚动区域
                const modalBody = modal.querySelector('.modal-body');
                const modalRect = modalBody.getBoundingClientRect();
                const scrollThreshold = 50; // 距离边缘多少像素开始滚动
                
                // 鼠标移动事件
                function onMouseMove(e) {
                    if (!draggedItem) return;
                    
                    // 使用 requestAnimationFrame 优化性能
                    if (animationFrame) {
                        cancelAnimationFrame(animationFrame);
                    }
                    
                    animationFrame = requestAnimationFrame(() => {
                        // 计算移动距离，减缓移动速度
                        const deltaY = (e.clientY - lastY) * 0.6; // 降低移动速度为原来的60%
                        lastY = e.clientY;
                        
                        // 更新拖动元素位置，使用更平滑的动画
                        const currentTop = parseInt(draggedItem.style.top) || 0;
                        const newTop = currentTop + deltaY;
                        
                        // 使用 transform 代替 top 属性，提高性能
                        draggedItem.style.transform = `translateY(${newTop - rect.top}px)`;
                        draggedItem.style.top = `${newTop}px`;
                        
                        // 自动滚动，降低滚动速度
                        if (e.clientY < modalRect.top + scrollThreshold) {
                            // 向上滚动，速度更慢
                            modalBody.scrollBy(0, -3);
                        } else if (e.clientY > modalRect.bottom - scrollThreshold) {
                            // 向下滚动，速度更慢
                            modalBody.scrollBy(0, 3);
                        }
                        
                        // 获取拖动元素的中心位置
                        const draggedRect = draggedItem.getBoundingClientRect();
                        const draggedMiddle = draggedRect.top + draggedRect.height / 2;
                        
                        // 确定应该插入的位置，添加缓冲区减少频繁切换
                        let targetIndex = -1;
                        const bufferZone = 10; // 添加10px的缓冲区
                        
                        // 遍历所有项（除了占位符和拖动项）
                        Array.from(sortableList.children).forEach((child, index) => {
                            if (child === placeholder || child === draggedItem) return;
                            
                            const childRect = child.getBoundingClientRect();
                            const childMiddle = childRect.top + childRect.height / 2;
                            
                            // 使用缓冲区判断是否越过中点
                            if (draggedMiddle < childMiddle - bufferZone) {
                                if (targetIndex === -1 || index < targetIndex) {
                                    targetIndex = index;
                                }
                            }
                        });
                        
                        // 如果没有找到合适的位置，则放在最后
                        if (targetIndex === -1) {
                            // 避免频繁移动，只有当占位符不在最后时才移动
                            if (placeholder !== sortableList.lastChild) {
                                sortableList.appendChild(placeholder);
                            }
                        } else {
                            const targetChild = sortableList.children[targetIndex];
                            // 避免频繁移动，只有当占位符位置变化时才移动
                            if (placeholder.nextSibling !== targetChild) {
                                sortableList.insertBefore(placeholder, targetChild);
                            }
                        }
                    });
                }
                
                // 鼠标释放事件
                function onMouseUp(e) {
                    if (!draggedItem) return;
                    
                    // 取消动画帧
                    if (animationFrame) {
                        cancelAnimationFrame(animationFrame);
                        animationFrame = null;
                    }
                    
                    // 移除事件监听
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                    
                    // 获取占位符的位置
                    const placeholderIndex = Array.from(sortableList.children).indexOf(placeholder);
                    
                    // 平滑过渡到最终位置
                    const finalRect = placeholder.getBoundingClientRect();
                    const currentRect = draggedItem.getBoundingClientRect();
                    const deltaY = finalRect.top - currentRect.top;
                    
                    // 添加过渡效果，延长过渡时间
                    draggedItem.style.transition = 'transform 0.3s ease-out, top 0.3s ease-out';
                    draggedItem.style.transform = `translateY(${deltaY}px)`;
                    
                    // 延迟后恢复正常布局，延长延迟时间
                    setTimeout(() => {
                        // 移除占位符
                        placeholder.remove();
                        
                        // 恢复拖动元素的样式
                        draggedItem.classList.remove('dragging');
                        draggedItem.style.position = '';
                        draggedItem.style.top = '';
                        draggedItem.style.left = '';
                        draggedItem.style.width = '';
                        draggedItem.style.height = '';
                        draggedItem.style.zIndex = '';
                        draggedItem.style.transform = '';
                        draggedItem.style.transition = '';
                        
                        // 将拖动元素插入到占位符的位置
                        if (placeholderIndex >= 0) {
                            if (placeholderIndex >= sortableList.children.length) {
                                sortableList.appendChild(draggedItem);
                            } else {
                                sortableList.insertBefore(draggedItem, sortableList.children[placeholderIndex]);
                            }
                        }
                        
                        // 重置变量
                        draggedItem = null;
                        draggedIndex = -1;
                        placeholder = null;
                    }, 300); // 延长到300ms
                }
                
                // 添加事件监听
                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
        });
        
        // 保存排序按钮点击事件
        document.getElementById('saveGroupOrderBtn').addEventListener('click', function() {
            // 直接调用saveGroupOrder函数，让它处理所有逻辑
            saveGroupOrder();
        });
        
        // 模态框关闭事件
        modal.addEventListener('hidden.bs.modal', function() {
            modal.remove();
        });
    }
    
    // 保存分组排序
    function saveGroupOrder() {
        // 获取新的分组顺序
        const newOrder = [];
        document.querySelectorAll('#sortableGroupList li').forEach(item => {
            newOrder.push(item.dataset.groupName);
        });
        
        console.log('新的分组顺序:', newOrder);
        
        // 显示保存中提示
        const saveIndicator = document.createElement('div');
        saveIndicator.className = 'save-indicator';
        saveIndicator.innerHTML = '<div class="spinner-border spinner-border-sm text-light" role="status"></div> 保存中...';
        document.body.appendChild(saveIndicator);
        
        // 发送到后端
        fetch('/api/update_watchlists_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ order: newOrder })
        })
        .then(response => response.json())
        .then(data => {
            console.log('保存结果:', data);
            
            // 更新全局分组顺序
            if (data.groups_order && Array.isArray(data.groups_order)) {
                groupOrder = data.groups_order;
                console.log('使用API返回的分组顺序:', groupOrder);
            } else {
                groupOrder = newOrder;
                console.log('API没有返回分组顺序，使用新的顺序:', groupOrder);
            }
            
            // 标记已手动编辑和有未保存的更改
            hasBeenManuallyEdited = true;
            hasUnsavedChanges = true;
            
            // 移除保存提示
            saveIndicator.innerHTML = '<i class="fas fa-check"></i> 已保存';
            saveIndicator.classList.add('success');
            
            setTimeout(() => {
                saveIndicator.remove();
                // 关闭模态框
                const modal = document.getElementById('sortGroupsModal');
                const modalInstance = bootstrap.Modal.getInstance(modal);
                modalInstance.hide();
                
                // 重新渲染观察列表
                renderWatchlist();
                
                // 通知主界面刷新下拉框
                try {
                    if (window.opener && !window.opener.closed) {
                        console.log('尝试通知主界面刷新下拉框');
                        if (typeof window.opener.refreshWatchlistDropdown === 'function') {
                            // 如果主界面有刷新函数，则调用它并传递更新后的数据
                            window.opener.refreshWatchlistDropdown(data.watchlists);
                            console.log('已通知主界面刷新下拉框');
                        } else {
                            // 如果没有刷新函数，则尝试重新加载主界面
                            console.log('主界面没有刷新函数，尝试重新加载');
                            window.opener.location.reload();
                        }
                    }
                } catch (error) {
                    console.error('通知主界面刷新下拉框时出错:', error);
                }
            }, 1000);
        })
        .catch(error => {
            console.error('保存分组顺序出错:', error);
            saveIndicator.innerHTML = '<i class="fas fa-times"></i> 保存失败';
            saveIndicator.classList.add('error');
            
            setTimeout(() => {
                saveIndicator.remove();
            }, 2000);
        });
    }
    
    // 关闭编辑器
    function closeEditor() {
        // 检查是否有未保存的更改
        if (hasUnsavedChanges) {
            if (confirm('您有未保存的更改，是否在关闭前保存？')) {
                // 保存更改后关闭
                saveAndClose();
            } else {
                // 不保存直接关闭
                window.close();
            }
        } else {
            // 没有更改，直接关闭
            window.close();
        }
    }
    
    // 保存并关闭
    function saveAndClose() {
        // 防止重复调用
        if (window.isSavingAndClosing) {
            console.log('已经在保存并关闭中，跳过重复调用');
            return;
        }
        
        window.isSavingAndClosing = true;
        
        // 显示保存中状态
        const saveBtn = document.getElementById('saveAllBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 保存中...';
        saveBtn.disabled = true;
        
        // 准备要发送的数据，包括手动编辑标志和分组顺序
        const dataToSend = {
            watchlists: watchlistData,
            hasBeenManuallyEdited: hasBeenManuallyEdited,
            groups_order: groupOrder
        };
        
        fetch('/api/watchlists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataToSend)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`服务器返回错误: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showToast('股票列表已保存', 'success');
                
                // 通知主界面刷新下拉框 - 简化这部分代码
                try {
                    if (window.opener && !window.opener.closed) {
                        console.log('尝试通知主界面刷新下拉框');
                        
                        // 创建一个包含分组顺序的对象传递给主页面
                        const dataWithOrder = {
                            watchlists: watchlistData,
                            groups_order: groupOrder
                        };
                        
                        // 只调用一次刷新函数，避免多次调用
                        if (typeof window.opener.refreshWatchlistDropdown === 'function') {
                            window.opener.refreshWatchlistDropdown(dataWithOrder);
                            console.log('已通知主界面刷新下拉框，并传递分组顺序:', groupOrder);
                        }
                    }
                } catch (error) {
                    console.error('通知主界面刷新下拉框时出错:', error);
                }
                
                // 延迟关闭窗口，让用户看到保存成功的提示
                setTimeout(() => {
                    window.close();
                }, 800);
            } else {
                throw new Error(data.error || '保存失败');
            }
        })
        .catch(error => {
            console.error('保存失败:', error);
            showToast('保存失败: ' + error.message, 'danger');
            
            // 恢复按钮状态
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            
            // 重置保存标志
            window.isSavingAndClosing = false;
        });
    }
    
    // 事件监听
    addGroupBtn.addEventListener('click', addGroup);
    refreshBtn.addEventListener('click', loadWatchlistData);
    saveAllBtn.addEventListener('click', saveAllChanges);
    importStocksBtn.addEventListener('click', importStocks);
    sortGroupsBtn.addEventListener('click', sortGroups);
    closeEditorBtn.addEventListener('click', closeEditor);
    
    // 初始加载
    loadWatchlistData();
    
    // 监听页面关闭事件，提示保存
    window.addEventListener('beforeunload', function(e) {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '您有未保存的更改，确定要离开吗？';
            return e.returnValue;
        }
    });
    
    // 清除选择
    function clearSelection() {
        selectedStocks = [];
        renderMultiSelectActions();
    }
}); 