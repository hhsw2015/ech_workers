#!/bin/sh
# ech-wk OpenWrt 自动安装脚本，支持自动获取最新版本

REPO_OWNER="byJoey"
REPO_NAME="ech-wk"
BIN_PATH="/usr/bin/ech-workers"
TMP_DIR="/tmp/ech-workers"

# 默认配置
DEFAULT_BEST_IP="joeyblog.net"
DEFAULT_SERVER_ADDR="echo.example.com:443"
DEFAULT_LISTEN_ADDR="0.0.0.0:30001"
DEFAULT_TOKEN=""
DEFAULT_DNS="https://dns.alidns.com/dns-query"
DEFAULT_ECH_DOMAIN="cloudflare-ech.com"
DEFAULT_ROUTING="global" # 默认分流模式 global

# 更新包列表
update_package_list() {
    echo "更新 opkg 包列表..."
    opkg update || { echo "更新失败"; exit 1; }
    echo "包列表更新完成"
}

# 检查并安装缺失的依赖
install_dependencies() {
    echo "检查依赖..."
    MISSING=0

    # 检查 curl
    if ! command -v curl >/dev/null 2>&1; then
        echo "缺少 curl，正在安装..."
        opkg install curl || { echo "安装 curl 失败"; MISSING=1; }
    fi

    # 检查 tar
    if ! command -v tar >/dev/null 2>&1; then
        echo "缺少 tar，正在安装..."
        opkg install tar || { echo "安装 tar 失败"; MISSING=1; }
    fi

    # 检查 jq
    if ! command -v jq >/dev/null 2>&1; then
        echo "缺少 jq，正在安装..."
        opkg install jq || { echo "安装 jq 失败"; MISSING=1; }
    fi

    # 检查 procd
    if ! command -v procd >/dev/null 2>&1; then
        echo "缺少 procd，正在安装..."
        opkg install procd || { echo "安装 procd 失败"; MISSING=1; }
    fi

    if [ $MISSING -eq 1 ]; then
        echo "缺失依赖，请检查安装日志。"
        exit 1
    fi

    echo "依赖检查完成，所有必要的依赖已安装。"
}

# 获取最新版本的 GitHub Release 下载链接
get_latest_release_url() {
    echo "正在获取 GitHub 最新发布版本..."

    # 获取最新 release 的信息
    RELEASE_INFO=$(curl -s "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest")
    if [ $? -ne 0 ]; then
        echo "获取 release 信息失败"
        return 1
    fi

    # 获取下载链接
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name | test("linux-amd64")) | .browser_download_url')
    if [ -z "$DOWNLOAD_URL" ]; then
        echo "未找到合适的下载链接"
        return 1
    fi

    echo "下载链接: $DOWNLOAD_URL"
    echo $DOWNLOAD_URL
}

# 安装二进制文件
ensure_binary() {
    if [ -x "$BIN_PATH" ]; then
        return 0
    fi

    echo "找不到二进制: $BIN_PATH"
    echo "自动下载最新版本..."

    DOWNLOAD_URL=$(get_latest_release_url)
    if [ $? -ne 0 ]; then
        echo "下载失败！"
        return 1
    fi

    echo "开始下载..."
    mkdir -p "$(dirname "$BIN_PATH")"
    mkdir -p "$TMP_DIR"

    # 使用 curl 下载压缩包
    curl -L -o "$TMP_DIR/ech-workers.tar.gz" "$DOWNLOAD_URL" || { echo "下载失败"; return 1; }

    echo "下载完成，开始解压..."
    tar -zxvf "$TMP_DIR/ech-workers.tar.gz" -C "$TMP_DIR" || { echo "解压失败"; return 1; }

    # 假设解压后文件名是 ech-workers，请根据实际情况调整
    mv "$TMP_DIR/ech-workers" "$BIN_PATH" || { echo "安装失败"; return 1; }

    chmod +x "$BIN_PATH"
    echo "安装完成: $BIN_PATH"
}

# 确保配置文件存在
ensure_conf() {
    if [ -f "$CONF_FILE" ]; then
        return 0
    fi

    mkdir -p "$(dirname "$CONF_FILE")"
    cat >"$CONF_FILE" <<EOF
BEST_IP="$DEFAULT_BEST_IP"
SERVER_ADDR="$DEFAULT_SERVER_ADDR"
LISTEN_ADDR="$DEFAULT_LISTEN_ADDR"
TOKEN="$DEFAULT_TOKEN"
DNS="$DEFAULT_DNS"
ECH_DOMAIN="$DEFAULT_ECH_DOMAIN"
ROUTING="$DEFAULT_ROUTING"
EOF
    echo "已生成默认配置: $CONF_FILE"
}

# 启动服务
ensure_init() {
    if [ -f "$INIT_FILE" ]; then
        return 0
    fi

    cat >"$INIT_FILE" <<'EOF'
#!/bin/sh /etc/rc.common

USE_PROCD=1
START=99
STOP=10

BIN="/usr/bin/ech-workers"
CONF="/etc/ech-workers.conf"

start_service() {
    [ -x "$BIN" ] || return 1
    [ -f "$CONF" ] && . "$CONF"

    # 给一些默认值，避免变量为空
    : "${DNS:=https://dns.alidns.com/dns-query}"
    : "${ECH_DOMAIN:=cloudflare-ech.com}"
    : "${ROUTING:=global}"  # 默认分流模式为 global

    procd_open_instance
    procd_set_param command "$BIN" \
        -f "${SERVER_ADDR}" \
        -l "${LISTEN_ADDR}" \
        -token "${TOKEN}" \
        -ip "${BEST_IP}" \
        -dns "${DNS}" \
        -ech "${ECH_DOMAIN}" \
        -routing "${ROUTING}"
    procd_set_param respawn
    procd_close_instance
}
EOF

    chmod +x "$INIT_FILE"
    /etc/init.d/ech-workers enable 2>/dev/null
    echo "已创建启动脚本: $INIT_FILE 并设置开机自启"
}

# 加载配置
load_conf() {
    [ -f "$CONF_FILE" ] && . "$CONF_FILE"
}

# 保存配置
save_conf() {
    mkdir -p "$(dirname "$CONF_FILE")"
    cat >"$CONF_FILE" <<EOF
BEST_IP="${BEST_IP}"
SERVER_ADDR="${SERVER_ADDR}"
LISTEN_ADDR="${LISTEN_ADDR}"
TOKEN="${TOKEN}"
DNS="${DNS}"
ECH_DOMAIN="${ECH_DOMAIN}"
ROUTING="${ROUTING}"
EOF
}

# 菜单界面
show_menu() {
    while true; do
        clear
        ensure_conf
        load_conf

        echo "==========================="
        echo "----- 当前配置 ------------"
        echo "优选 IP      : ${BEST_IP}"
        echo "服务地址     : ${SERVER_ADDR}"
        echo "监听地址     : ${LISTEN_ADDR}"
        echo "TOKEN(身份令牌): ${TOKEN}"
        echo "DNS(可选)    : ${DNS}"
        echo "ECH 域名(可选): ${ECH_DOMAIN}"
        echo "分流模式     : ${ROUTING}"
        echo "---------------------------"
        echo "----- ech-workers 菜单 ----"
        echo "1) 修改优选 IP"
        echo "2) 修改服务地址"
        echo "3) 修改监听地址"
        echo "4) 修改 TOKEN(身份令牌)"
        echo "5) 修改分流模式"
        echo "6) 启动 ech"
        echo "7) 关闭 ech"
        echo "8) 查看日志(最近50行)"
        echo "9) 退出"
        echo "==========================="
        printf "请选择 [1-9]: "
        read -r choice

        case "$choice" in
            1)
                printf "输入新的优选 IP: "
                read -r BEST_IP
                save_conf
                ;;
            2)
                printf "输入新的服务地址 (例如 example.com:443): "
                read -r SERVER_ADDR
                save_conf
                ;;
            3)
                printf "输入新的监听地址 (例如 0.0.0.0:30002): "
                read -r LISTEN_ADDR
                save_conf
                ;;
            4)
                printf "输入新的 TOKEN(身份令牌): "
                read -r TOKEN
                save_conf
                ;;
            5)
                echo "选择分流模式："
                echo "1) global"
                echo "2) bypass_cn"
                printf "请选择 [1-2]: "
                read -r routing_choice
                if [ "$routing_choice" -eq 1 ]; then
                    ROUTING="global"
                elif [ "$routing_choice" -eq 2 ]; then
                    ROUTING="bypass_cn"
                else
                    echo "无效选择"
                fi
                save_conf
                ;;
            6)
                ensure_binary || { echo "启动失败：二进制不存在"; sleep 2; continue; }
                ensure_init
                /etc/init.d/ech-workers restart
                echo "已启动 / 重启 ech-workers"
                sleep 2
                ;;
            7)
                if [ -x "$INIT_FILE" ]; then
                    /etc/init.d/ech-workers stop
                    echo "已停止 ech-workers"
                else
                    echo "找不到 $INIT_FILE"
                fi
                sleep 2
                ;;
            8)
                echo "日志输出 (logread -e ech-workers | tail -n 50):"
                echo "----------------------------------------------"
                if command -v logread >/dev/null 2>&1; then
                    logread -e ech-workers | tail -n 50
                else
                    echo "系统没有 logread，请手动查看日志。"
                fi
                echo "----------------------------------------------"
                printf "按回车返回菜单..."
                read dummy
                ;;
            9)
                exit 0
                ;;
            *)
                echo "无效选择"
                sleep 1
                ;;
        esac
    done
}

# 入口
update_package_list   # 更新包列表
install_dependencies  # 自动安装依赖
ensure_conf
show_menu
