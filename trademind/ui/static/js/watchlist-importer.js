/**
 * TradeMind Lite - 自选股导入功能
 * 
 * 本文件包含自选股导入功能的前端交互逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const importModal = document.getElementById('importWatchlistModal');
    const successModal = document.getElementById('importSuccessModal');
    const luckyButton = document.getElementById('luckyButton');
    
    // 步骤1元素
    const stockInputForm = document.getElementById('stockInputForm');
    const marketSelect = document.getElementById('marketSelect');
    const stockInput = document.getElementById('stockInput');
    const stockFile = document.getElementById('stockFile');
    const hasHeaderRow = document.getElementById('hasHeaderRow');
    const codeColumnIndex = document.getElementById('codeColumnIndex');
    const pasteFromClipboardBtn = document.getElementById('pasteFromClipboardBtn');
    const groupNameInput = document.getElementById('groupNameInput');
    const autoCategories = document.getElementById('autoCategories');
    const groupNameContainer = document.getElementById('groupNameContainer');
    const validateStocksBtn = document.getElementById('validateStocksBtn');
    const validateSpinner = document.getElementById('validateSpinner');
    
    // 步骤2元素
    const validationProgressBar = document.getElementById('validationProgressBar');
    const validationCurrentStatus = document.getElementById('validationCurrentStatus');
    const validationStats = document.getElementById('validationStats');
    const validCount = document.getElementById('validCount');
    const invalidCount = document.getElementById('invalidCount');
    const validationResultsTable = document.getElementById('validationResultsTable');
    const backToStep1Btn = document.getElementById('backToStep1Btn');
    const proceedToStep3Btn = document.getElementById('proceedToStep3Btn');
    const validStockCount = document.getElementById('validStockCount');
    
    // 步骤3元素
    const confirmGroupName = document.getElementById('confirmGroupName');
    const confirmValidCount = document.getElementById('confirmValidCount');
    const confirmInvalidCount = document.getElementById('confirmInvalidCount');
    const backToStep2Btn = document.getElementById('backToStep2Btn');
    const confirmImportBtn = document.getElementById('confirmImportBtn');
    const importSpinner = document.getElementById('importSpinner');
    
    // 成功模态框元素
    const importSuccessMessage = document.getElementById('importSuccessMessage');
    
    // 步骤标签
    const step1Tab = document.getElementById('step1-tab');
    const step2Tab = document.getElementById('step2-tab');
    const step3Tab = document.getElementById('step3-tab');
    
    // 存储验证结果
    let validationResults = [];
    
    // 初始化Bootstrap标签页
    const importStepsTabs = new bootstrap.Tab(step1Tab);
    
    // 更新进度条函数
    function updateProgressBar(current, total) {
        const percent = Math.min(Math.round((current / total) * 100), 100);
        
        // 更新自定义进度条
        const progressBar = document.querySelector('#validationProgressContainer .progress-bar');
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
            progressBar.textContent = `${percent}%`;
        }
        
        // 更新原始进度条
        if (validationProgressBar) {
            validationProgressBar.style.width = `${percent}%`;
            validationProgressBar.setAttribute('aria-valuenow', percent);
            validationProgressBar.textContent = `${percent}%`;
        }
    }
    
    // 从剪贴板粘贴
    pasteFromClipboardBtn.addEventListener('click', function() {
        navigator.clipboard.readText()
            .then(text => {
                stockInput.value = text;
            })
            .catch(err => {
                console.error('无法从剪贴板读取: ', err);
                alert('无法从剪贴板读取，请手动粘贴。');
            });
    });
    
    // 处理文件上传
    stockFile.addEventListener('change', function(e) {
        if (this.files.length === 0) return;
        
        const file = this.files[0];
        const fileType = file.name.split('.').pop().toLowerCase();
        
        // 清空文本输入框
        stockInput.value = '';
        
        // 显示文件名
        const fileNameDisplay = document.createElement('div');
        fileNameDisplay.className = 'alert alert-info mt-2';
        fileNameDisplay.innerHTML = `<i class="bi bi-file-earmark"></i> 已选择文件: <strong>${file.name}</strong>`;
        
        // 移除之前的文件名显示
        const previousFileDisplay = this.parentNode.querySelector('.alert');
        if (previousFileDisplay) {
            previousFileDisplay.remove();
        }
        
        // 添加到文件输入框后面
        this.parentNode.appendChild(fileNameDisplay);
        
        // 显示加载状态
        validateStocksBtn.disabled = true;
        validateSpinner.classList.remove('d-none');
        
        // 根据文件类型处理
        if (fileType === 'txt' || fileType === 'csv') {
            readTextFile(file);
        } else if (fileType === 'xlsx' || fileType === 'xls') {
            readExcelFile(file);
        } else {
            alert('不支持的文件格式，请上传TXT、CSV或Excel文件');
            this.value = '';
            validateStocksBtn.disabled = false;
            validateSpinner.classList.add('d-none');
        }
    });
    
    // 读取文本文件
    function readTextFile(file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const content = e.target.result;
            
            // 解析文本内容
            parseFileContent(content);
        };
        
        reader.onerror = function() {
            alert('读取文件失败');
        };
        
        reader.readAsText(file);
    }
    
    // 读取Excel文件
    function readExcelFile(file) {
        // 检查是否已加载XLSX库
        if (typeof XLSX === 'undefined') {
            // 动态加载XLSX库
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js';
            script.onload = function() {
                processExcelFile(file);
            };
            script.onerror = function() {
                alert('加载Excel处理库失败，请检查网络连接');
            };
            document.head.appendChild(script);
        } else {
            processExcelFile(file);
        }
    }
    
    // 处理Excel文件
    function processExcelFile(file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, {type: 'array'});
                
                // 获取第一个工作表
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                
                // 转换为CSV
                const csvContent = XLSX.utils.sheet_to_csv(firstSheet);
                
                // 解析CSV内容
                parseFileContent(csvContent);
            } catch (error) {
                console.error('处理Excel文件出错:', error);
                alert('处理Excel文件出错: ' + error.message);
            }
        };
        
        reader.onerror = function() {
            alert('读取Excel文件失败');
        };
        
        reader.readAsArrayBuffer(file);
    }
    
    // 解析文件内容
    function parseFileContent(content) {
        // 分割为行
        const lines = content.split('\n');
        
        // 如果有表头，跳过第一行
        const startIndex = hasHeaderRow.checked ? 1 : 0;
        
        // 获取代码列索引
        const colIndex = parseInt(codeColumnIndex.value) || 0;
        
        // 提取股票代码
        const codes = [];
        for (let i = startIndex; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            // 分割行（支持CSV格式）
            const columns = line.split(/,|;|\t/).map(col => col.trim());
            
            // 检查列索引是否有效
            if (colIndex < columns.length) {
                const code = columns[colIndex].replace(/^["']|["']$/g, '').trim();
                if (code) {
                    codes.push(code);
                }
            }
        }
        
        if (codes.length === 0) {
            alert('未能从文件中提取到有效的股票代码');
            return;
        }
        
        // 显示提取到的代码数量
        alert(`成功从文件中提取到 ${codes.length} 个股票代码`);
        
        // 将代码填入文本框，让用户可以编辑和确认
        stockInput.value = codes.join('\n');
        
        // 启用验证按钮
        validateStocksBtn.disabled = false;
        validateSpinner.classList.add('d-none');
    }
    
    // 自动分类复选框变更事件
    autoCategories.addEventListener('change', function() {
        if (this.checked) {
            // 如果选中自动分类，禁用分组名称输入
            groupNameContainer.classList.add('d-none');
            groupNameInput.disabled = true;
        } else {
            // 如果取消自动分类，启用分组名称输入
            groupNameContainer.classList.remove('d-none');
            groupNameInput.disabled = false;
        }
    });
    
    // 验证股票代码
    validateStocksBtn.addEventListener('click', function() {
        // 获取输入的股票代码
        if (!stockInput.value.trim()) {
            alert('请输入股票代码或上传文件');
            return;
        }
        
        // 显示加载动画
        validateStocksBtn.disabled = true;
        validateSpinner.classList.remove('d-none');
        
        // 从文本框获取，先解析文本
        fetch('/api/parse-stock-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: stockInput.value.trim()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 获取解析后的股票代码
                const stockCodes = data.codes;
                
                if (stockCodes.length === 0) {
                    alert('未能解析出有效的股票代码');
                    validateStocksBtn.disabled = false;
                    validateSpinner.classList.add('d-none');
                    return;
                }
                
                // 继续验证流程
                startValidation(stockCodes);
            } else {
                alert('解析股票文本失败: ' + data.error);
                validateStocksBtn.disabled = false;
                validateSpinner.classList.add('d-none');
            }
        })
        .catch(error => {
            console.error('解析股票文本出错:', error);
            alert('解析股票文本出错: ' + error.message);
            validateStocksBtn.disabled = false;
            validateSpinner.classList.add('d-none');
        });
    });
    
    // 开始验证流程
    function startValidation(stockCodes) {
        // 显示加载动画
        validateStocksBtn.disabled = true;
        validateSpinner.classList.remove('d-none');
        
        // 清空验证结果
        validationResults = [];
        validationResultsTable.innerHTML = '';
        
        // 获取验证结果区域
        const validationResultsSection = document.querySelector('.validation-results');
        if (validationResultsSection) {
            validationResultsSection.classList.remove('d-none');
        }
        
        // 移除之前的进度条和状态文本
        const existingProgressContainer = document.querySelector('#validationProgressContainer');
        const existingStatusText = document.querySelector('#validationStatusText');
        if (existingProgressContainer) existingProgressContainer.remove();
        if (existingStatusText) existingStatusText.remove();
        
        // 使用原始进度条，不创建新的
        if (validationProgressBar) {
            validationProgressBar.style.width = '0%';
            validationProgressBar.setAttribute('aria-valuenow', '0');
            validationProgressBar.textContent = '0%';
            validationProgressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        }
        
        // 使用原始状态文本
        if (validationCurrentStatus) {
            validationCurrentStatus.textContent = '正在初始化验证...';
        }
        
        // 设置验证状态变量
        window.validationInProgress = true;
        
        // 启用步骤2标签页
        const step2Tab = document.getElementById('step2-tab');
        if (step2Tab) {
            step2Tab.disabled = false;
            // 切换到步骤2
            const step2TabInstance = new bootstrap.Tab(step2Tab);
            step2TabInstance.show();
        }
        
        // 添加初始加载动画，提高用户体验
        const loadingRow = document.createElement('tr');
        loadingRow.id = 'validation-loading-row';
        loadingRow.innerHTML = `
            <td colspan="4" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">正在验证股票代码，请稍候...</p>
            </td>
        `;
        validationResultsTable.appendChild(loadingRow);
        
        // 批量验证股票代码
        setTimeout(() => {
            batchValidateStocks(stockCodes, marketSelect.value, groupNameInput.value, autoCategories.checked);
        }, 100); // 短暂延迟，让UI先渲染
        
        // 监听模态框关闭事件，停止验证过程
        importModal.addEventListener('hide.bs.modal', function() {
            if (window.validationInProgress) {
                window.validationInProgress = false;
                // 调用取消验证API
                fetch('/api/cancel-validation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('验证过程已取消:', data);
                })
                .catch(error => {
                    console.error('取消验证出错:', error);
                });
            }
        });
        
        // 监听返回按钮点击事件
        document.querySelectorAll('.btn-back').forEach(btn => {
            btn.addEventListener('click', function() {
                if (window.validationInProgress) {
                    window.validationInProgress = false;
                    // 调用取消验证API
                    fetch('/api/cancel-validation', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log('验证过程已取消:', data);
                    })
                    .catch(error => {
                        console.error('取消验证出错:', error);
                    });
                }
            });
        });
    }
    
    // 批量验证股票代码
    function batchValidateStocks(codes, market, groupName, isAutoCategories) {
        // 分批处理，每批最多20个代码
        const batchSize = 20;
        const batches = [];
        
        for (let i = 0; i < codes.length; i += batchSize) {
            batches.push(codes.slice(i, i + batchSize));
        }
        
        // 初始化进度
        let processedCount = 0;
        
        // 顺序处理每一批
        processBatch(0);
        
        function processBatch(batchIndex) {
            // 检查验证是否已取消
            if (!window.validationInProgress) {
                // 恢复按钮状态
                validateStocksBtn.disabled = false;
                validateSpinner.classList.add('d-none');
                return;
            }
            
            if (batchIndex >= batches.length) {
                // 所有批次处理完成
                validateStocksBtn.disabled = false;
                validateSpinner.classList.add('d-none');
                
                // 移除加载行
                const loadingRow = document.getElementById('validation-loading-row');
                if (loadingRow) loadingRow.remove();
                
                // 更新进度条为完成状态
                if (validationProgressBar) {
                    validationProgressBar.classList.remove('progress-bar-animated');
                    validationProgressBar.classList.add('bg-success');
                    validationProgressBar.style.width = '100%';
                    validationProgressBar.setAttribute('aria-valuenow', '100');
                    validationProgressBar.textContent = '100%';
                }
                
                // 更新状态文本
                if (validationCurrentStatus) {
                    validationCurrentStatus.textContent = '验证完成！';
                }
                
                // 更新统计信息
                const validStocks = validationResults.filter(r => r.valid);
                validCount.textContent = `${validStocks.length} 有效`;
                invalidCount.textContent = `${validationResults.length - validStocks.length} 无效`;
                validStockCount.textContent = `(${validStocks.length})`;
                
                // 更新步骤3的确认信息
                if (confirmGroupName) confirmGroupName.textContent = isAutoCategories ? '自动分类' : groupName;
                if (confirmValidCount) confirmValidCount.textContent = validStocks.length;
                if (confirmInvalidCount) confirmInvalidCount.textContent = validationResults.length - validStocks.length;
                
                // 如果没有有效股票，禁用继续按钮
                if (proceedToStep3Btn) proceedToStep3Btn.disabled = validStocks.length === 0;
                
                // 标记验证已完成
                window.validationInProgress = false;
                
                return;
            }
            
            const batch = batches[batchIndex];
            
            // 更新当前状态
            if (validationCurrentStatus) {
                validationCurrentStatus.textContent = `正在验证第 ${processedCount + 1} 到 ${processedCount + batch.length} 个股票代码...`;
            }
            
            // 发送请求验证当前批次
            fetch('/api/validate-stocks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    codes: batch,
                    market: market,
                    translate: true // 请求翻译名称
                })
            })
            .then(response => response.json())
            .then(data => {
                // 检查验证是否已取消
                if (!window.validationInProgress) return;
                
                // 移除加载行
                const loadingRow = document.getElementById('validation-loading-row');
                if (loadingRow) loadingRow.remove();
                
                if (data.results) {
                    // 处理验证结果
                    processedCount += batch.length;
                    
                    // 更新进度条
                    updateProgressBar(processedCount, codes.length);
                    
                    // 更新统计信息
                    if (validationStats) {
                        validationStats.textContent = `${processedCount}/${codes.length}`;
                    }
                    
                    // 添加结果到表格
                    data.results.forEach(result => {
                        validationResults.push(result);
                        addResultToTable(result);
                    });
                    
                    // 处理下一批
                    setTimeout(() => {
                        processBatch(batchIndex + 1);
                    }, 300);
                } else {
                    // 显示友好的错误消息
                    const errorMsg = data.error || '未知错误';
                    console.error('验证股票代码失败:', errorMsg);
                    
                    // 添加错误提示行
                    const errorRow = document.createElement('tr');
                    errorRow.classList.add('table-warning');
                    errorRow.innerHTML = `
                        <td colspan="4" class="text-center">
                            <div class="alert alert-warning mb-0">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                验证部分股票代码时遇到问题，请重试或联系管理员
                            </div>
                        </td>
                    `;
                    validationResultsTable.appendChild(errorRow);
                    
                    validateStocksBtn.disabled = false;
                    validateSpinner.classList.add('d-none');
                    window.validationInProgress = false;
                }
            })
            .catch(error => {
                console.error('验证股票代码出错:', error);
                
                // 移除加载行
                const loadingRow = document.getElementById('validation-loading-row');
                if (loadingRow) loadingRow.remove();
                
                // 添加错误提示行，显示友好的错误消息
                const errorRow = document.createElement('tr');
                errorRow.classList.add('table-danger');
                errorRow.innerHTML = `
                    <td colspan="4" class="text-center">
                        <div class="alert alert-danger mb-0">
                            <i class="bi bi-x-circle-fill me-2"></i>
                            验证过程中出现错误，请稍后重试
                        </div>
                    </td>
                `;
                validationResultsTable.appendChild(errorRow);
                
                validateStocksBtn.disabled = false;
                validateSpinner.classList.add('d-none');
                window.validationInProgress = false;
            });
        }
    }
    
    // 添加验证结果到表格
    function addResultToTable(result) {
        const row = document.createElement('tr');
        
        // 设置行的类，根据验证结果
        if (result.valid) {
            row.classList.add('table-success');
        } else {
            row.classList.add('table-danger');
        }
        
        // 原始代码
        const originalCell = document.createElement('td');
        originalCell.textContent = result.original;
        row.appendChild(originalCell);
        
        // 转换后代码
        const convertedCell = document.createElement('td');
        convertedCell.textContent = result.valid ? result.converted : '-';
        row.appendChild(convertedCell);
        
        // 名称
        const nameCell = document.createElement('td');
        if (result.valid) {
            // 显示中文名称（如果有）和英文名称
            if (result.chineseName) {
                nameCell.innerHTML = `<span class="fw-bold">${result.chineseName}</span>`;
                if (result.name && result.name !== result.chineseName) {
                    nameCell.innerHTML += `<br><small class="text-muted">${result.name}</small>`;
                }
            } else {
                nameCell.textContent = result.name || '-';
            }
        } else {
            nameCell.textContent = '-';
        }
        row.appendChild(nameCell);
        
        // 状态
        const statusCell = document.createElement('td');
        if (result.valid) {
            let statusHtml = '<span class="badge bg-success">有效</span>';
            if (result.category) {
                statusHtml += ` <small class="text-muted">${result.category}</small>`;
            }
            statusCell.innerHTML = statusHtml;
        } else {
            let reason = result.reason || '未知原因';
            
            // 处理特殊错误情况
            if (reason.includes("'NoneType' object has no attribute")) {
                reason = '服务器处理错误';
            } else if (reason.includes('期货') || reason.includes('指数') || 
                reason.includes('不支持') || reason.includes('无效市场')) {
                statusCell.innerHTML = `<span class="badge bg-danger">无效</span> <strong class="text-danger">${reason}</strong>`;
                row.appendChild(statusCell);
                validationResultsTable.appendChild(row);
                return;
            }
            
            statusCell.innerHTML = `<span class="badge bg-danger">无效</span> <small>${reason}</small>`;
        }
        row.appendChild(statusCell);
        
        // 添加到表格
        validationResultsTable.appendChild(row);
    }
    
    // 返回步骤1
    backToStep1Btn.addEventListener('click', function() {
        const step1TabInstance = new bootstrap.Tab(step1Tab);
        step1TabInstance.show();
    });
    
    // 进入步骤3
    proceedToStep3Btn.addEventListener('click', function() {
        // 启用步骤3标签页
        step3Tab.disabled = false;
        
        // 切换到步骤3
        const step3TabInstance = new bootstrap.Tab(step3Tab);
        step3TabInstance.show();
    });
    
    // 返回步骤2
    backToStep2Btn.addEventListener('click', function() {
        const step2TabInstance = new bootstrap.Tab(step2Tab);
        step2TabInstance.show();
    });
    
    // 确认导入
    confirmImportBtn.addEventListener('click', function() {
        // 检查元素是否存在
        if (!confirmImportBtn || !importSpinner) {
            console.error('导入按钮或加载动画元素不存在');
            return;
        }
        
        // 显示加载状态
        confirmImportBtn.disabled = true;
        importSpinner.classList.remove('d-none');
        
        // 获取有效的股票
        const validStocks = validationResults.filter(r => r.valid);
        const isAutoCategories = autoCategories && autoCategories.checked;
        const groupNameValue = groupNameInput ? groupNameInput.value.trim() : '';
        
        // 发送请求导入自选股
        fetch('/api/import-watchlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stocks: validStocks,
                groupName: isAutoCategories ? '' : groupNameValue,
                autoCategories: isAutoCategories
            })
        })
        .then(response => response.json())
        .then(data => {
            if (confirmImportBtn) confirmImportBtn.disabled = false;
            if (importSpinner) importSpinner.classList.add('d-none');
            
            if (data.success) {
                // 关闭导入模态框
                if (importModal) {
                    const importModalInstance = bootstrap.Modal.getInstance(importModal);
                    if (importModalInstance) importModalInstance.hide();
                }
                
                // 显示成功消息
                if (importSuccessMessage) {
                    importSuccessMessage.textContent = data.message;
                }
                
                // 显示成功模态框
                if (successModal) {
                    const successModalInstance = new bootstrap.Modal(successModal);
                    successModalInstance.show();
                }
                
                // 重置表单
                resetImportForm();
                
                // 刷新观察列表下拉菜单
                refreshWatchlistDropdown(data.watchlists);
            } else {
                // 显示友好的错误消息
                const errorMsg = data.error || '未知错误';
                console.error('导入自选股失败:', errorMsg);
                
                // 使用更友好的错误提示
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger mt-3';
                errorAlert.innerHTML = `
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    导入失败: ${errorMsg}
                `;
                
                // 添加到确认区域
                const confirmArea = document.querySelector('.step-3-content');
                if (confirmArea) {
                    // 移除之前的错误提示
                    const previousError = confirmArea.querySelector('.alert-danger');
                    if (previousError) previousError.remove();
                    
                    confirmArea.appendChild(errorAlert);
                } else {
                    // 如果找不到确认区域，使用alert
                    alert('导入自选股失败: ' + errorMsg);
                }
            }
        })
        .catch(error => {
            console.error('导入自选股出错:', error);
            
            // 恢复按钮状态
            if (confirmImportBtn) confirmImportBtn.disabled = false;
            if (importSpinner) importSpinner.classList.add('d-none');
            
            // 使用更友好的错误提示
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger mt-3';
            errorAlert.innerHTML = `
                <i class="bi bi-x-circle-fill me-2"></i>
                导入过程中出现错误，请稍后重试
            `;
            
            // 添加到确认区域
            const confirmArea = document.querySelector('.step-3-content');
            if (confirmArea) {
                // 移除之前的错误提示
                const previousError = confirmArea.querySelector('.alert-danger');
                if (previousError) previousError.remove();
                
                confirmArea.appendChild(errorAlert);
            } else {
                // 如果找不到确认区域，使用alert
                alert('导入自选股出错，请稍后重试');
            }
        });
    });
    
    // 刷新观察列表下拉菜单
    function refreshWatchlistDropdown(watchlists) {
        const watchlistSelect = document.getElementById('watchlist');
        if (!watchlistSelect) return;
        
        // 保存当前选中的值
        const selectedValue = watchlistSelect.value;
        
        // 清空下拉菜单，只保留第一个选项
        while (watchlistSelect.options.length > 1) {
            watchlistSelect.remove(1);
        }
        
        // 添加新的选项
        for (const groupName in watchlists) {
            const option = document.createElement('option');
            option.value = groupName;
            option.textContent = `${groupName} (${Object.keys(watchlists[groupName]).length}个股票)`;
            watchlistSelect.appendChild(option);
        }
        
        // 恢复之前选中的值
        if (selectedValue && Array.from(watchlistSelect.options).some(opt => opt.value === selectedValue)) {
            watchlistSelect.value = selectedValue;
        }
    }
    
    // 重置导入表单
    function resetImportForm() {
        // 重置步骤显示
        const steps = document.querySelectorAll('.import-step');
        if (steps && steps.length) {
            steps.forEach(step => {
                if (step.classList.contains('step-1')) {
                    step.classList.remove('d-none');
                } else {
                    step.classList.add('d-none');
                }
            });
        }
        
        // 重置输入框
        if (stockInput) stockInput.value = '';
        if (groupNameInput) groupNameInput.value = '';
        
        // 重置自动分类选项
        if (autoCategories) autoCategories.checked = false;
        if (groupNameContainer) groupNameContainer.classList.remove('d-none');
        
        // 重置验证结果
        validationResults = [];
        
        // 清空验证结果表格
        if (validationResultsTable) {
            const tbody = validationResultsTable.querySelector('tbody');
            if (tbody) tbody.innerHTML = '';
        }
        
        // 重置进度条
        if (validationProgressBar) {
            validationProgressBar.style.width = '0%';
            validationProgressBar.setAttribute('aria-valuenow', '0');
        }
        
        // 重置状态文本
        if (validationCurrentStatus) validationCurrentStatus.textContent = '';
        
        // 隐藏验证结果区域
        const validationResultsArea = document.querySelector('.validation-results');
        if (validationResultsArea) validationResultsArea.classList.add('d-none');
        
        // 重置按钮状态
        if (validateStocksBtn) {
            validateStocksBtn.disabled = false;
            validateStocksBtn.textContent = '验证股票代码';
        }
        
        if (validateSpinner) validateSpinner.classList.add('d-none');
        
        // 重置文件上传
        if (stockFile) stockFile.value = '';
        
        // 移除文件名显示
        const fileNameDisplay = document.querySelector('.file-name-display');
        if (fileNameDisplay) fileNameDisplay.remove();
        
        // 重置导入确认按钮
        if (confirmImportBtn) confirmImportBtn.disabled = false;
        if (importSpinner) importSpinner.classList.add('d-none');
        
        // 重置统计信息
        if (validCount) validCount.textContent = '0 有效';
        if (invalidCount) invalidCount.textContent = '0 无效';
        if (validStockCount) validStockCount.textContent = '(0)';
        
        // 移除任何错误提示
        const errorAlerts = document.querySelectorAll('.alert-danger');
        if (errorAlerts && errorAlerts.length) {
            errorAlerts.forEach(alert => alert.remove());
        }
        
        console.log('导入表单已重置');
    }
    
    // 导入模态框关闭时重置表单
    importModal.addEventListener('hidden.bs.modal', function() {
        resetImportForm();
    });

    // "手气不错"功能 - 自动整理自选股列表
    luckyButton.addEventListener('click', function() {
        // 显示加载状态
        luckyButton.disabled = true;
        luckyButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 正在整理...';
        
        // 显示进度区域
        const progressContainer = document.getElementById('luckyProgressContainer');
        const progressBar = document.getElementById('luckyProgressBar');
        const statusText = document.getElementById('luckyStatusText');
        progressContainer.classList.remove('d-none');
        
        // 设置初始进度
        updateLuckyProgress(5, '正在读取自选股列表...');
        
        // 设置进度轮询
        let progressInterval = setInterval(function() {
            fetch('/api/auto-organize-progress')
                .then(response => response.json())
                .then(data => {
                    if (data.in_progress) {
                        updateLuckyProgress(data.percent, data.status);
                    } else if (data.completed) {
                        // 停止轮询
                        clearInterval(progressInterval);
                        
                        // 设置为100%
                        updateLuckyProgress(100, '整理完成！');
                    }
                })
                .catch(error => {
                    console.error('获取进度失败:', error);
                });
        }, 1000);
        
        // 发送请求到后端
        fetch('/api/auto-organize-watchlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // 停止进度轮询
            clearInterval(progressInterval);
            
            // 恢复按钮状态
            luckyButton.disabled = false;
            luckyButton.innerHTML = '<i class="bi bi-magic"></i> 手气不错 - 自动整理自选股列表';
            
            // 隐藏进度区域
            progressContainer.classList.add('d-none');
            
            if (data.success) {
                // 关闭导入模态框
                const importModalInstance = bootstrap.Modal.getInstance(importModal);
                importModalInstance.hide();
                
                // 显示成功消息
                importSuccessMessage.innerHTML = `
                    <p>${data.message}</p>
                    <div class="alert alert-success">
                        <ul>
                            <li>整理分组: ${data.stats.groups}个</li>
                            <li>验证股票: ${data.stats.stocks}个</li>
                            <li>翻译名称: ${data.stats.translated}个</li>
                            <li>修复无效: ${data.stats.fixed}个</li>
                        </ul>
                    </div>
                `;
                
                // 显示成功模态框
                const successModalInstance = new bootstrap.Modal(successModal);
                successModalInstance.show();
                
                // 刷新观察列表下拉菜单
                refreshWatchlistDropdown(data.watchlists);
            } else {
                alert('自动整理自选股列表失败: ' + data.error);
            }
        })
        .catch(error => {
            // 停止进度轮询
            clearInterval(progressInterval);
            
            // 隐藏进度区域
            progressContainer.classList.add('d-none');
            
            console.error('自动整理自选股列表出错:', error);
            alert('自动整理自选股列表出错: ' + error.message);
            luckyButton.disabled = false;
            luckyButton.innerHTML = '<i class="bi bi-magic"></i> 手气不错 - 自动整理自选股列表';
        });
    });
    
    // 更新"手气不错"进度条
    function updateLuckyProgress(percent, status) {
        const progressBar = document.getElementById('luckyProgressBar');
        const statusText = document.getElementById('luckyStatusText');
        const animatedText = document.getElementById('luckyAnimatedText');
        
        // 更新进度条
        percent = Math.min(Math.round(percent), 100);
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressBar.textContent = `${percent}%`;
        
        // 更新状态文本
        statusText.textContent = status;
        
        // 根据进度阶段更新样式和提示信息
        if (percent >= 100) {
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-success');
            statusText.classList.remove('alert-info');
            statusText.classList.add('alert-success');
            statusText.textContent = '整理完成！所有股票已成功分类并保存。';
            
            // 隐藏动画文本
            animatedText.classList.add('d-none');
        } else if (percent >= 85) {
            statusText.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> 验证完成！正在写入文件并更新配置...';
            updateAnimatedText('即将完成，正在保存结果...');
        } else if (percent >= 65) {
            statusText.innerHTML = '<i class="bi bi-diagram-3-fill me-1"></i> 正在智能分类股票到不同分组...';
            updateAnimatedText('正在对股票进行智能分类，这需要一点时间...');
        } else if (percent >= 40) {
            // 为验证阶段添加更多变化的提示
            const verifyMessages = [
                '正在验证股票代码有效性...',
                '正在查询股票信息和最新数据...',
                '正在翻译股票名称为中文...',
                '正在修复无效的股票代码...',
                '正在处理特殊格式的股票代码...'
            ];
            
            // 根据进度选择不同的消息
            const messageIndex = Math.floor((percent - 20) / 5) % verifyMessages.length;
            statusText.innerHTML = `<i class="bi bi-search me-1"></i> ${verifyMessages[messageIndex]}`;
            
            // 添加动态效果
            updateAnimatedText('正在处理数据，请不要关闭窗口...');
        } else if (percent >= 20) {
            statusText.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> 正在批量验证股票代码，这可能需要一点时间...';
            updateAnimatedText('系统正在验证每个股票代码，请耐心等待...');
        } else if (percent >= 10) {
            statusText.innerHTML = '<i class="bi bi-file-earmark-text me-1"></i> 正在读取和解析股票数据...';
            updateAnimatedText('正在读取数据，请稍候...');
        } else {
            statusText.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> 正在初始化整理过程...';
            updateAnimatedText('系统正在准备中...');
        }
    }
    
    // 更新动画文本
    function updateAnimatedText(message) {
        const animatedText = document.getElementById('luckyAnimatedText');
        if (!animatedText) return;
        
        // 显示动画文本
        animatedText.classList.remove('d-none');
        
        // 更新文本内容
        const textSpan = animatedText.querySelector('span');
        if (textSpan) {
            textSpan.textContent = message;
        }
        
        // 随机改变动画颜色
        const spinners = animatedText.querySelectorAll('.spinner-grow');
        const colors = ['text-primary', 'text-success', 'text-info', 'text-warning'];
        
        spinners.forEach(spinner => {
            // 移除所有颜色类
            colors.forEach(color => {
                spinner.classList.remove(color);
            });
            
            // 添加随机颜色
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            spinner.classList.add(randomColor);
        });
    }
}); 