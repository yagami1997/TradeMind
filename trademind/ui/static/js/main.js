/**
 * TradeMind Lite - 主JavaScript文件
 */

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

    // 添加浏览器关闭事件监听器
    window.addEventListener('beforeunload', function(e) {
        // 发送关闭服务器的请求
        try {
            // 使用同步请求确保在页面关闭前发送完成
            if (navigator.sendBeacon) {
                navigator.sendBeacon('/api/shutdown', '');
            } else {
                // 备用方案：使用同步XMLHttpRequest
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/shutdown', false); // 同步请求
                xhr.send();
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
        
        // 显示加载动画
        analyzeBtn.disabled = true;
        analyzeSpinner.classList.remove('d-none');
        
        // 准备请求数据
        let symbols = [];
        let names = {};
        let title = document.getElementById('title').value || '美股技术面分析报告';
        
        if (symbolsInput.value.trim()) {
            // 处理手动输入的股票代码
            symbols = symbolsInput.value.trim().split('\n').map(line => {
                line = line.trim();
                if (line.includes('=')) {
                    const [code, name] = line.split('=', 2);
                    names[code.trim().toUpperCase()] = name.trim();
                    return code.trim().toUpperCase();
                }
                return line.toUpperCase();
            }).filter(code => code);
        } else if (watchlistSelect.value) {
            // 处理选择的观察列表
            const watchlistName = watchlistSelect.value;
            fetch(`/watchlists`)
                .then(response => response.json())
                .then(watchlists => {
                    if (watchlists[watchlistName]) {
                        symbols = Object.keys(watchlists[watchlistName]);
                        names = watchlists[watchlistName];
                        title = `${watchlistName}分析报告`;
                        sendAnalysisRequest(symbols, names, title, analyzeAll);
                    }
                });
            return; // 异步处理，提前返回
        }
        
        // 发送分析请求
        sendAnalysisRequest(symbols, names, title, analyzeAll);
    });
    
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
}); 