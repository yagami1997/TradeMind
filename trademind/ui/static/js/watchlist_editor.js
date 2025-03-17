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

// 初始化页面
function initPage() {
    console.log('初始化自选股编辑器页面');
    
    // 获取DOM元素
    watchlistContainer = document.getElementById('watchlistContainer');
    const addGroupBtn = document.getElementById('addGroupBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const importStocksBtn = document.getElementById('importStocksBtn');
    const sortGroupsBtn = document.getElementById('sortGroupsBtn');
    const closeEditorBtn = document.getElementById('closeEditorBtn');
    
    // 添加关闭编辑器按钮的点击事件
    if (closeEditorBtn) {
        closeEditorBtn.addEventListener('click', function() {
            // 弹出提示信息
            alert('请手动刷新Web主页，加载最新的自选股分组');
            // 关闭当前窗口
            window.close();
        });
    } else {
        console.error('找不到关闭编辑器按钮');
    }
    
    // 加载股票列表数据
    loadWatchlistData();
    
    // 添加其他按钮的事件处理
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadWatchlistData();
        });
    }
}

// 加载股票列表数据
function loadWatchlistData() {
    // 显示加载中状态
    if (watchlistContainer) {
        watchlistContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载股票列表...</p>
            </div>
        `;
    }
    
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
            } else {
                // 如果没有返回预期的数据结构，使用原始数据
                watchlistData = data;
                
                // 如果之前没有从页面获取到分组顺序，则使用Object.keys()
                if (!groupOrder || groupOrder.length === 0) {
                    // 保存分组顺序
                    groupOrder = Object.keys(watchlistData);
                    console.log('使用原始数据，分组顺序:', groupOrder);
                }
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
            if (watchlistContainer) {
                watchlistContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle-fill"></i> 
                        加载股票列表失败: ${error.message}
                        <hr>
                        <p>请检查服务器连接或刷新页面重试。</p>
                    </div>
                `;
            }
            
            // 如果加载失败，初始化一个空的数据结构
            watchlistData = { '默认分组': {} };
            groupOrder = ['默认分组'];
        });
}

// 渲染股票列表
function renderWatchlist() {
    if (!watchlistData || !watchlistContainer) return;
    
    console.log('渲染数据:', watchlistData);
    console.log('使用分组顺序:', groupOrder);
    
    watchlistContainer.innerHTML = '';
    
    // 按照分组顺序渲染
    groupOrder.forEach(groupName => {
        if (watchlistData[groupName]) {
            const groupStocks = watchlistData[groupName];
            const stockCount = Object.keys(groupStocks).length;
            
            const groupDiv = document.createElement('div');
            groupDiv.className = 'watchlist-group mb-4';
            groupDiv.innerHTML = `
                <div class="group-header">
                    <h3>${groupName}</h3>
                    <span class="badge bg-primary">${stockCount}个股票</span>
                </div>
                <div class="group-content">
                    <div class="stock-list">
                        ${Object.entries(groupStocks).map(([code, name]) => `
                            <div class="stock-item">
                                <span class="stock-code">${code}</span>
                                <span class="stock-name">${name}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            watchlistContainer.appendChild(groupDiv);
        }
    });
}

// 初始化页面
initPage(); 