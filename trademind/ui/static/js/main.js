/**
 * TradeMind Lite - 主JavaScript文件
 */

// 全局函数，用于刷新观察列表下拉框
function refreshWatchlistDropdown(data) {
    // 防御性检查输入数据
    if (!data) {
        console.error('刷新观察列表下拉框失败: 数据为空');
        return;
    }
    
    // 处理不同格式的输入数据
    let watchlists = data;
    let groups_order = null;
    
    try {
        // 如果传入的是包含watchlists和groups_order的对象
        if (data && typeof data === 'object' && data.watchlists) {
            watchlists = data.watchlists;
            groups_order = data.groups_order;
            console.log('主界面刷新观察列表下拉框，包含分组顺序');
        } else {
            console.log('主界面刷新观察列表下拉框，无分组顺序');
        }
        
        // 防御性检查watchlists
        if (!watchlists || typeof watchlists !== 'object' || Array.isArray(watchlists)) {
            console.error('刷新观察列表下拉框失败: watchlists格式不正确');
            return;
        }
        
        // 获取下拉菜单元素
        const watchlistSelect = document.getElementById('watchlist');
        if (!watchlistSelect) {
            console.error('找不到观察列表下拉菜单');
            return;
        }
        
        // 保存当前选中的值
        const selectedValue = watchlistSelect.value;
        
        // 清空下拉菜单，只保留第一个选项
        while (watchlistSelect.options.length > 1) {
            watchlistSelect.remove(1);
        }
        
        // 确定分组顺序
        let groupNames = Object.keys(watchlists);
        
        // 如果提供了分组顺序，使用它
        if (groups_order && Array.isArray(groups_order) && groups_order.length > 0) {
            console.log('使用提供的分组顺序');
            
            // 创建一个新的数组，按照指定的顺序排列分组
            const orderedGroups = [];
            
            // 首先添加按顺序排列的分组
            groups_order.forEach(groupName => {
                if (watchlists[groupName]) {
                    orderedGroups.push(groupName);
                }
            });
            
            // 然后添加未在顺序中指定的分组
            groupNames.forEach(groupName => {
                if (!orderedGroups.includes(groupName)) {
                    orderedGroups.push(groupName);
                }
            });
            
            // 使用排序后的分组名称
            groupNames = orderedGroups;
            console.log('最终使用的分组顺序长度:', groupNames.length);
        }
        
        // 添加新的选项
        groupNames.forEach(groupName => {
            try {
                const option = document.createElement('option');
                option.value = groupName;
                
                // 防御性检查watchlists[groupName]
                if (watchlists[groupName] && typeof watchlists[groupName] === 'object') {
                    option.textContent = `${groupName} (${Object.keys(watchlists[groupName]).length}个股票)`;
                } else {
                    option.textContent = `${groupName} (0个股票)`;
                }
                
                watchlistSelect.appendChild(option);
            } catch (optionError) {
                console.error(`添加选项 ${groupName} 时出错:`, optionError);
                // 继续处理其他选项，不中断执行
            }
        });
        
        // 恢复之前选中的值，如果它仍然存在
        try {
            if (selectedValue && Array.from(watchlistSelect.options).some(option => option.value === selectedValue)) {
                watchlistSelect.value = selectedValue;
            }
            
            // 触发change事件，更新股票列表
            const event = new Event('change');
            watchlistSelect.dispatchEvent(event);
        } catch (selectError) {
            console.error('设置选中值或触发事件时出错:', selectError);
        }
    } catch (error) {
        console.error('刷新观察列表下拉菜单时出错:', error);
    }
}

// 加载观察列表
function loadWatchlists(forceRefresh = false) {
    // 防止循环调用
    if (window.isLoadingWatchlists) {
        console.log('跳过加载观察列表，防止循环调用');
        return;
    }
    
    window.isLoadingWatchlists = true;
    console.log('加载观察列表...');
    
    // 添加时间戳参数，防止缓存
    const timestamp = new Date().getTime();
    const url = `/api/watchlists?t=${timestamp}`;
    
    // 添加超时处理
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时
    
    fetch(url, { 
        signal: controller.signal,
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`服务器返回错误: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.watchlists) {
            console.log('成功获取观察列表数据');
            
            // 创建一个包含watchlists和groups_order的对象
            const watchlistData = {
                watchlists: data.watchlists,
                groups_order: data.groups_order || Object.keys(data.watchlists)
            };
            
            try {
                // 使用refreshWatchlistDropdown函数更新下拉菜单
                refreshWatchlistDropdown(watchlistData);
            } catch (refreshError) {
                console.error('刷新下拉菜单时出错:', refreshError);
                // 出错时不抛出异常，避免中断执行
            }
        } else {
            console.error('获取观察列表失败:', data);
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            console.error('获取观察列表超时');
        } else {
            console.error('获取观察列表时出错:', error);
        }
    })
    .finally(() => {
        // 延迟重置标志，防止短时间内多次调用
        setTimeout(() => {
            window.isLoadingWatchlists = false;
        }, 1000);
    });
}

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const analyzeForm = document.getElementById('analyzeForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeSpinner = document.getElementById('analyzeSpinner');
    const resultCard = document.getElementById('resultCard');
    const resultMessage = document.getElementById('resultMessage');
    const viewReportBtn = document.getElementById('viewReportBtn');
    const cleanReportsBtn = document.getElementById('cleanReportsBtn');
    const cleanReportsModal = new bootstrap.Modal(document.getElementById('cleanReportsModal'));
    const confirmCleanBtn = document.getElementById('confirmCleanBtn');
    const cleanSpinner = document.getElementById('cleanSpinner');
    const symbolsInput = document.getElementById('symbols');
    const watchlistSelect = document.getElementById('watchlist');

    // 加载临时查询列表
    loadTempQueryStocks();
    
    // 加载观察列表
    loadWatchlists();
    
    // 添加隐藏的标记元素，用于检测是否需要重新加载
    const reloadFlag = document.createElement('div');
    reloadFlag.id = 'watchlistReloadFlag';
    reloadFlag.style.display = 'none';
    document.body.appendChild(reloadFlag);
    
    // 监听自定义事件，用于在编辑器保存后刷新观察列表
    document.addEventListener('watchlistUpdated', function(e) {
        console.log('收到watchlistUpdated事件:', e.detail);
        // 重新加载观察列表
        loadWatchlists();
    });
    
    // 监听编辑器关闭事件
    document.addEventListener('watchlistEditorClosed', function(e) {
        console.log('收到watchlistEditorClosed事件:', e.detail);
        // 强制重新加载观察列表
        loadWatchlists(true);
    });
    
    // 检查localStorage，看是否需要刷新观察列表
    const editorSaved = localStorage.getItem('watchlistEditorSaved');
    const editorSavedTime = localStorage.getItem('watchlistEditorSavedTime');
    const editorClosed = localStorage.getItem('watchlistEditorClosed');
    const editorClosedTime = localStorage.getItem('watchlistEditorClosedTime');
    
    if (editorSaved === 'true' && editorSavedTime) {
        const savedTime = parseInt(editorSavedTime);
        const currentTime = new Date().getTime();
        const timeDiff = currentTime - savedTime;
        
        // 如果保存时间在5秒内，刷新观察列表
        if (timeDiff < 5000) {
            console.log('检测到编辑器最近保存了数据，刷新观察列表');
            loadWatchlists();
            // 清除标记
            localStorage.removeItem('watchlistEditorSaved');
            localStorage.removeItem('watchlistEditorSavedTime');
        }
    }
    
    // 检查编辑器是否最近关闭
    if (editorClosed === 'true' && editorClosedTime) {
        const closedTime = parseInt(editorClosedTime);
        const currentTime = new Date().getTime();
        const timeDiff = currentTime - closedTime;
        
        // 如果关闭时间在5秒内，刷新观察列表
        if (timeDiff < 5000) {
            console.log('检测到编辑器最近关闭，刷新观察列表');
            loadWatchlists(true);
            // 清除标记
            localStorage.removeItem('watchlistEditorClosed');
            localStorage.removeItem('watchlistEditorClosedTime');
        }
    }

    // 添加浏览器关闭事件监听器
    let isRealClose = true; // 添加标志变量，控制是否真的关闭服务器
    
    // 在页面内部导航时设置标志
    document.addEventListener('click', function(e) {
        // 如果点击的是导航链接或表单提交按钮，设置标志为false
        if (e.target.tagName === 'A' || 
            (e.target.tagName === 'BUTTON' && e.target.type === 'submit')) {
            isRealClose = false;
            // 2秒后重置标志，以防导航被取消
            setTimeout(() => { isRealClose = true; }, 2000);
        }
    });
    
    // 设置一个标记，表示页面正在刷新
    let isRefreshing = false;
    
    // 监听页面刷新事件 - F5键
    window.addEventListener('keydown', function(e) {
        if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
            console.log('检测到刷新快捷键，标记页面正在刷新');
            isRefreshing = true;
        }
    });
    
    // 监听页面刷新按钮点击
    window.addEventListener('beforeunload', function(e) {
        // 保存临时查询列表
        try {
            saveTempQueryStocks();
        } catch (error) {
            console.error('保存临时查询列表时出错:', error);
        }
        
        // 如果是内部导航，不关闭服务器
        if (!isRealClose) {
            console.log('检测到内部导航，不关闭服务器');
            return;
        }
        
        // 如果是刷新，不关闭服务器
        if (isRefreshing) {
            console.log('检测到页面刷新，不关闭服务器');
            return;
        }
        
        // 如果是通过浏览器刷新按钮刷新，不关闭服务器
        // 这是一个简单的方法，通过检查document.visibilityState来判断
        // 刷新时页面仍然可见，而关闭时页面不可见
        if (document.visibilityState !== 'hidden') {
            console.log('检测到页面仍然可见，可能是刷新，不关闭服务器');
            return;
        }
        
        // 到这里，应该是真正的浏览器关闭
        console.log('检测到浏览器关闭，尝试关闭服务器');
        
        // 发送关闭服务器的请求
        try {
            // 使用sendBeacon API，它专为页面卸载时发送请求设计
            if (navigator.sendBeacon) {
                navigator.sendBeacon('/api/shutdown?real_close=true', 'real_close=true');
                console.log('已使用sendBeacon发送关闭服务器请求');
            } else {
                // 备用方案：使用同步XMLHttpRequest
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/shutdown?real_close=true', false); // 同步请求
                xhr.setRequestHeader('Content-Type', 'text/plain');
                xhr.send('real_close=true');
                console.log('已使用同步XHR发送关闭服务器请求');
            }
        } catch (error) {
            console.error('关闭服务器时出错:', error);
        }
    });

    // 分析表单提交
    analyzeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const analyzeAll = document.getElementById('analyzeAll').checked;
        
        // 检查是否至少指定了股票代码、观察列表或选择了分析所有股票
        if (!symbolsInput.value.trim() && !watchlistSelect.value && !analyzeAll) {
            alert('请输入股票代码、选择观察列表或选择分析所有股票');
            return;
        }
        
        // 如果有输入股票代码，保存到临时查询列表
        if (symbolsInput.value.trim()) {
            saveTempQueryStocks();
        }
        
        // 禁用按钮并显示加载动画
        analyzeBtn.disabled = true;
        analyzeSpinner.classList.remove('d-none');
        
        // 获取表单数据
        let symbols = [];
        let names = {};
        
        if (symbolsInput.value.trim()) {
            // 从输入框获取股票代码
            symbols = symbolsInput.value.trim().split(/[\n,]+/).map(s => s.trim()).filter(s => s);
        } else if (watchlistSelect.value) {
            // 从观察列表获取股票代码
            const selectedGroup = watchlistSelect.value;
            fetch('/watchlists')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.watchlists && data.watchlists[selectedGroup]) {
                        const stocks = data.watchlists[selectedGroup];
                        
                        // 获取分组顺序数组（如果存在）
                        let groupOrder = data.groups_order || Object.keys(data.watchlists);
                        
                        // 添加防御性检查
                        if (!Array.isArray(groupOrder)) {
                            console.warn('分组顺序不是数组，使用默认顺序');
                            groupOrder = Object.keys(data.watchlists);
                        }
                        
                        // 获取stock_order.json中的顺序（如果存在）
                        fetch(`/api/get-stock-order?group=${encodeURIComponent(selectedGroup)}`)
                            .then(res => res.json())
                            .then(orderData => {
                                // 使用有序数组存储股票代码
                                let orderedSymbols = [];
                                
                                // 如果API返回了有序的股票列表
                                if (orderData.success && Array.isArray(orderData.stock_order) && orderData.stock_order.length > 0) {
                                    console.log(`使用保存的股票顺序，共${orderData.stock_order.length}个股票`);
                                    
                                    // 首先添加按顺序的股票
                                    for (const symbol of orderData.stock_order) {
                                        if (stocks[symbol]) {
                                            orderedSymbols.push(symbol);
                                        }
                                    }
                                    
                                    // 然后添加可能遗漏的股票（不在保存顺序中但在分类列表中的股票）
                                    for (const symbol in stocks) {
                                        if (!orderedSymbols.includes(symbol)) {
                                            orderedSymbols.push(symbol);
                                        }
                                    }
                                } else {
                                    // 如果没有保存的顺序，使用JSON文件中的原始顺序（基于Object.keys的顺序）
                                    console.log('未找到保存的股票顺序，使用默认顺序');
                                    orderedSymbols = Object.keys(stocks);
                                }
                                
                                // 使用有序数组构建symbols和names
                                for (const symbol of orderedSymbols) {
                                    symbols.push(symbol);
                                    names[symbol] = stocks[symbol];
                                }
                                
                                // 发送分析请求
                                const title = document.getElementById('title').value || '美股技术面分析报告';
                                sendAnalysisRequest(symbols, names, title, false);
                            })
                            .catch(error => {
                                console.error('获取股票顺序时出错，使用默认顺序:', error);
                                // 出错时使用默认顺序
                                for (const symbol in stocks) {
                                    symbols.push(symbol);
                                    names[symbol] = stocks[symbol];
                                }
                                
                                // 发送分析请求
                                const title = document.getElementById('title').value || '美股技术面分析报告';
                                sendAnalysisRequest(symbols, names, title, false);
                            });
                    } else {
                        alert('获取观察列表失败');
                        analyzeBtn.disabled = false;
                        analyzeSpinner.classList.add('d-none');
                    }
                })
                .catch(error => {
                    console.error('获取观察列表时出错:', error);
                    alert('获取观察列表时出错');
                    analyzeBtn.disabled = false;
                    analyzeSpinner.classList.add('d-none');
                });
            return;
        }
        
        // 发送分析请求
        const title = document.getElementById('title').value || '美股技术面分析报告';
        sendAnalysisRequest(symbols, names, title, analyzeAll);
    });
    
    // 加载临时查询股票列表
    function loadTempQueryStocks() {
        fetch('/api/temp-query')
            .then(response => response.json())
            .then(data => {
                if (data.codes && data.codes.length > 0) {
                    symbolsInput.value = data.codes.join('\n');
                }
            })
            .catch(error => {
                console.error('加载临时查询股票列表时出错:', error);
            });
    }
    
    // 保存临时查询股票列表
    function saveTempQueryStocks() {
        if (!symbolsInput.value.trim()) return;
        
        const codes = symbolsInput.value.trim().split(/[\n,]+/).map(s => s.trim()).filter(s => s);
        if (codes.length === 0) return;
        
        fetch('/api/temp-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                codes: codes
            })
        })
        .catch(error => {
            console.error('保存临时查询股票列表时出错:', error);
        });
    }
    
    // 分析所有股票复选框事件
    document.getElementById('analyzeAll').addEventListener('change', function() {
        const watchlistSelect = document.getElementById('watchlist');
        if (this.checked) {
            watchlistSelect.disabled = true;
            watchlistSelect.value = '';
        } else {
            watchlistSelect.disabled = false;
        }
    });
    
    // 发送分析请求的函数
    function sendAnalysisRequest(symbols, names, title, analyzeAll) {
        // 创建进度显示区域
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress mb-3';
        progressContainer.style.height = '25px';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        progressBar.role = 'progressbar';
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', '0');
        progressBar.setAttribute('aria-valuemin', '0');
        progressBar.setAttribute('aria-valuemax', '100');
        progressBar.textContent = '准备分析...';
        
        progressContainer.appendChild(progressBar);
        
        // 创建状态文本区域
        const statusText = document.createElement('div');
        statusText.className = 'alert alert-info';
        statusText.textContent = '正在初始化分析...';
        
        // 显示进度区域
        resultCard.classList.remove('d-none');
        resultCard.querySelector('.card-header').classList.remove('bg-danger');
        resultCard.querySelector('.card-header').classList.remove('bg-success');
        resultCard.querySelector('.card-header').classList.remove('bg-primary');
        resultCard.querySelector('.card-header h5').textContent = '分析进行中';
        resultMessage.innerHTML = '';
        resultMessage.appendChild(statusText);
        resultMessage.appendChild(progressContainer);
        viewReportBtn.classList.add('d-none');
        
        // 设置轮询进度的间隔
        let progressInterval = null;
        
        // 发送AJAX请求
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbols: symbols,
                names: names,
                title: title,
                analyze_all: analyzeAll
            })
        })
        .then(response => {
            // 开始轮询进度
            progressInterval = setInterval(() => {
                fetch('/api/progress')
                    .then(res => res.json())
                    .then(data => {
                        if (data.progress && data.progress.in_progress) {
                            // 更新进度条
                            const percent = Math.min(Math.round(data.progress.percent * 100), 99);
                            progressBar.style.width = `${percent}%`;
                            progressBar.setAttribute('aria-valuenow', percent);
                            progressBar.textContent = `${percent}%`;
                            
                            // 更新状态文本
                            if (data.progress.current_symbol) {
                                statusText.textContent = `正在分析: ${data.progress.current_symbol} (${data.progress.current_index}/${data.progress.total})`;
                            }
                            
                            // 显示预计剩余时间（如果有）
                            if (data.progress.remaining_seconds) {
                                const remainingMinutes = Math.round(data.progress.remaining_seconds / 60);
                                if (remainingMinutes > 0) {
                                    statusText.textContent += ` - 预计剩余时间: ${remainingMinutes} 分钟`;
                                } else {
                                    statusText.textContent += ` - 即将完成`;
                                }
                            }
                        } else if (data.progress && !data.progress.in_progress) {
                            // 分析已完成，停止轮询
                            clearInterval(progressInterval);
                            
                            // 更新进度条为100%
                            progressBar.style.width = '100%';
                            progressBar.setAttribute('aria-valuenow', '100');
                            progressBar.textContent = '100%';
                            progressBar.className = 'progress-bar bg-success';
                            
                            // 更新状态文本
                            statusText.textContent = '分析已完成，报告已生成！';
                            statusText.className = 'alert alert-success';
                            
                            // 显示报告链接
                            if (data.progress.report_url) {
                                viewReportBtn.classList.remove('d-none');
                                viewReportBtn.href = data.progress.report_url;
                                
                                // 显示报告路径和时间戳
                                const reportPathElement = document.createElement('p');
                                reportPathElement.innerHTML = `报告路径: <code>${data.progress.report_path}</code>`;
                                resultMessage.appendChild(reportPathElement);
                                
                                // 显示时间戳（如果有）
                                if (data.progress.timestamp) {
                                    const timestampElement = document.createElement('p');
                                    timestampElement.innerHTML = `生成时间: <code>${data.progress.timestamp}</code>`;
                                    resultMessage.appendChild(timestampElement);
                                }
                                
                                // 显示回测结果说明
                                const backTestExplanation = document.querySelector('.backtest-zero-notice');
                                if (backTestExplanation) {
                                    backTestExplanation.style.display = 'block';
                                }
                                
                                // 更新结果卡片
                                resultCard.querySelector('.card-header').classList.remove('bg-primary');
                                resultCard.querySelector('.card-header').classList.remove('bg-danger');
                                resultCard.querySelector('.card-header').classList.remove('bg-success');
                                resultCard.querySelector('.card-header h5').textContent = '分析成功';
                                
                                // 刷新报告列表
                                loadRecentReports();
                            }
                            
                            // 启用分析按钮
                            analyzeBtn.disabled = false;
                            analyzeSpinner.classList.add('d-none');
                        }
                    })
                    .catch(err => console.error('获取进度失败:', err));
            }, 1000);
            
            return response.json();
        })
        .catch(error => {
            // 停止进度轮询
            if (progressInterval) {
                clearInterval(progressInterval);
            }
            
            // 隐藏加载动画
            analyzeBtn.disabled = false;
            analyzeSpinner.classList.add('d-none');
            
            // 显示错误信息
            resultCard.querySelector('.card-header').classList.remove('bg-primary');
            resultCard.querySelector('.card-header').classList.remove('bg-success');
            resultCard.querySelector('.card-header').classList.add('bg-danger');
            resultCard.querySelector('.card-header h5').textContent = '分析失败';
            resultMessage.innerHTML = '';
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger';
            errorAlert.textContent = '发生错误：' + error.message;
            resultMessage.appendChild(errorAlert);
            viewReportBtn.classList.add('d-none');
        });
    }
    
    // 清理报告按钮点击
    cleanReportsBtn.addEventListener('click', function(e) {
        e.preventDefault();
        cleanReportsModal.show();
    });
    
    // 清理选项按钮点击
    document.querySelectorAll('.clean-option').forEach(button => {
        button.addEventListener('click', function() {
            const days = this.getAttribute('data-days');
            document.getElementById('days').value = days;
            
            // 直接触发确认清理
            confirmCleanBtn.click();
        });
    });
    
    // 确认清理按钮点击
    confirmCleanBtn.addEventListener('click', function() {
        // 显示加载动画
        confirmCleanBtn.disabled = true;
        cleanSpinner.classList.remove('d-none');
        
        // 获取天数
        const days = document.getElementById('days').value;
        
        // 获取是否强制删除所有
        const forceAll = document.getElementById('forceAll').checked;
        
        // 创建FormData对象
        const formData = new FormData();
        formData.append('days', days);
        formData.append('force_all', forceAll);
        
        // 发送AJAX请求
        fetch('/clean', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // 无论成功与否，都重置按钮状态
            confirmCleanBtn.disabled = false;
            cleanSpinner.classList.add('d-none');
            return response.json();
        })
        .then(data => {
            // 隐藏模态框
            cleanReportsModal.hide();
            
            if (data.error || !data.success) {
                alert('清理报告失败：' + (data.error || '未知错误'));
            } else {
                // 显示成功消息
                alert(data.message || '报告清理成功！');
                
                // 强制刷新整个页面
                console.log('正在刷新页面...');
                window.location.reload();
            }
        })
        .catch(error => {
            // 确保在出错时也重置按钮状态
            confirmCleanBtn.disabled = false;
            cleanSpinner.classList.add('d-none');
            
            // 隐藏模态框
            cleanReportsModal.hide();
            
            alert('发生错误：' + error.message);
        });
    });
    
    // 股票代码和观察列表互斥
    symbolsInput.addEventListener('input', function() {
        if (this.value.trim()) {
            watchlistSelect.value = '';
        }
    });
    
    watchlistSelect.addEventListener('change', function() {
        if (this.value) {
            symbolsInput.value = '';
        }
    });
    
    // 加载最近报告列表
    function loadRecentReports() {
        fetch('/api/reports')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.reports && data.reports.length > 0) {
                    const recentReportsSection = document.getElementById('recentReports');
                    if (recentReportsSection) {
                        const recentReportsList = document.getElementById('recentReportsList');
                        recentReportsList.innerHTML = '';
                        
                        // 只显示最近的5个报告
                        const reportsToShow = data.reports.slice(0, 5);
                        
                        reportsToShow.forEach(report => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item d-flex justify-content-between align-items-center';
                            li.innerHTML = `
                                <span>${report.name}</span>
                                <div>
                                    <small class="text-muted me-3 report-date">${report.created}</small>
                                    <a href="${report.url}" class="btn btn-sm action-button view-report-btn" target="_blank">查看</a>
                                </div>
                            `;
                            recentReportsList.appendChild(li);
                        });
                        
                        recentReportsSection.classList.remove('d-none');
                    }
                }
            })
            .catch(error => {
                console.error('加载报告列表失败:', error);
            });
    }
    
    // 加载报告列表的函数 - 用于清理报告后刷新列表
    function loadReports() {
        // 调用loadRecentReports函数来刷新报告列表
        loadRecentReports();
    }
    
    // 页面加载时加载最近的报告列表
    loadRecentReports();
    
    // 添加关闭服务器按钮的点击事件
    document.getElementById('shutdownServerBtn').addEventListener('click', function() {
        if (confirm('确定要关闭服务器吗？这将停止所有正在进行的分析任务。')) {
            // 发送关闭服务器的请求
            fetch('/api/shutdown?real_close=true', {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/plain'
                },
                body: 'real_close=true'
            })
            .then(() => {
                alert('服务器正在关闭，此页面将关闭。');
                window.close();
                // 如果window.close()不起作用，显示一条消息
                setTimeout(() => {
                    document.body.innerHTML = '<div class="container mt-5"><div class="alert alert-success"><h4>服务器已关闭</h4><p>您可以安全地关闭此页面。</p></div></div>';
                }, 1000);
            })
            .catch(error => {
                console.error('关闭服务器时出错:', error);
                alert('关闭服务器时出错，请手动关闭终端。');
            });
        }
    });
}); 