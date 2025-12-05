# ECH-worker GUI 客户端 linux版本

⚠️⚠️⚠️⚠️

仅供测试学习使用

目前仅在Archlinux ~小南梁Linux~ 上测试通过，其他发行版未测试。

整套代码由ai编写，

部分文件需要从telegram下载，如果没有telegram账号，请从release中下载

### 文件说明：
proxy_set_linux_sh.sh 从v2rayn里扒的，用于设置系统代理

ech-worker是二进制文件 从这里下载 👉 https://t.me/CF_NAT/38899 

源码是 ech-workers.go 尽量自己编译，可以在releses中下载，来自于 https://t.me/CF_NAT/38904 

ech_worker_gui.py GUI客户端,记得 授予可执行权限 `chmod +x ech_worker_gui.py`，基础运行方式 `./ech_worker_gui.py`，只支持简易分流

ech-worker.desktop 快捷启动文件，放到 ~/.local/share/applications/ 目录下

worker.js，来自于 https://t.me/CF_NAT/38899 ，可以在release中下载，作者给的代码里 token 默认为空，尽量自己修改为自己的token,部署到cloudflare worker,可以不绑定自定义域名

.ech_worker_config.json 为默认配置文件，记得修改 token 为自己的token，"l"字段为监听地址，默认是 127.0.0.1:30000


### 用法：

1. 克隆
```
git clone https://github.com/Pideo1/ECH-gui
```
2.复制
```
mkdir -p ~/.local/bin
```
```
cp ECH-gui -r ~/.local/bin && chmod +x ~/.local/bin/ECH-gui/*
```
```
cp ECH-gui/ech-worker.desktop ~/.local/share/applications/
```
3.下载ech-workers-20251201.zip,然后解压，依据系统、系统结构选择二进制文件，复制到ech_worker_gui.py所在目录，
然后改名为ech-workers

4.按下 Super键，输入 ECH,点击那个 soundcloud图标

<img width="870" height="952" alt="image" src="https://github.com/user-attachments/assets/b7642353-b558-4a74-836a-5a371c72f7ac" />

按照自身需求填写相关内容，模板已经填了，
