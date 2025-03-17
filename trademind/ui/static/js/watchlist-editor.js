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
                } else {
                    // 如果没有返回预期的数据结构，使用原始数据
                    watchlistData = data;
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
            });
    }
    
    // 渲染股票列表
    function renderWatchlist() {
        if (!watchlistData) return;
        
        console.log('渲染数据:', watchlistData);
        
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
        
        // 遍历每个分组
        Object.keys(watchlistData).forEach(groupName => {
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
        
        fetch('/api/watchlists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(watchlistData)
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
    
    // 事件监听
    addGroupBtn.addEventListener('click', addGroup);
    refreshBtn.addEventListener('click', loadWatchlistData);
    saveAllBtn.addEventListener('click', saveAllChanges);
    importStocksBtn.addEventListener('click', importStocks);
    
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