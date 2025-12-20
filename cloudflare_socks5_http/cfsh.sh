#!/bin/bash
export LANG=en_US.UTF-8
arch="$(uname -m)"
case "$arch" in
x86_64|x64|amd64)   cpu=amd64 ;;
i386|i686)          cpu=386 ;;
armv8|armv8l|arm64|aarch64) cpu=arm64 ;;
armv7l)             cpu=arm ;;
mips64le)           cpu=mips64le ;;
mips64)             cpu=mips64 ;;
mips|mipsle)        cpu=mipsle ;;
*)
echo "当前架构为 $arch，暂不支持" && exit
;;
esac
INIT_SYSTEM=$(cat /proc/1/comm 2>/dev/null)
showports(){
if [ "$INIT_SYSTEM" = "systemd" ]; then
ports=$(ps aux | grep "$HOME/cfs5http/cfwp" 2>/dev/null | grep -v grep | sed -n 's/.*client_ip=:\([0-9]\+\).*/\1/p')
else
ports=$(ps w | grep "$HOME/cfs5http/cfwp" 2>/dev/null | grep -v grep | sed -n 's/.*client_ip=:\([0-9]\+\).*/\1/p')
fi
}
showmenu(){
showports
if [ -n "$ports" ]; then
echo "已在运行的节点端口："
echo "$ports" | while IFS= read -r port; do
echo "  - $port"
done
else
echo "未安装任何节点"
fi
}
delsystem(){
local port=$1
if [ "$INIT_SYSTEM" = "systemd" ]; then
systemctl stop "cf_${port}.service" >/dev/null 2>&1
systemctl disable "cf_${port}.service" >/dev/null 2>&1
rm -f "/etc/systemd/system/cf_${port}.service"
systemctl daemon-reload >/dev/null 2>&1
else
/etc/init.d/cf_$port stop >/dev/null 2>&1
/etc/init.d/cf_$port disable >/dev/null 2>&1
rm -f /etc/init.d/cf_$port
killall -9 cf_$port >/dev/null 2>&1
fi
}
echo "================================================================"
echo "甬哥Github项目 ：github.com/yonggekkk"
echo "甬哥Blogger博客 ：ygkkk.blogspot.com"
echo "甬哥YouTube频道 ：www.youtube.com/@ygkkk"
echo "================================================================"
echo "Cloudflare Socks5/Http本地代理脚本"
echo "支持：Workers域名、Pages域名、自定义域名"
echo "可选：ECH-TLS、普通TLS、无TLS 三种代理模式，应对各种阻断封杀"
echo "脚本快捷方式：bash cfsh.sh"
echo "================================================================"
echo "1、增设CF-Socks5/Http节点配置"
echo "2、查看某个节点配置信息及日志"
echo "3、删除某个节点"
echo "4、卸载删除所有配置节点"
echo "5、退出"
echo
showmenu
echo
read -p "请选择【1-5】:" menu
if [ "$menu" = "1" ]; then
mkdir -p "$HOME/cfs5http"
if [ ! -s "$HOME/cfs5http/cfwp" ]; then
curl -L -o "$HOME/cfs5http/cfwp" -# --retry 2 --insecure https://raw.githubusercontent.com/yonggekkk/Cloudflare-vless-trojan/main/s5http_wkpgs/linux-$cpu
chmod +x "$HOME/cfs5http/cfwp"
fi
echo
read -p "1、CF workers/pages/自定义的域名设置（格式为：域名:443系端口或者80系端口）:" menu
cf_domain="$menu"
echo
read -p "2、密钥设置（回车默认：不设密钥）:" menu
token="${menu:-}"
echo
read -p "3、客户端本地端口设置（回车默认：30000）:" menu
port="${menu:-30000}"
echo
read -p "4、客户端地址优选IP/域名（回车默认：yg1.ygkkk.dpdns.org）:" menu
cf_cdnip="${menu:-yg1.ygkkk.dpdns.org}"
echo
read -p "5、ProxyIP设置（回车默认：使用服务端ProxyIP）:" menu
pyip="${menu:-}"
echo
read -p "6、DoH服务器设置（回车默认：dns.alidns.com/dns-query）:" menu
dns="${menu:-dns.alidns.com/dns-query}"
echo
read -p "7、ECH开关（y=开启, n=关闭, 回车跳过：开启）:" menu
enable_ech=$([ -z "$menu" ] || [ "$menu" = y ] && echo y || echo n)
echo
read -p "8、分流开关（y=国内外分流代理, n=全局代理, 回车默认: 国内外分流代理）:" menu
cnrule=$([ -z "$menu" ] || [ "$menu" = y ] && echo y || echo n)
echo
SCRIPT="$HOME/cfs5http/cf_$port.sh"
LOG="$HOME/cfs5http/$port.log"
cat > "$SCRIPT" << EOF
#!/bin/bash
[ -f /proc/1/comm ] && INIT_SYSTEM=\$(cat /proc/1/comm)
CMD="$HOME/cfs5http/cfwp \
client_ip=:$port \
dns=$dns \
cf_domain=$cf_domain \
cf_cdnip=$cf_cdnip \
token=$token \
enable_ech=$enable_ech \
cnrule=$cnrule \
pyip=$pyip"
if [ "\$INIT_SYSTEM" = "systemd" ]; then
exec \$CMD > $LOG 2>&1
else
nohup \$CMD > "$LOG" 2>&1 &
fi
EOF
chmod +x "$SCRIPT"
if [ "$INIT_SYSTEM" = "systemd" ]; then
cat > "/etc/systemd/system/cf_$port.service" << EOF
[Unit]
Description=CF $port Service
After=network.target
[Service]
Type=simple
ExecStart=/bin/bash -c $SCRIPT
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload >/dev/null 2>&1
systemctl start "cf_$port.service" >/dev/null 2>&1
systemctl enable "cf_$port.service" >/dev/null 2>&1
elif [ "$INIT_SYSTEM" = "procd" ]; then
cat > "/etc/init.d/cf_$port" << EOF
#!/bin/sh /etc/rc.common
START=99
STOP=10
USE_PROCD=1
SCRIPT="$HOME/cfs5http/cf_$port.sh"
start_service() {
procd_open_instance
procd_set_param command /bin/sh -c "sleep 10 && /bin/bash \"$SCRIPT\""
procd_set_param respawn
procd_close_instance
}
EOF
chmod +x "/etc/init.d/cf_$port"
/etc/init.d/cf_$port start >/dev/null 2>&1
/etc/init.d/cf_$port enable >/dev/null 2>&1
else
bash "$SCRIPT"
echo "可将 /bin/bash $SCRIPT 手动设置开机自启"
fi
sleep 5 && echo "安装完毕，Socks5/Http节点已在运行中，可运行快捷方式 bash cfsh.sh 进入菜单选择2，查看节点配置信息及日志" 
echo
until grep -q '服务端域名与端口\|客户端地址与端口\|运行中的优选IP' "$HOME/cfs5http/$port.log" 2>/dev/null; do sleep 1; done; head -n 16 "$HOME/cfs5http/$port.log" 2>/dev/null | grep '服务端域名与端口\|客户端地址与端口\|运行中的优选IP'
echo
elif [ "$menu" = "2" ]; then
showmenu
echo
read -p "选择要查看的端口节点配置信息及日志（输入端口即可）:" port
{ echo "$port端口节点配置信息及日志如下：" ; echo "------------------------------------"; sed -n '1,16p' "$HOME/cfs5http/$port.log" | grep '服务端域名与端口\|客户端地址与端口\|运行中的优选IP' ; echo "------------------------------------" ; sed '1,16d' "$HOME/cfs5http/$port.log" | tail -n 10; }
echo
elif [ "$menu" = "3" ]; then
showmenu
echo
read -p "选择要删除的端口节点（输入端口即可）:" port
delsystem "$port"
pid=$(lsof -t -i :$port)
kill -9 $pid >/dev/null 2>&1
rm -rf "$HOME/cfs5http/$port.log" "$HOME/cfs5http/cf_$port.sh"
echo "端口 $port 的进程已被终止"
elif [ "$menu" = "4" ]; then
showmenu
echo
read -p "确认卸载所有节点？(y/n): " menu
if [ "$menu" != "y" ]; then
echo "已取消操作" && exit
fi
echo "$ports" | while IFS= read -r port; do
delsystem "$port"
done
ps | grep '[c]fwp' | awk '{print $1}' | xargs -r kill -9
rm -rf "$HOME/cfs5http" cfsh.sh china_ipv4.txt china_ipv6.txt
echo "所有节点已卸载完成"
else
exit
fi
