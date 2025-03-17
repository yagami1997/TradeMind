/**
 * TradeMind Lite - 股票列表编辑器
 * 
 * 本文件包含股票列表编辑器的前端交互逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const watchlistContainer = document.getElementById('watchlistContainer');
    const addGroupBtn = document.getElementById('addGroupBtn');
    const saveGroupBtn = document.getElementById('saveGroupBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const addGroupModal = new bootstrap.Modal(document.getElementById('addGroupModal'));
    
    // 全局变量
    let watchlists = {};
    let hasChanges = false;
    
    // 初始化
    loadWatchlists();
    
    // 事件监听器
    addGroupBtn.addEventListener('click', function() {
        addGroupModal.show();
    });
    
    saveGroupBtn.addEventListener('click', function() {
        const groupName = document.getElementById('groupName').value.trim();
        if (groupName) {
            if (!watchlists[groupName]) {
                watchlists[groupName] = {};
                renderWatchlists();
                addGroupModal.hide();
                document.getElementById('groupName').value = '';
                hasChanges = true;
                showToast('成功添加分组: ' + groupName);
            } else {
                showToast('分组已存在', 'error');
            }
        }
    });
    
    refreshBtn.addEventListener('click', function() {
        if (hasChanges) {
            if (confirm('您有未保存的更改，刷新将丢失这些更改。确定要继续吗？')) {
                loadWatchlists();
            }
        } else {
            loadWatchlists();
        }
    });
    
    saveAllBtn.addEventListener('click', function() {
        saveWatchlists();
    });
    
    // 加载股票列表
    function loadWatchlists() {
        watchlistContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载股票列表...</p>
            </div>
        `;
        
        fetch('/api/watchlists')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    watchlists = data.watchlists;
                    renderWatchlists();
                    hasChanges = false;
                } else {
                    watchlistContainer.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            <i class="bi bi-exclamation-triangle-fill"></i> 加载股票列表失败: ${data.error || '未知错误'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                watchlistContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="bi bi-exclamation-triangle-fill"></i> 加载股票列表出错: ${error.message}
                    </div>
                `;
            });
    }
    
    // 渲染股票列表
    function renderWatchlists() {
        watchlistContainer.innerHTML = '';
        
        if (Object.keys(watchlists).length === 0) {
            watchlistContainer.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-circle-fill"></i> 没有找到股票列表。点击"添加分组"按钮创建一个新分组。
                </div>
            `;
            return;
        }
        
        for (const groupName in watchlists) {
            const stocks = watchlists[groupName];
            const stockCount = Object.keys(stocks).length;
            
            const groupCard = document.createElement('div');
            groupCard.className = 'group-card mb-4';
            groupCard.innerHTML = `
                <div class="group-header">
                    <div>
                        <h5 class="mb-0 d-inline-block">
                            <span class="group-name" data-group="${groupName}">${groupName}</span>
                            <span class="badge bg-secondary ms-2">${stockCount}个股票</span>
                        </h5>
                        <button class="btn btn-sm btn-link edit-group-name" data-group="${groupName}">
                            <i class="bi bi-pencil"></i>
                        </button>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary add-stock-btn" data-group="${groupName}">
                            <i class="bi bi-plus-circle"></i> 添加股票
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-group-btn" data-group="${groupName}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="group-body">
                    <div class="stock-list" data-group="${groupName}">
                    </div>
                </div>
                <div class="add-stock-form d-none" data-group="${groupName}">
                    <div class="row g-2">
                        <div class="col-md-4">
                            <input type="text" class="form-control stock-code-input" placeholder="股票代码" required>
                        </div>
                        <div class="col-md-6">
                            <input type="text" class="form-control stock-name-input" placeholder="股票名称" required>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-primary w-100 confirm-add-stock" data-group="${groupName}">添加</button>
                        </div>
                    </div>
                </div>
            `;
            
            watchlistContainer.appendChild(groupCard);
            
            const stockList = groupCard.querySelector(`.stock-list[data-group="${groupName}"]`);
            
            // 添加股票行
            for (const stockCode in stocks) {
                const stockName = stocks[stockCode];
                addStockRow(stockList, groupName, stockCode, stockName);
            }
            
            // 添加事件监听器
            const deleteGroupBtn = groupCard.querySelector(`.delete-group-btn[data-group="${groupName}"]`);
            deleteGroupBtn.addEventListener('click', function() {
                if (confirm(`确定要删除分组"${groupName}"吗？这将删除该分组中的所有股票。`)) {
                    delete watchlists[groupName];
                    renderWatchlists();
                    hasChanges = true;
                    showToast(`已删除分组: ${groupName}`);
                }
            });
            
            const addStockBtn = groupCard.querySelector(`.add-stock-btn[data-group="${groupName}"]`);
            const addStockForm = groupCard.querySelector(`.add-stock-form[data-group="${groupName}"]`);
            
            addStockBtn.addEventListener('click', function() {
                addStockForm.classList.toggle('d-none');
                if (!addStockForm.classList.contains('d-none')) {
                    addStockForm.querySelector('.stock-code-input').focus();
                }
            });
            
            const confirmAddStockBtn = groupCard.querySelector(`.confirm-add-stock[data-group="${groupName}"]`);
            confirmAddStockBtn.addEventListener('click', function() {
                const stockCodeInput = addStockForm.querySelector('.stock-code-input');
                const stockNameInput = addStockForm.querySelector('.stock-name-input');
                
                const stockCode = stockCodeInput.value.trim().toUpperCase();
                const stockName = stockNameInput.value.trim();
                
                if (stockCode && stockName) {
                    watchlists[groupName][stockCode] = stockName;
                    addStockRow(stockList, groupName, stockCode, stockName);
                    stockCodeInput.value = '';
                    stockNameInput.value = '';
                    hasChanges = true;
                    showToast(`已添加股票: ${stockCode} (${stockName})`);
                } else {
                    showToast('请输入股票代码和名称', 'error');
                }
            });
            
            const editGroupNameBtn = groupCard.querySelector(`.edit-group-name[data-group="${groupName}"]`);
            editGroupNameBtn.addEventListener('click', function() {
                const groupNameSpan = groupCard.querySelector(`.group-name[data-group="${groupName}"]`);
                const currentName = groupNameSpan.textContent;
                
                const newName = prompt('请输入新的分组名称:', currentName);
                if (newName && newName !== currentName) {
                    if (!watchlists[newName]) {
                        watchlists[newName] = {...watchlists[groupName]};
                        delete watchlists[groupName];
                        renderWatchlists();
                        hasChanges = true;
                        showToast(`已将分组"${currentName}"重命名为"${newName}"`);
                    } else {
                        showToast(`分组"${newName}"已存在`, 'error');
                    }
                }
            });
        }
    }
    
    // 添加股票行
    function addStockRow(stockList, groupName, stockCode, stockName) {
        const stockRow = document.createElement('div');
        stockRow.className = 'stock-row';
        stockRow.dataset.code = stockCode;
        
        stockRow.innerHTML = `
            <div class="stock-code">${stockCode}</div>
            <div class="stock-name" data-code="${stockCode}" data-group="${groupName}">${stockName}</div>
            <div class="actions">
                <button class="btn btn-sm btn-link edit-stock-btn" data-code="${stockCode}" data-group="${groupName}">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-link text-danger delete-stock-btn" data-code="${stockCode}" data-group="${groupName}">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        
        stockList.appendChild(stockRow);
        
        // 添加事件监听器
        const editStockBtn = stockRow.querySelector(`.edit-stock-btn[data-code="${stockCode}"]`);
        editStockBtn.addEventListener('click', function() {
            const stockNameDiv = stockRow.querySelector(`.stock-name[data-code="${stockCode}"]`);
            const currentName = stockNameDiv.textContent;
            
            const newName = prompt('请输入新的股票名称:', currentName);
            if (newName && newName !== currentName) {
                watchlists[groupName][stockCode] = newName;
                stockNameDiv.textContent = newName;
                hasChanges = true;
                showToast(`已将股票"${stockCode}"的名称修改为"${newName}"`);
            }
        });
        
        const deleteStockBtn = stockRow.querySelector(`.delete-stock-btn[data-code="${stockCode}"]`);
        deleteStockBtn.addEventListener('click', function() {
            if (confirm(`确定要删除股票"${stockCode} (${stockName})"吗？`)) {
                delete watchlists[groupName][stockCode];
                stockRow.remove();
                hasChanges = true;
                showToast(`已删除股票: ${stockCode}`);
                
                // 更新股票数量
                const stockCount = Object.keys(watchlists[groupName]).length;
                const badge = document.querySelector(`.group-header h5 .badge[data-group="${groupName}"]`);
                if (badge) {
                    badge.textContent = `${stockCount}个股票`;
                }
            }
        });
    }
    
    // 保存股票列表
    function saveWatchlists() {
        saveAllBtn.disabled = true;
        saveAllBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 保存中...';
        
        fetch('/api/save-watchlists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                watchlists: watchlists
            })
        })
        .then(response => response.json())
        .then(data => {
            saveAllBtn.disabled = false;
            saveAllBtn.innerHTML = '<i class="bi bi-save"></i> 保存所有修改';
            
            if (data.success) {
                hasChanges = false;
                showToast('股票列表已保存');
            } else {
                showToast('保存股票列表失败: ' + (data.error || '未知错误'), 'error');
            }
        })
        .catch(error => {
            saveAllBtn.disabled = false;
            saveAllBtn.innerHTML = '<i class="bi bi-save"></i> 保存所有修改';
            showToast('保存股票列表出错: ' + error.message, 'error');
        });
    }
    
    // 显示提示消息
    function showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${type === 'error' ? 'bg-danger text-white' : 'bg-success text-white'}">
                    <strong class="me-auto">${type === 'error' ? '错误' : '成功'}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        // 自动删除
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
    
    // 页面关闭前提示保存
    window.addEventListener('beforeunload', function(e) {
        if (hasChanges) {
            const message = '您有未保存的更改，确定要离开吗？';
            e.returnValue = message;
            return message;
        }
    });
}); 