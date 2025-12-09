在hi3798mv100设备上部署了ech-workers代理服务，并且配置了systemd服务。以下是安装和设置过程的详细步骤总结：
(Ubuntu 20.04.6 LTS (GNU/Linux 4.4.35_ecoo_81112068 armv7l0
安装和设置过程
1. 获取ech-workers程序
确保你已经获得了ech-workers可执行程序，并将其放置到/usr/local/bin/目录下，并给予执行权限。

bash
# 假设ech-workers程序在当前目录
sudo cp ech-workers /usr/local/bin/
sudo chmod +x /usr/local/bin/ech-workers
2. 创建systemd服务配置文件
创建服务文件/etc/systemd/system/ech-workers.service，内容如下：

[Unit]
Description=ECH Workers Proxy Service
After=network.target

[Service]
Type=simple
User=root
# 使用阿里 DNS 避免查询失败
ExecStart=/usr/local/bin/ech-workers \
  -l 0.0.0.0:30000 \
  -f "xxxxxxxxxxx.workers.dev:443" \
  -token "xxxxxxxx" \
  -ip "xx.xx.xxx" \
  -dns "dns.alidns.com/dns-query"
Restart=on-failure  # 仅在失败时重启，而不是一直重启
RestartSec=10       # 重启间隔增加到10秒
RestartPreventExitStatus=0  # 正常退出时不重启

[Install]
WantedBy=multi-user.target


3. 重新加载systemd配置并启动服务
bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ech-workers

# 设置开机自启
sudo systemctl enable ech-workers

# 检查服务状态
sudo systemctl status ech-workers
