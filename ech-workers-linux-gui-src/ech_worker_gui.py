#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import subprocess
import os
import sys
import threading
import signal
import json
import time
import requests
from io import StringIO

# 设置编码
sys.stdout = StringIO()

# 这行代码会将StringIO设置回原始的标准输出
sys.stdout = sys.__stdout__

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class ECHWorkerGUI(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="ECH Worker GUI")
        
        # 设置窗口初始大小，不设置最大大小限制，让窗口可以自由伸缩
        self.set_default_size(700, 500)  # 增大初始大小以容纳日志窗口
        self.set_border_width(20)
        
        # 存储当前运行的进程
        self.running_process = None
        self.process_thread = None
        
        # 代理设置状态
        self.proxy_set = False
        
        # 延迟测试定时器
        self.latency_timer = None
        
        # 配置文件目录 - 程序所在目录
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.current_config_name = "默认配置"  # 默认配置名称
        
        # 创建主布局
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.add(main_box)
        
        # 创建配置文件管理区域
        config_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(config_box, False, True, 0)
        
        # 配置文件选择标签
        config_label = Gtk.Label(label="配置文件:")
        config_box.pack_start(config_label, False, False, 0)
        
        # 配置文件选择下拉框
        self.config_combo = Gtk.ComboBoxText()
        self.config_combo.set_entry_text_column(0)
        config_box.pack_start(self.config_combo, True, True, 0)
        
        # 保存为新配置按钮
        self.save_as_button = Gtk.Button(label="保存为...")
        self.save_as_button.connect("clicked", self.on_save_as_clicked)
        config_box.pack_start(self.save_as_button, False, False, 0)
        
        # 删除配置按钮
        self.delete_config_button = Gtk.Button(label="删除配置")
        self.delete_config_button.connect("clicked", self.on_delete_config_clicked)
        config_box.pack_start(self.delete_config_button, False, False, 0)
        
        # 创建内容框
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.pack_start(content_box, False, True, 0)  # 不垂直扩展，让日志窗口占据更多空间
        
        # 创建网格布局来排列标签和输入框
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        content_box.pack_start(grid, False, True, 0)  # 允许水平填充但不垂直扩展
        
        # 存储输入框的字典
        self.entries = {}
        
        # 配置项列表
        configs = [
            {"key": "dns", "label": "ECH 查询 DoH 服务器", "default": "doh.onedns.net/dns-query", "required": False},
            {"key": "ech", "label": "ECH 查询域名", "default": "cloudflare-ech.com", "required": False},
            {"key": "f", "label": "服务端地址", "default": "", "required": True},
            {"key": "ip", "label": "指定服务端 IP", "default": "", "required": True},
            {"key": "l", "label": "代理监听地址", "default": "127.0.0.1:30000", "required": False},
            {"key": "token", "label": "身份验证令牌", "default": "", "required": False},
            {"key": "ignore_hosts", "label": "忽略的主机", "default": "localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12", "required": False}
        ]
        
        # 创建标签和输入框
        for i, config in enumerate(configs):
            # 创建标签
            label_text = config["label"]
            if config["required"]:
                # 创建带有红色星号的标签
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                label = Gtk.Label(label=label_text)
                label.set_halign(Gtk.Align.START)  # 左对齐标签
                required_mark = Gtk.Label(label="*")
                # 使用CSS样式替代已弃用的override_color方法
                css_provider = Gtk.CssProvider()
                css_provider.load_from_data(b"* { color: #ff0000; }")
                required_mark.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                hbox.pack_start(label, False, False, 0)
                hbox.pack_start(required_mark, False, False, 0)
                grid.attach(hbox, 0, i, 1, 1)
            else:
                label = Gtk.Label(label=label_text)
                label.set_halign(Gtk.Align.START)  # 左对齐标签
                grid.attach(label, 0, i, 1, 1)
            
            # 创建输入框
            entry = Gtk.Entry()
            entry.set_hexpand(True)  # 允许输入框水平扩展
            entry.set_halign(Gtk.Align.FILL)  # 填充可用空间
            
            # 如果是ignore_hosts配置项，设置占位文本
            if config["key"] == "ignore_hosts":
                entry.set_placeholder_text("使用逗号作为分隔")
            
            grid.attach(entry, 1, i, 1, 1)
            # 修复：将这一行移到循环内部，确保每个配置项都被添加到entries字典中
            self.entries[config["key"]] = entry
        
        # 创建按钮框
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_homogeneous(True)  # 按钮均匀分布
        content_box.pack_start(button_box, False, True, 0)  # 允许水平填充但不垂直扩展
        
        # 创建启动按钮
        self.start_button = Gtk.Button(label="启动服务")
        self.start_button.connect("clicked", self.on_start_clicked)
        button_box.pack_start(self.start_button, True, True, 0)
        # 创建停止按钮
        self.stop_button = Gtk.Button(label="停止服务")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        self.stop_button.set_sensitive(False)  # 初始状态为禁用
        button_box.pack_start(self.stop_button, True, True, 0)
        
        # 创建代理管理按钮（合并了设置和清除功能）
        self.proxy_button = Gtk.Button(label="设置为系统代理")
        self.proxy_button.connect("clicked", self.on_proxy_button_clicked)
        button_box.pack_start(self.proxy_button, True, True, 0)
        
        # 创建退出按钮
        self.exit_button = Gtk.Button(label="退出")
        self.exit_button.connect("clicked", Gtk.main_quit)
        button_box.pack_start(self.exit_button, True, True, 0)
        
        # 创建状态标签
        self.status_label = Gtk.Label(label="就绪")
        self.status_label.set_halign(Gtk.Align.START)  # 左对齐状态标签
        content_box.pack_start(self.status_label, False, True, 0)  # 允许水平填充但不垂直扩展
        
        # 添加日志窗口标签
        log_label = Gtk.Label(label="程序日志")
        log_label.set_halign(Gtk.Align.START)
        main_box.pack_start(log_label, False, True, 0)
        
        # 创建日志窗口 - 使用ScrolledWindow和TextView
        self.log_scrolled_window = Gtk.ScrolledWindow()
        self.log_scrolled_window.set_hexpand(True)
        self.log_scrolled_window.set_vexpand(True)
        self.log_scrolled_window.set_min_content_height(200)  # 设置最小高度
        main_box.pack_start(self.log_scrolled_window, True, True, 0)  # 允许扩展和填充
        
        # 创建文本视图用于显示日志
        self.log_textview = Gtk.TextView()
        self.log_textview.set_editable(False)  # 只读
        self.log_textview.set_wrap_mode(Gtk.WrapMode.CHAR)  # 字符换行
        self.log_scrolled_window.add(self.log_textview)
        
        # 获取文本缓冲区
        self.log_buffer = self.log_textview.get_buffer()
        
        # 加载配置文件列表
        self.load_config_files()
        
        # 应用保存的配置到输入框并连接事件
        for config in configs:
            key = config["key"]
            self.entries[key].connect("changed", self.on_entry_changed, key)
        
        # 连接配置选择变化事件
        self.config_combo.connect("changed", self.on_config_changed)
        
        # 检查可执行文件是否存在
        self.executable_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ech-workers")
        if not os.path.isfile(self.executable_path) or not os.access(self.executable_path, os.X_OK):
            self.status_label.set_text("错误: 找不到可执行文件 ech-workers")
            self.status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 0, 0, 1))  # 红色
            self.start_button.set_sensitive(False)
            self.append_log("错误: 找不到可执行文件 ech-workers")
        else:
            self.append_log("程序初始化完成，可执行文件已找到")
    
    def get_config_file_path(self, config_name):
        """获取配置文件路径"""
        if config_name == "默认配置":
            return os.path.join(self.config_dir, ".ech_worker_config.json")
        else:
            # 移除可能的特殊字符，确保文件名安全
            safe_name = "".join(c for c in config_name if c.isalnum() or c in "_- ").strip()
            return os.path.join(self.config_dir, f".ech_worker_{safe_name}.json")
    
    def load_config_files(self):
        """加载并显示所有可用的配置文件"""
        self.config_combo.remove_all()
        self.config_combo.append_text("默认配置")
        
        # 搜索配置文件
        config_files = []
        for filename in os.listdir(self.config_dir):
            if filename.startswith(".ech_worker_") and filename.endswith(".json") and filename != ".ech_worker_config.json":
                # 提取配置名称
                config_name = filename[len(".ech_worker_"):-len(".json")].strip()
                if config_name:
                    config_files.append(config_name)
        
        # 按名称排序并添加到下拉框
        for config_name in sorted(config_files):
            self.config_combo.append_text(config_name)
        
        # 设置默认选择
        self.config_combo.set_active(0)
        self.current_config_name = "默认配置"
        self.load_config("默认配置")
    
    def load_config(self, config_name):
        """加载指定名称的配置"""
        config_file = self.get_config_file_path(config_name)
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 应用配置到输入框
                for key, entry in self.entries.items():
                    if key in config:
                        entry.set_text(config[key])
                    else:
                        # 保留默认值
                        pass
                
                self.append_log(f"已加载配置: {config_name}")
        except Exception as e:
            self.append_log(f"加载配置 '{config_name}' 失败: {str(e)}")
    
    def save_config(self, config_name=None):
        """保存当前配置到指定名称的文件"""
        if config_name is None:
            config_name = self.current_config_name
        
        config_file = self.get_config_file_path(config_name)
        try:
            config = {}
            for key, entry in self.entries.items():
                config[key] = entry.get_text().strip()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.append_log(f"配置 '{config_name}' 已保存")
            
            # 如果是新配置，刷新配置列表
            if config_name != self.current_config_name:
                self.load_config_files()
                # 选择新保存的配置
                for i, item in enumerate(self.config_combo):
                    if item == config_name:
                        self.config_combo.set_active(i)
                        break
        except Exception as e:
            self.append_log(f"保存配置 '{config_name}' 失败: {str(e)}")
    
    def on_entry_changed(self, widget, key):
        """输入框内容变化时自动保存当前配置"""
        self.save_config()
    
    def on_config_changed(self, widget):
        """配置选择变化时加载选中的配置"""
        # 获取选中的配置名称
        active_text = self.config_combo.get_active_text()
        if active_text:
            # 保存当前配置
            self.save_config(self.current_config_name)
            # 加载新选择的配置
            self.current_config_name = active_text
            self.load_config(active_text)
    
    def on_save_as_clicked(self, widget):
        """保存为新配置"""
        # 创建对话框
        dialog = Gtk.Dialog(
            title="保存为新配置",
            transient_for=self,
            flags=0,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        
        # 添加输入框
        box = dialog.get_content_area()
        box.set_border_width(10)
        label = Gtk.Label(label="请输入配置名称:")
        box.pack_start(label, False, False, 0)
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("例如: 公司配置")
        box.pack_start(entry, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            config_name = entry.get_text().strip()
            if config_name:
                if config_name == "默认配置":
                    # 已经存在默认配置，直接保存到默认配置
                    self.save_config("默认配置")
                else:
                    # 保存为新配置
                    self.save_config(config_name)
            else:
                self.append_log("错误: 配置名称不能为空")
        
        dialog.destroy()
    
    def on_delete_config_clicked(self, widget):
        """删除当前选中的配置"""
        # 不能删除默认配置
        if self.current_config_name == "默认配置":
            self.append_log("错误: 无法删除默认配置")
            return
        
        # 确认对话框
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"确认删除配置 '{self.current_config_name}'?"
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            config_file = self.get_config_file_path(self.current_config_name)
            try:
                if os.path.exists(config_file):
                    os.remove(config_file)
                self.append_log(f"配置 '{self.current_config_name}' 已删除")
                
            # 重新加载配置列表
                self.load_config_files()
            except Exception as e:
                self.append_log(f"删除配置失败: {str(e)}")
        
        dialog.destroy()
    
    def append_log(self, message):
        """在日志窗口中添加一条消息，最多保留20行"""
        # 获取当前时间
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # 添加到缓冲区
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, log_message)
        
        # 限制日志行数不超过20行
        text = self.log_buffer.get_text(self.log_buffer.get_start_iter(), end_iter, True)
        lines = text.split('\n')
        if len(lines) > 20:
            # 只保留最后20行
            new_text = '\n'.join(lines[-20:])
            self.log_buffer.set_text(new_text)
        
        # 滚动到底部
        self.log_textview.scroll_mark_onscreen(self.log_buffer.get_insert())
    
    def set_label_color(self, label, color_hex):
        """使用CSS设置标签颜色"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(f"* {{ color: {color_hex}; }}".encode())
        label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def update_ui_state(self, is_running):
        """更新UI组件的状态"""
        self.start_button.set_sensitive(not is_running)
        self.stop_button.set_sensitive(is_running)
        
        # 禁用或启用输入框和配置管理控件
        for entry in self.entries.values():
            entry.set_sensitive(not is_running)
        
        # 服务运行时禁用配置管理
        self.config_combo.set_sensitive(not is_running)
        self.save_as_button.set_sensitive(not is_running)
        self.delete_config_button.set_sensitive(not is_running)
    
    def clear_env_proxy(self):
        """清除环境变量中的代理设置"""
        # 定义要清除的代理相关环境变量
        proxy_vars = [
            'http_proxy', 'https_proxy', 'ftp_proxy', 
            'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY',
            'all_proxy', 'ALL_PROXY',
            'no_proxy', 'NO_PROXY'
        ]
        
        # 清除这些环境变量
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]
                self.append_log(f"已清除环境变量: {var}")
        
        self.append_log("已清除环境变量中的代理设置")

    def on_start_clicked(self, widget):
        # 清除环境变量中的代理设置
        self.clear_env_proxy()
        
        # 检查必填项
        if not self.entries["f"].get_text().strip() or not self.entries["ip"].get_text().strip():
            self.status_label.set_text("错误: 请填写所有必填项")
            self.set_label_color(self.status_label, "#ff0000")  # 红色
            self.append_log("错误: 请填写所有必填项")
            return
        
        # 构建命令行参数
        cmd = [self.executable_path]
        cmd_str_parts = [self.executable_path]
        
        # 添加参数，排除 ignore_hosts
        for key, entry in self.entries.items():
            # 跳过 ignore_hosts 参数
            if key == "ignore_hosts":
                continue
            
            value = entry.get_text().strip()
            if value:  # 只有当值不为空时才添加参数
                cmd.extend([f"-{key}", value])
                cmd_str_parts.extend([f"-{key}", f'"{value}"'])
        
        # 显示命令
        cmd_str = " ".join(cmd_str_parts)
        self.append_log(f"执行命令: {cmd_str}")
        # 更新UI状态
        self.update_ui_state(True)
        
        # 尝试启动进程
        try:
            # 更新状态
            self.status_label.set_text("正在启动服务...")
            self.set_label_color(self.status_label, "#009900")  # 绿色
            
            # 在单独的线程中运行进程，避免阻塞GUI
            self.process_thread = threading.Thread(target=self.run_process, args=(cmd,))
            self.process_thread.daemon = True  # 守护线程，主程序退出时自动终止
            self.process_thread.start()
            
        except Exception as e:
            error_msg = f"启动失败: {str(e)}"
            self.status_label.set_text(error_msg)
            self.set_label_color(self.status_label, "#ff0000")  # 红色
            self.append_log(error_msg)
            self.update_ui_state(False)
    
    def test_latency(self):
        """测试代理延迟"""
        try:
            import requests
            
            # 获取代理监听地址
            proxy_addr = self.entries["l"].get_text().strip()
            if not proxy_addr:
                proxy_addr = "127.0.0.1:30000"  # 默认值
            
            # 设置代理
            proxies = {
                'http': f'http://{proxy_addr}',
                'https': f'http://{proxy_addr}'
            }
            
            # 测试请求 - 使用流式请求，一旦收到"success"就结束
            start_time = time.time()
            #response = requests.get('http://www.google.com/generate_204', proxies=proxies, timeout=3, stream=True)
            response = requests.get('http://detectportal.firefox.com/', proxies=proxies, timeout=3, stream=True)
            
            # 逐块读取响应内容
            received_data = b''
            success_found = False
            for chunk in response.iter_content(chunk_size=128):
                if chunk:
                    received_data += chunk
                    # 检查是否包含"success"字符串
                    if b"success" in received_data:
                        success_found = True
                        break
                
                # 检查是否超时
                if (time.time() - start_time) > 3:
                    break
            
            end_time = time.time()
            
            # 关闭响应
            response.close()
            
            if success_found:
                # 计算延迟（毫秒）
                latency = int((end_time - start_time) * 1000)
                
                # 根据延迟返回颜色和状态文本
                if latency < 1000:
                    return latency, Gdk.RGBA(0, 0.8, 0, 1)  # 绿色
                elif 1000 <= latency <= 3000:
                    return latency, Gdk.RGBA(1, 0.8, 0, 1)  # 黄色
                else:
                    return None, Gdk.RGBA(1, 0, 0, 1)  # 红色（超时）
            else:
                # 未找到"success"字符串或超时
                return None, Gdk.RGBA(1, 0, 0, 1)  # 红色（超时或失败）
                
        except requests.Timeout:
            return None, Gdk.RGBA(1, 0, 0, 1)  # 超时
        except Exception as e:
            self.append_log(f"延迟测试失败: {str(e)}")
            return None, None  # 测试失败

    
    def update_latency(self):
        """更新延迟测试结果并显示"""
        try:
            # 进行延迟测试
            latency, color = self.test_latency()
            if latency is not None:
                # 显示延迟测试结果
                self.status_label.set_text(f"服务已启动 - 延迟: {latency} 毫秒")
                if color:
                    self.status_label.override_color(Gtk.StateFlags.NORMAL, color)
                self.append_log(f"延迟测试结果: {latency} 毫秒")
            else:
                # 测试失败
                self.append_log("延迟测试失败: 无法连接到服务或超时")
        except Exception as e:
            self.append_log(f"更新延迟时出错: {str(e)}")
        
        # 返回True以保持定时器继续运行
        return True


    def on_stop_clicked(self, widget):
        """停止正在运行的进程并清除代理设置"""
        if self.running_process:
            try:
                self.append_log("正在停止服务...")
                self.status_label.set_text("正在停止服务...")
                
                # 尝试优雅终止进程
                if os.name == 'nt':  # Windows系统
                    self.running_process.terminate()
                else:  # Unix/Linux系统
                    os.kill(self.running_process.pid, signal.SIGTERM)
                
                # 等待进程终止，但设置超时
                try:
                    self.running_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 如果超时，强制终止
                    self.append_log("强制终止服务...")
                    if os.name == 'nt':
                        self.running_process.kill()
                    else:
                        os.kill(self.running_process.pid, signal.SIGKILL)
                
                self.append_log("服务已停止")
                
                # 如果设置了代理，自动清除
                if self.proxy_set:
                    self.append_log("自动清除代理设置...")
                    self.clear_system_proxy(show_dialog=False)
                
                self.status_label.set_text("服务已停止")
                self.status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.5, 0.5, 0.5, 1))  # 灰色
                
            except Exception as e:
                error_msg = f"停止服务时出错: {str(e)}"
                self.append_log(error_msg)
                self.status_label.set_text("停止失败")
                self.status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 0, 0, 1))  # 红色
            finally:
                self.update_ui_state(False)
    
    def on_proxy_button_clicked(self, widget):
        """代理按钮点击事件，根据当前状态切换功能"""
        if self.proxy_set:
            # 清除代理
            self.clear_system_proxy()
        else:
            # 设置代理
            self.set_system_proxy()
    
    def set_system_proxy(self):
        """设置系统代理"""
        # 获取代理监听地址
        proxy_address = self.entries["l"].get_text().strip()
        
        if not proxy_address:
            self.append_log("错误: 代理监听地址不能为空")
            return
        
        # 解析代理地址和端口
        try:
            proxy_ip, proxy_port = proxy_address.split(":")
            # 确保端口是数字
            int(proxy_port)
        except ValueError:
            self.append_log(f"错误: 无效的代理监听地址格式: {proxy_address}。请使用 IP:端口 格式")
            return
        
        # 获取代理设置脚本路径
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_set_linux_sh.sh")
        
        if not os.path.isfile(script_path) or not os.access(script_path, os.X_OK):
            self.append_log(f"错误: 找不到可执行的代理设置脚本: {script_path}")
            return
        
        # 获取忽略的主机（从输入框中读取）
        ignore_hosts = self.entries["ignore_hosts"].get_text().strip()
        # 如果输入框为空，使用默认值
        if not ignore_hosts:
            ignore_hosts = "localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12"
        
        # 执行代理设置脚本
        try:
            self.append_log(f"正在设置系统代理: {proxy_ip}:{proxy_port}")
            
            # 使用bash执行脚本
            result = subprocess.run(
                ["bash", script_path, "manual", proxy_ip, proxy_port, ignore_hosts],
                capture_output=True,
                text=True
            )
            
            # 记录脚本输出
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    self.append_log(f"代理脚本: {line}")
            if result.stderr:
                for line in result.stderr.strip().split("\n"):
                    self.append_log(f"代理脚本错误: {line}")
            
            # 检查执行结果
            if result.returncode == 0:
                self.proxy_set = True  # 设置代理状态标志
                # 更新按钮文本
                self.proxy_button.set_label("清除代理设置")
                
                # 显示成功对话框
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="代理设置成功"
                )
                dialog.format_secondary_text(f"系统代理已设置为: {proxy_ip}:{proxy_port}")
                dialog.run()
                dialog.destroy()
            else:
                self.append_log(f"系统代理设置失败，返回码: {result.returncode}")
                # 显示错误对话框
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="代理设置失败"
                )
                dialog.format_secondary_text(f"执行脚本时出错，请检查日志")
                dialog.run()
                dialog.destroy()
                
        except Exception as e:
            error_msg = f"设置代理时出错: {str(e)}"
            self.append_log(error_msg)
            # 显示错误对话框
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="代理设置失败"
            )
            dialog.format_secondary_text(error_msg)
            dialog.run()
            dialog.destroy()
    
    def clear_system_proxy(self, show_dialog=True):
        """清除系统代理设置"""
        # 获取代理设置脚本路径
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_set_linux_sh.sh")
        
        if not os.path.isfile(script_path) or not os.access(script_path, os.X_OK):
            self.append_log(f"错误: 找不到可执行的代理设置脚本: {script_path}")
            return
        
        try:
            self.append_log("正在清除系统代理设置...")
            
            # 执行代理设置脚本，模式设为none以禁用代理
            result = subprocess.run(
                ["bash", script_path, "none"],
                capture_output=True,
                text=True
            )
            
            # 记录脚本输出
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    self.append_log(f"代理脚本: {line}")
            if result.stderr:
                for line in result.stderr.strip().split("\n"):
                    self.append_log(f"代理脚本错误: {line}")
            if result.returncode == 0:
                self.proxy_set = False  # 重置代理状态标志
                # 更新按钮文本
                self.proxy_button.set_label("设置为系统代理")
                
                # 只有在show_dialog为True时才显示对话框
                if show_dialog:
                    dialog = Gtk.MessageDialog(
                        transient_for=self,
                        flags=0,
                        message_type=Gtk.MessageType.INFO,
                        buttons=Gtk.ButtonsType.OK,
                        text="代理已清除"
                    )
                    dialog.format_secondary_text("系统代理设置已成功清除")
                    dialog.run()
                    dialog.destroy()
            else:
                self.append_log(f"清除代理失败，返回码: {result.returncode}")
                
                # 只有在show_dialog为True时才显示对话框
                if show_dialog:
                    dialog = Gtk.MessageDialog(
                        transient_for=self,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="清除代理失败"
                    )
                    dialog.format_secondary_text(f"执行脚本时出错，请检查日志")
                    dialog.run()
                    dialog.destroy()
                
        except Exception as e:
            error_msg = f"清除代理时出错: {str(e)}"
            self.append_log(error_msg)
            
            # 只有在show_dialog为True时才显示对话框
            if show_dialog:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="清除代理失败"
                )
                dialog.format_secondary_text(error_msg)
                dialog.run()
                dialog.destroy()
    def run_process(self, cmd):
        """在单独线程中运行进程并处理输出"""
        try:
            # 启动进程
            self.running_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # 更新状态为服务已启动
            GLib.idle_add(self.status_label.set_text, "服务已启动")
            GLib.idle_add(self.status_label.override_color, Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0.8, 0, 1))  # 绿色
            GLib.idle_add(self.append_log, "服务已成功启动")
            
            # 等待1秒让服务完全初始化
            time.sleep(0.8)
            
            # 进行第一次延迟测试
            self.update_latency()
            
            # 设置定时器，每3分钟(180秒)重新测试一次延迟
            self.latency_timer = GLib.timeout_add_seconds(180, self.update_latency)
            
            # 读取输出
            for line in iter(self.running_process.stdout.readline, ''):
                if line.strip():
                    GLib.idle_add(self.append_log, line.strip())
            
            # 等待进程结束
            self.running_process.wait()
            
            # 取消延迟测试定时器
            if self.latency_timer:
                GLib.source_remove(self.latency_timer)
                self.latency_timer = None
            
            # 检查进程是否正常退出
            if self.running_process.returncode == 0 or self.running_process.returncode is None:
                GLib.idle_add(self.append_log, "服务已停止")
            else:
                GLib.idle_add(self.append_log, f"服务异常退出，返回码: {self.running_process.returncode}")
            
            # 自动清除代理设置（如果已设置）
            if self.proxy_set:
                GLib.idle_add(self.clear_system_proxy, False)
            
            # 更新UI状态
            GLib.idle_add(self.status_label.set_text, "服务已停止")
            GLib.idle_add(self.status_label.override_color, Gtk.StateFlags.NORMAL, Gdk.RGBA(0.5, 0.5, 0.5, 1))  # 灰色
            GLib.idle_add(self.update_ui_state, False)
            
        except Exception as e:
            GLib.idle_add(self.append_log, f"运行进程时出错: {str(e)}")
            GLib.idle_add(self.status_label.set_text, "运行出错")
            GLib.idle_add(self.status_label.override_color, Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 0, 0, 1))  # 红色
            GLib.idle_add(self.update_ui_state, False)
        finally:
            self.running_process = None
            self.process_thread = None


def main():
    # 检查GTK版本
    if not Gtk.check_version(3, 0, 0):
        print("GTK版本兼容")
    else:
        print("警告: GTK版本可能不兼容")
    
    # 创建并运行GUI
    win = ECHWorkerGUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()

    def clear_env_proxy(self):
        """清除环境变量中的代理设置"""
        # 定义要清除的代理相关环境变量
        proxy_vars = [
            'http_proxy', 'https_proxy', 'ftp_proxy', 
            'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY',
            'all_proxy', 'ALL_PROXY',
            'no_proxy', 'NO_PROXY'
        ]
        
        # 清除这些环境变量
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]
                self.append_log(f"已清除环境变量: {var}")
        
        self.append_log("已清除环境变量中的代理设置")