#!/bin/bash
#
# TradeMind 时间同步检查脚本
# 版本: 1.0.1
# 
# 功能：
# 1. 检查系统时间与NTP时间的偏差
# 2. 确保使用PST时间戳
# 3. 记录时间同步日志
#
# 使用方法：
# 1. 直接运行: ./time_check.sh
# 2. Git hook中使用: 已通过pre-commit自动调用
#
# 配置：
# 可以通过.env文件覆盖默认配置

# 加载配置文件（如果存在）
if [ -f ".env" ]; then
    source .env
fi

# 默认配置
NTP_SERVER=${NTP_SERVER:-"pool.ntp.org"}
MAX_DRIFT=${MAX_DRIFT:-1.0}
LOG_FILE=${LOG_FILE:-".time_sync.log"}
TIMEZONE=${TIMEZONE:-"America/Los_Angeles"}

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 时间戳
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# 检查时间偏差（不使用sudo）
check_time_drift() {
    # 使用timeout命令防止卡住
    local ntp_time=$(timeout 2 sntp -q $NTP_SERVER 2>/dev/null | grep -oP 'offset [-+]?\d+\.\d+' | awk '{print $2}')
    if [[ -n "$ntp_time" ]]; then
        if (( $(echo "$ntp_time > $MAX_DRIFT" | bc -l) )) || (( $(echo "$ntp_time < -$MAX_DRIFT" | bc -l) )); then
            echo -e "${YELLOW}警告: 系统时间偏差${ntp_time}秒${NC}"
            echo -e "${YELLOW}建议: 使用系统设置同步时间${NC}"
            return 0  # 继续执行，只作为警告
        fi
    fi
    return 0
}

# 检查PST时间
check_pst_time() {
    local pst_time=$(TZ=$TIMEZONE date "+%Y-%m-%d %H:%M:%S %Z")
    echo -e "${GREEN}当前PST时间: $pst_time${NC}"
    
    # 记录到日志
    echo "[${TIMESTAMP}] PST: ${pst_time}" >> "$LOG_FILE"
    echo "状态: 成功" >> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"
}

# 清理旧日志
cleanup_logs() {
    if [ -f "$LOG_FILE" ]; then
        local log_size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE")
        if [ "$log_size" -gt 1048576 ]; then  # 1MB
            echo -e "${YELLOW}正在清理旧日志...${NC}"
            tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp"
            mv "${LOG_FILE}.tmp" "$LOG_FILE"
        fi
    fi
}

# 主函数
main() {
    echo "=== 检查时间同步状态 ==="
    
    # 清理旧日志
    cleanup_logs
    
    # 检查时间偏差
    check_time_drift
    
    # 检查并记录PST时间
    check_pst_time
    
    echo -e "${GREEN}✅ 时间检查完成${NC}"
    echo "=== 检查完成 ==="
}

# 执行主函数
main
