#!/usr/bin/env bash
# =============================================================================
# system_info.sh - Linux System Information Retrieval Script
# Smart Linux Resource Manager (SLRM)
# Author: Member 5 (Linux Integration, Alerts & Reports)
#
# Usage:
#   ./system_info.sh            # Key=Value output for Python subprocess parsing
#   ./system_info.sh --kv       # Key=Value output (default)
#   ./system_info.sh --pretty   # Human-readable formatted output
#   ./system_info.sh --json     # JSON-formatted output
# =============================================================================

set -u

get_hostname() {
    hostname 2>/dev/null || uname -n 2>/dev/null || echo "Unknown"
}

get_os_name() {
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        echo "${PRETTY_NAME:-${NAME:-Linux}}"
    elif command -v lsb_release >/dev/null 2>&1; then
        lsb_release -ds 2>/dev/null | tr -d '"'
    elif [ "$(uname -s)" = "Darwin" ]; then
        echo "macOS $(sw_vers -productVersion 2>/dev/null || echo '')"
    else
        uname -sr 2>/dev/null || echo "Linux"
    fi
}

get_kernel_version() {
    uname -r 2>/dev/null || echo "Unknown"
}

get_architecture() {
    uname -m 2>/dev/null || echo "Unknown"
}

get_uptime() {
    if uptime -p >/dev/null 2>&1; then
        uptime -p | sed 's/^up //'
    elif [ -f /proc/uptime ]; then
        awk '{
            total=int($1);
            days=int(total/86400);
            hours=int((total%86400)/3600);
            mins=int((total%3600)/60);
            if (days > 0) printf "%d days, %d hours, %d minutes\n", days, hours, mins;
            else if (hours > 0) printf "%d hours, %d minutes\n", hours, mins;
            else printf "%d minutes\n", mins;
        }' /proc/uptime
    else
        uptime 2>/dev/null | sed -E 's/^.*up +([^,]+(, *[0-9]+:[0-9]+)?),.*$/\1/' | xargs || echo "Unknown"
    fi
}

get_cpu_model() {
    local model=""
    if [ -f /proc/cpuinfo ]; then
        model="$(grep -m1 -i "model name" /proc/cpuinfo 2>/dev/null | cut -d':' -f2 | xargs)"
    fi
    if [ -z "$model" ] && command -v lscpu >/dev/null 2>&1; then
        model="$(lscpu 2>/dev/null | grep -i "Model name:" | cut -d':' -f2 | xargs)"
    fi
    if [ -z "$model" ] && [ "$(uname -s)" = "Darwin" ]; then
        model="$(sysctl -n machdep.cpu.brand_string 2>/dev/null)"
    fi
    if [ -z "$model" ]; then
        model="$(uname -p 2>/dev/null || uname -m 2>/dev/null || echo 'Generic Processor')"
    fi
    echo "$model"
}

get_cpu_cores() {
    if command -v nproc >/dev/null 2>&1; then
        nproc 2>/dev/null
    elif [ -f /proc/cpuinfo ]; then
        grep -c "^processor" /proc/cpuinfo 2>/dev/null
    elif [ "$(uname -s)" = "Darwin" ]; then
        sysctl -n hw.logicalcpu 2>/dev/null || echo "1"
    else
        echo "1"
    fi
}

get_load_average() {
    if [ -f /proc/loadavg ]; then
        awk '{print $1 ", " $2 ", " $3}' /proc/loadavg 2>/dev/null
    else
        uptime 2>/dev/null | awk -F'load averages?: ' '{print $2}' | xargs || echo "0.00, 0.00, 0.00"
    fi
}

get_total_ram() {
    if command -v free >/dev/null 2>&1; then
        free -h 2>/dev/null | awk '/^Mem:/ {print $2}'
    elif [ -f /proc/meminfo ]; then
        awk '/^MemTotal:/ {printf "%.2f GiB\n", $2 / 1048576}' /proc/meminfo
    elif [ "$(uname -s)" = "Darwin" ]; then
        sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.2f GB\n", $1 / 1073741824}'
    else
        echo "Unknown"
    fi
}

get_logged_in_user() {
    whoami 2>/dev/null || echo "${USER:-Unknown}"
}

get_active_users_count() {
    who 2>/dev/null | wc -l | xargs || echo "1"
}

get_ip_address() {
    if hostname -I >/dev/null 2>&1; then
        hostname -I 2>/dev/null | awk '{print $1}'
    elif command -v ip >/dev/null 2>&1; then
        ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -n1
    elif command -v ipconfig >/dev/null 2>&1; then
        ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1"
    else
        echo "127.0.0.1"
    fi
}

get_root_disk_summary() {
    df -h / 2>/dev/null | awk 'NR==2 {print $3 " / " $2 " (" $5 ")"}' || echo "Unknown"
}

HOSTNAME_VAL="$(get_hostname)"
OS_NAME_VAL="$(get_os_name)"
KERNEL_VAL="$(get_kernel_version)"
ARCH_VAL="$(get_architecture)"
UPTIME_VAL="$(get_uptime)"
CPU_MODEL_VAL="$(get_cpu_model)"
CPU_CORES_VAL="$(get_cpu_cores)"
LOAD_AVG_VAL="$(get_load_average)"
TOTAL_RAM_VAL="$(get_total_ram)"
USER_VAL="$(get_logged_in_user)"
ACTIVE_USERS_VAL="$(get_active_users_count)"
IP_ADDR_VAL="$(get_ip_address)"
ROOT_DISK_VAL="$(get_root_disk_summary)"
TIMESTAMP_VAL="$(date '+%Y-%m-%d %H:%M:%S')"

# Ensure non-empty values
[ -z "$CPU_MODEL_VAL" ] && CPU_MODEL_VAL="Unknown CPU"
[ -z "$IP_ADDR_VAL" ] && IP_ADDR_VAL="127.0.0.1"

MODE="${1:---kv}"

case "$MODE" in
    --pretty|-p)
        echo "============================================================"
        echo "         SMART LINUX RESOURCE MANAGER - SYSTEM INFO         "
        echo "============================================================"
        echo "Timestamp        : $TIMESTAMP_VAL"
        echo "Hostname         : $HOSTNAME_VAL"
        echo "Operating System : $OS_NAME_VAL"
        echo "Kernel Version   : $KERNEL_VAL"
        echo "Architecture     : $ARCH_VAL"
        echo "System Uptime    : $UPTIME_VAL"
        echo "CPU Model        : $CPU_MODEL_VAL"
        echo "Logical Cores    : $CPU_CORES_VAL"
        echo "Load Average     : $LOAD_AVG_VAL"
        echo "Total Memory     : $TOTAL_RAM_VAL"
        echo "Root Disk Usage  : $ROOT_DISK_VAL"
        echo "Current User     : $USER_VAL"
        echo "Logged-in Users  : $ACTIVE_USERS_VAL"
        echo "IP Address       : $IP_ADDR_VAL"
        echo "============================================================"
        ;;
    --json|-j)
        cat <<EOF
{
  "timestamp": "$TIMESTAMP_VAL",
  "hostname": "$HOSTNAME_VAL",
  "os_name": "$OS_NAME_VAL",
  "kernel": "$KERNEL_VAL",
  "architecture": "$ARCH_VAL",
  "uptime": "$UPTIME_VAL",
  "cpu_model": "$CPU_MODEL_VAL",
  "cpu_cores": "$CPU_CORES_VAL",
  "load_average": "$LOAD_AVG_VAL",
  "total_ram": "$TOTAL_RAM_VAL",
  "root_disk": "$ROOT_DISK_VAL",
  "logged_in_user": "$USER_VAL",
  "active_users": "$ACTIVE_USERS_VAL",
  "ip_address": "$IP_ADDR_VAL"
}
EOF
        ;;
    --kv|*)
        echo "TIMESTAMP=$TIMESTAMP_VAL"
        echo "HOSTNAME=$HOSTNAME_VAL"
        echo "OS_NAME=$OS_NAME_VAL"
        echo "KERNEL=$KERNEL_VAL"
        echo "ARCHITECTURE=$ARCH_VAL"
        echo "UPTIME=$UPTIME_VAL"
        echo "CPU_MODEL=$CPU_MODEL_VAL"
        echo "CPU_CORES=$CPU_CORES_VAL"
        echo "LOAD_AVERAGE=$LOAD_AVG_VAL"
        echo "TOTAL_RAM=$TOTAL_RAM_VAL"
        echo "ROOT_DISK=$ROOT_DISK_VAL"
        echo "LOGGED_IN_USER=$USER_VAL"
        echo "ACTIVE_USERS=$ACTIVE_USERS_VAL"
        echo "IP_ADDRESS=$IP_ADDR_VAL"
        ;;
esac

