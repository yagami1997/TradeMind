# 决策记录：浏览器关闭自动停止服务器

**决策ID**: 001  
**日期**: 2025-03-14 19:53:04 PDT  
**状态**: 已实施  

## 背景

TradeMind Lite的Web模式允许用户通过浏览器界面进行股票分析。当前实现中，用户关闭浏览器后，服务器仍然继续运行，需要用户手动输入命令（按回车键，然后输入2或stop命令）来停止服务器。这种用户体验不够流畅，增加了用户的操作负担。

## 决策

实现浏览器关闭自动停止服务器的功能，使用户在关闭浏览器窗口后，服务器能够自动检测到这一事件并停止运行，然后返回到主菜单界面。

## 实施方案

1. 在前端JavaScript中添加`beforeunload`事件监听器，当用户关闭浏览器时发送关闭服务器的请求
2. 在后端Flask应用中添加`/api/shutdown`API端点，用于接收关闭请求并停止服务器
3. 修改服务器命令处理逻辑，使其能够在服务器停止时自动返回到主菜单，无需用户手动输入命令
4. 确保全局变量`server_running`在整个应用程序中可访问，以便正确控制服务器状态

## 技术细节

### 前端实现
在`trademind/ui/static/js/main.js`中添加浏览器关闭事件监听器：

```javascript
// 添加浏览器关闭事件监听器
window.addEventListener('beforeunload', function() {
    // 发送关闭服务器的请求
    navigator.sendBeacon('/api/shutdown', '');
});
```

### 后端实现
在`trademind/ui/web.py`中添加关闭服务器的API端点：

```python
@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    """
    关闭服务器API
    """
    global server_running
    try:
        # 设置服务器停止标志
        if 'server_running' in globals() and server_running is not None:
            server_running.clear()
            print("\n浏览器已关闭，服务器正在停止...")
        return jsonify({'success': True, 'message': '服务器正在关闭'})
    except Exception as e:
        logger.exception(f"关闭服务器时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
```

修改命令处理逻辑，使用非阻塞方式检查输入，并在服务器停止时自动返回主菜单：

```python
def handle_commands():
    """处理用户输入的命令"""
    while server_running.is_set():
        try:
            # 使用非阻塞的方式检查输入
            import select
            import sys
            
            # 检查是否有输入可用（非阻塞）
            ready, _, _ = select.select([sys.stdin], [], [], 1.0)  # 1秒超时
            
            # 如果有输入可用
            if ready:
                # 处理用户输入...
                
        except (EOFError, KeyboardInterrupt):
            # 处理异常...
            continue
    
    # 如果服务器停止了，自动返回到主菜单
    print("\n服务器已停止，返回主菜单...")
    return False  # 默认不重启
```

## 优势

1. 改善用户体验：用户关闭浏览器后，无需额外操作即可停止服务器
2. 资源管理：避免不必要的服务器运行，节省系统资源
3. 流程简化：减少用户操作步骤，使整个使用流程更加直观和自然

## 风险与缓解

1. **风险**：浏览器可能在某些情况下无法正确触发`beforeunload`事件
   **缓解**：保留原有的手动停止服务器的功能，作为备选方案

2. **风险**：网络请求可能在浏览器关闭过程中失败
   **缓解**：使用`navigator.sendBeacon()`方法，它专为在页面卸载期间发送数据而设计

## 结论

通过实现浏览器关闭自动停止服务器的功能，显著改善了TradeMind Lite的用户体验。用户现在可以通过简单关闭浏览器窗口来完成整个操作流程，无需额外的命令输入步骤。 