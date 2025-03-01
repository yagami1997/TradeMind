#!/bin/bash
#
# TradeMind 时间同步检查脚本
# 版本: 1.0.0
# 
# 功能：
# 1. 自动同步NTP时间
# 2. 检查系统时间偏差
# 3. 确保使用PST时间戳
# 4. 记录时间同步日志
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

# 获取NTP服务器时间
check_ntp_time() {
    echo -e "${YELLOW}正在同步NTP时间...${NC}"
    if command -v sntp &> /dev/null; then
        sudo sntp -sS $NTP_SERVER
    elif command -v ntpdate &> /dev/null; then
        sudo ntpdate $NTP_SERVER
    else
        echo -e "${RED}错误: 未找到sntp或ntpdate命令${NC}"
        echo "请安装: sudo apt-get install ntp 或 sudo yum install ntp"
        return 1
    fi
}

# 检查PST时间
check_pst_time() {
    local pst_time=$(TZ=$TIMEZONE date "+%Y-%m-%d %H:%M:%S %Z")
    echo -e "${GREEN}当前PST时间: $pst_time${NC}"
    
    # 记录到日志
    echo "[${TIMESTAMP}] PST: ${pst_time}" >> "$LOG_FILE"
    echo "状态: 成功" >> "$LOG_FILE"
    echo "同步服务器: $NTP_SERVER" >> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"
}

# 检查时间偏差
check_time_drift() {
    local ntp_time=$(sntp -q $NTP_SERVER 2>/dev/null | grep -oP 'offset [-+]?\d+\.\d+' | awk '{print $2}')
    if [[ -n "$ntp_time" ]]; then
        if (( $(echo "$ntp_time > $MAX_DRIFT" | bc -l) )) || (( $(echo "$ntp_time < -$MAX_DRIFT" | bc -l) )); then
            echo -e "${RED}警告: 系统时间偏差超过${MAX_DRIFT}秒 (${ntp_time}s)${NC}"
            return 1
        fi
    fi
    return 0
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
    echo "=== 开始时间同步检查 ==="
    
    # 清理旧日志
    cleanup_logs
    
    # 检查NTP时间同步
    if ! check_ntp_time; then
        echo -e "${RED}❌ NTP时间同步失败${NC}"
        exit 1
    fi
    
    # 检查时间偏差
    if ! check_time_drift; then
        echo -e "${RED}❌ 时间偏差检查失败${NC}"
        exit 1
    fi
    
    # 检查并记录PST时间
    check_pst_time
    
    echo -e "${GREEN}✅ 时间同步检查通过${NC}"
    echo "=== 检查完成 ==="
}

# 执行主函数
main
