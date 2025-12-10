#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECH Workers 客户端 - 跨平台版本 (Python + PyQt5)
支持 Windows 和 macOS
"""

import sys
import json
import os
import subprocess
import threading
import ipaddress
from pathlib import Path

# Windows 特殊处理
if sys.platform == 'win32':
    # 隐藏控制台窗口
    try:
        from ctypes import windll
        # 获取控制台窗口句柄并隐藏
        hwnd = windll.kernel32.GetConsoleWindow()
        if hwnd:
            windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
    except:
        pass
    
    # 高 DPI 支持 - 必须在导入 PyQt5 之前设置
    # 使用 PROCESS_PER_MONITOR_DPI_AWARE_V2 (Windows 10 1703+)
    # 这支持每个监视器 DPI 感知，并启用子窗口 DPI 缩放
    try:
        from ctypes import windll, ctypes
        # 尝试使用最新的 DPI 感知 API (Windows 10 1703+)
        try:
            # PROCESS_PER_MONITOR_DPI_AWARE_V2 = 2
            # 这个值支持每个监视器 DPI 感知和子窗口 DPI 缩放
            windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            # 如果 shcore 不可用，尝试旧版 API
            try:
                # PROCESS_PER_MONITOR_DPI_AWARE = 2 (旧版)
                windll.shcore.SetProcessDpiAwareness(2)
            except:
                # 如果都失败，使用最基础的 DPI 感知
                try:
                    windll.user32.SetProcessDPIAware()
                except:
                    pass
    except:
        pass

# 检查 PyQt5
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                  QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                  QComboBox, QTextEdit, QCheckBox, QGroupBox, 
                                  QMessageBox, QInputDialog, QSystemTrayIcon, QMenu, QAction)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
    from PyQt5.QtGui import QIcon, QTextCursor, QPixmap, QPainter, QColor, QFont
    HAS_PYQT = True
    
    # 注册 QTextCursor 类型以避免信号槽错误
    try:
        from PyQt5.QtCore import qRegisterMetaType
        qRegisterMetaType('QTextCursor')
    except (ImportError, AttributeError):
        # qRegisterMetaType 在某些 PyQt5 版本中可能不可用，忽略
        pass
    
    # 高 DPI 支持 - 必须在创建 QApplication 之前设置
    # PyQt5 5.6+ 支持高 DPI 缩放
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 设置环境变量以优化高 DPI 显示（Windows）
    if sys.platform == 'win32':
        try:
            # 启用高 DPI 缩放
            os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
            # 设置缩放因子舍入策略（避免模糊）
            os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'Round'
            # 禁用自动缩放因子（让系统处理）
            # os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
        except:
            pass
except ImportError:
    HAS_PYQT = False
    print("错误: 未安装 PyQt5")
    print("安装命令: pip3 install PyQt5")
    sys.exit(1)

APP_VERSION = "1.4"
APP_TITLE = f"ECH Workers 客户端 v{APP_VERSION}"

# 中国IP列表文件名（离线版本，放在程序目录）
CHINA_IP_LIST_FILE = "chn_ip.txt"

def get_app_dir():
    """获取程序所在目录（支持打包后的可执行文件）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的可执行文件
        return Path(sys.executable).parent.absolute()
    else:
        # 开发模式或直接运行 Python 脚本
        return Path(__file__).parent.absolute()

# 复用原有的 ConfigManager, ProcessManager, AutoStartManager
# 从原文件导入这些类（简化版本）
class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        # 跨平台配置文件路径
        if sys.platform == 'win32':
            # Windows: %APPDATA%\ECHWorkersClient
            self.config_dir = Path(os.getenv('APPDATA', Path.home())) / "ECHWorkersClient"
        else:
            # macOS/Linux: ~/Library/Application Support/ECHWorkersClient 或 ~/.config/ECHWorkersClient
            if sys.platform == 'darwin':
                self.config_dir = Path.home() / "Library" / "Application Support" / "ECHWorkersClient"
            else:
                self.config_dir = Path.home() / ".config" / "ECHWorkersClient"
        
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.servers = []
        self.current_server_id = None
        
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.servers = data.get('servers', [])
                    self.current_server_id = data.get('current_server_id')
            except Exception as e:
                print(f"加载配置失败: {e}")
                self.servers = []
                self.current_server_id = None
        
        if not self.servers:
            self.add_default_server()
    
    def save_config(self):
        """保存配置"""
        try:
            data = {
                'servers': self.servers,
                'current_server_id': self.current_server_id
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def add_default_server(self):
        """添加默认服务器"""
        import uuid
        default_server = {
            'id': str(uuid.uuid4()),
            'name': '默认服务器',
            'server': 'example.com:443',
            'listen': '127.0.0.1:30000',
            'token': '',
            'ip': 'saas.sin.fan',
            'dns': 'dns.alidns.com/dns-query',
            'ech': 'cloudflare-ech.com',
            'routing_mode': 'bypass_cn'  # 默认跳过中国大陆
        }
        self.servers.append(default_server)
        self.current_server_id = default_server['id']
        self.save_config()
    
    def get_current_server(self):
        """获取当前服务器配置"""
        if self.current_server_id:
            for server in self.servers:
                if server['id'] == self.current_server_id:
                    return server
        return self.servers[0] if self.servers else None
    
    def update_server(self, server_data):
        """更新服务器配置"""
        for i, server in enumerate(self.servers):
            if server['id'] == server_data['id']:
                self.servers[i] = server_data
                break
    
    def add_server(self, server_data):
        """添加服务器"""
        import uuid
        if 'id' not in server_data:
            server_data['id'] = str(uuid.uuid4())
        self.servers.append(server_data)
        self.current_server_id = server_data['id']
    
    def delete_server(self, server_id):
        """删除服务器"""
        self.servers = [s for s in self.servers if s['id'] != server_id]
        if self.current_server_id == server_id:
            self.current_server_id = self.servers[0]['id'] if self.servers else None


class ProcessThread(QThread):
    """进程线程"""
    log_output = pyqtSignal(str)
    process_finished = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.process = None
        self.is_running = False
    
    def run(self):
        """运行进程"""
        exe_path = self._find_executable()
        if not exe_path:
            app_dir = get_app_dir()
            self.log_output.emit("错误: 找不到 ech-workers 可执行文件!\n")
            self.log_output.emit(f"请确保 ech-workers 可执行文件在以下位置之一:\n")
            self.log_output.emit(f"  - {app_dir}/ech-workers\n")
            self.log_output.emit(f"  - {app_dir}/ech-workers.exe\n")
            self.log_output.emit(f"  - {Path.cwd()}/ech-workers\n")
            self.log_output.emit(f"  - 或者在系统 PATH 中\n")
            self.log_output.emit(f"\n注意: ech-workers 必须是编译后的可执行文件，不是源文件。\n")
            self.process_finished.emit()
            return
        
        cmd = [exe_path]
        if self.config.get('server'):
            cmd.extend(['-f', self.config['server']])
        if self.config.get('listen'):
            cmd.extend(['-l', self.config['listen']])
        if self.config.get('token'):
            cmd.extend(['-token', self.config['token']])
        if self.config.get('ip'):
            cmd.extend(['-ip', self.config['ip']])
        if self.config.get('dns') and self.config['dns'] != 'dns.alidns.com/dns-query':
            cmd.extend(['-dns', self.config['dns']])
        if self.config.get('ech') and self.config['ech'] != 'cloudflare-ech.com':
            cmd.extend(['-ech', self.config['ech']])
        # 添加分流模式参数
        routing_mode = self.config.get('routing_mode', 'bypass_cn')
        if routing_mode:
            cmd.extend(['-routing', routing_mode])
        
        try:
            # Windows 上需要指定 UTF-8 编码，因为 Go 程序输出 UTF-8
            # 同时隐藏子进程的控制台窗口
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'bufsize': 1
            }
            
            # Windows: 使用 CREATE_NO_WINDOW 隐藏控制台
            if sys.platform == 'win32':
                CREATE_NO_WINDOW = 0x08000000
                popen_kwargs['creationflags'] = CREATE_NO_WINDOW
            
            self.process = subprocess.Popen(cmd, **popen_kwargs)
            self.is_running = True
            
            # 使用 UTF-8 解码，忽略无法解码的字符
            while self.is_running:
                line = self.process.stdout.readline()
                if not line:
                    break
                try:
                    # 尝试 UTF-8 解码
                    decoded_line = line.decode('utf-8', errors='replace')
                except:
                    # 如果失败，尝试系统默认编码
                    try:
                        decoded_line = line.decode(errors='replace')
                    except:
                        decoded_line = str(line)
                if decoded_line:
                    self.log_output.emit(decoded_line)
            
            self.process.wait()
            self.is_running = False
            self.process_finished.emit()
        except Exception as e:
            self.log_output.emit(f"错误: 启动失败 - {str(e)}\n")
            self.process_finished.emit()
    
    def stop(self):
        """停止进程"""
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                self.process.kill()
    
    def _find_executable(self):
        """查找可执行文件（跨平台）"""
        # 程序所在目录（支持双击运行）
        app_dir = get_app_dir()
        # 当前工作目录
        current_dir = Path.cwd()
        
        # Windows 和 Unix 的可执行文件扩展名
        exe_ext = '.exe' if sys.platform == 'win32' else ''
        
        # 可能的可执行文件路径（按优先级）
        possible_paths = [
            app_dir / f'ech-workers{exe_ext}',
            current_dir / f'ech-workers{exe_ext}',
            # Windows 特定路径
            app_dir / 'ech-workers.exe' if sys.platform == 'win32' else None,
            current_dir / 'ech-workers.exe' if sys.platform == 'win32' else None,
            # Unix 路径（无扩展名）
            app_dir / 'ech-workers' if sys.platform != 'win32' else None,
            current_dir / 'ech-workers' if sys.platform != 'win32' else None,
        ]
        
        # 过滤掉 None 值
        possible_paths = [p for p in possible_paths if p is not None]
        
        for path in possible_paths:
            if path.exists():
                # Windows: 检查文件是否存在即可（.exe 文件）
                # Unix: 检查文件权限
                if sys.platform == 'win32':
                    # Windows 上，.exe 文件可以直接运行
                    if path.suffix.lower() == '.exe':
                        return str(path)
                    # 或者检查文件是否可执行
                    try:
                        with open(path, 'rb') as f:
                            header = f.read(2)
                            # PE 文件头
                            if header == b'MZ':
                                return str(path)
                    except:
                        pass
                else:
                    # Unix/Linux/macOS: 检查执行权限
                    if os.access(path, os.X_OK):
                        return str(path)
                    # 或者检查是否是二进制文件
                    try:
                        with open(path, 'rb') as f:
                            header = f.read(4)
                            # ELF 或 Mach-O
                            if (header.startswith(b'\x7fELF') or 
                                header.startswith(b'\xfe\xed\xfa') or
                                header.startswith(b'#!')):
                                # 尝试添加执行权限
                                try:
                                    os.chmod(path, 0o755)
                                except:
                                    pass
                                return str(path)
                    except:
                        pass
        
        # 尝试从 PATH 中查找
        import shutil
        exe = shutil.which('ech-workers')
        if exe:
            return exe
        
        # 如果都找不到，返回 None
        return None


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config_manager.load_config()
        self.process_thread = None
        self.is_autostart = '-autostart' in sys.argv
        self.china_ip_ranges = None  # 缓存中国IP列表
        self.tray_icon = None  # 系统托盘图标
        
        self.init_ui()
        self.init_server_combo()  # 初始化下拉框
        self.load_server_config()
        self.init_tray_icon()  # 初始化系统托盘
        
        # 异步加载中国IP列表（静默模式：失败时不显示错误）
        self.load_china_ip_list_async(silent=True)
        
        if self.is_autostart:
            self.hide()
            QApplication.processEvents()
            self.auto_start()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(APP_TITLE)
        
        # Windows DPI 适配：根据系统 DPI 调整窗口大小
        # PyQt5 的 AA_EnableHighDpiScaling 会自动处理缩放
        # 我们设置逻辑像素大小，系统会自动转换为物理像素
        base_width = 950
        base_height = 800
        
        # 获取可用屏幕区域（排除任务栏）
        try:
            # 方法1: 使用 QApplication.desktop() (PyQt5 推荐方式)
            try:
                desktop = QApplication.desktop()
                available_geometry = desktop.availableGeometry()
                screen_width = available_geometry.width()
                screen_height = available_geometry.height()
                screen_x = available_geometry.x()
                screen_y = available_geometry.y()
            except:
                # 方法2: 使用 QScreen (如果 desktop() 不可用)
                try:
                    screen = QApplication.primaryScreen()
                    available_geometry = screen.availableGeometry()
                    screen_width = available_geometry.width()
                    screen_height = available_geometry.height()
                    screen_x = available_geometry.x()
                    screen_y = available_geometry.y()
                except:
                    # 如果都失败，使用默认值
                    screen_width = 1920
                    screen_height = 1080
                    screen_x = 0
                    screen_y = 0
            
            # 确保窗口大小不超过可用区域
            if base_width > screen_width:
                base_width = screen_width - 40  # 留出边距
            if base_height > screen_height:
                base_height = screen_height - 40  # 留出边距，确保不遮挡任务栏
            
            # 计算居中位置
            x = screen_x + (screen_width - base_width) // 2
            y = screen_y + (screen_height - base_height) // 2
            
            # 确保窗口不会超出屏幕边界
            if x < screen_x:
                x = screen_x + 20
            if y < screen_y:
                y = screen_y + 20
            
            self.setGeometry(x, y, base_width, base_height)
        except:
            # 如果获取屏幕信息失败，使用默认位置
            self.setGeometry(100, 100, base_width, base_height)
        
        # 设置窗口图标（黑客帝国风格）
        self.setWindowIcon(self._create_matrix_icon())
        
        # 应用现代化样式
        self.setStyleSheet(self._get_modern_style())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 服务器管理
        server_group = QGroupBox("服务器管理")
        server_layout = QHBoxLayout()
        server_layout.setSpacing(10)
        server_label = QLabel("选择服务器:")
        server_label.setStyleSheet("font-weight: 600;")
        server_layout.addWidget(server_label)
        self.server_combo = QComboBox()
        self.server_combo.currentIndexChanged.connect(self.on_server_changed)
        server_layout.addWidget(self.server_combo, 1)
        
        # 按钮组
        btn_new = QPushButton("新增")
        btn_new.clicked.connect(self.add_server)
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_server)
        btn_rename = QPushButton("重命名")
        btn_rename.clicked.connect(self.rename_server)
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(self.delete_server)
        
        server_layout.addWidget(btn_new)
        server_layout.addWidget(btn_save)
        server_layout.addWidget(btn_rename)
        server_layout.addWidget(btn_delete)
        server_layout.addStretch()
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # 核心配置
        core_group = QGroupBox("核心配置")
        core_layout = QVBoxLayout()
        core_layout.setSpacing(12)
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("例如: your-worker.workers.dev:443")
        core_layout.addWidget(self.create_label_edit("服务地址:", self.server_edit))
        self.listen_edit = QLineEdit()
        self.listen_edit.setPlaceholderText("例如: 127.0.0.1:30000")
        core_layout.addWidget(self.create_label_edit("监听地址:", self.listen_edit))
        core_group.setLayout(core_layout)
        layout.addWidget(core_group)
        
        # 高级选项
        advanced_group = QGroupBox("高级选项 (可选)")
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(12)
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("身份验证令牌（可选）")
        self.token_edit.setEchoMode(QLineEdit.Password)
        advanced_layout.addWidget(self.create_label_edit("身份令牌:", self.token_edit))
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("例如: saas.sin.fan")
        row1.addWidget(self.create_label_edit("优选IP或域名:", self.ip_edit))
        self.dns_edit = QLineEdit()
        self.dns_edit.setPlaceholderText("例如: dns.alidns.com/dns-query")
        row1.addWidget(self.create_label_edit("DOH服务器:", self.dns_edit))
        advanced_layout.addLayout(row1)
        self.ech_edit = QLineEdit()
        self.ech_edit.setPlaceholderText("例如: cloudflare-ech.com")
        advanced_layout.addWidget(self.create_label_edit("ECH域名:", self.ech_edit))
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 分流设置
        routing_group = QGroupBox("分流设置")
        routing_layout = QHBoxLayout()
        routing_layout.setSpacing(10)
        routing_label = QLabel("代理模式:")
        routing_label.setStyleSheet("font-weight: 600;")
        routing_layout.addWidget(routing_label)
        self.routing_combo = QComboBox()
        self.routing_combo.addItem("全局代理", "global")
        self.routing_combo.addItem("🇨🇳 跳过中国大陆", "bypass_cn")
        self.routing_combo.addItem("不改变代理", "none")
        self.routing_combo.currentIndexChanged.connect(self.on_routing_changed)
        routing_layout.addWidget(self.routing_combo, 1)
        routing_layout.addStretch()
        routing_group.setLayout(routing_layout)
        layout.addWidget(routing_group)
        
        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        self.start_btn = QPushButton("启动代理")
        self.start_btn.clicked.connect(self.start_process)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setEnabled(False)
        self.proxy_btn = QPushButton("设置系统代理")
        self.proxy_btn.clicked.connect(self.toggle_system_proxy)
        self.proxy_btn.setEnabled(False)  # 只有启动后才能设置
        self.auto_start_check = QCheckBox("开机启动")
        self.auto_start_check.stateChanged.connect(self.on_auto_start_changed)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.proxy_btn)
        control_layout.addWidget(self.auto_start_check)
        control_layout.addStretch()
        btn_clear = QPushButton("清空日志")
        btn_clear.clicked.connect(self.clear_log)
        control_layout.addWidget(btn_clear)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 系统代理状态
        self.system_proxy_enabled = False
        
        # 日志
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # 使用等宽字体，更适合日志显示
        from PyQt5.QtGui import QFont
        font = QFont("Consolas" if sys.platform == 'win32' else "Monaco" if sys.platform == 'darwin' else "DejaVu Sans Mono", 9)
        self.log_text.setFont(font)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
    
    def _create_matrix_icon(self):
        """创建黑客帝国风格图标"""
        # 创建不同尺寸的图标
        sizes = [16, 32, 48, 64, 128, 256]
        icon = QIcon()
        
        for size in sizes:
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(0, 0, 0))  # 黑色背景
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制绿色边框
            painter.setPen(QColor(0, 255, 65))  # 矩阵绿
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(2, 2, size - 4, size - 4)
            
            # 绘制内部装饰（矩阵代码风格）
            if size >= 32:
                # 绘制一些绿色线条和点，模拟矩阵代码
                painter.setPen(QColor(0, 255, 65))
                
                # 绘制对角线
                if size >= 48:
                    painter.drawLine(4, 4, size - 4, size - 4)
                    painter.drawLine(size - 4, 4, 4, size - 4)
                
                # 绘制中心点
                center = size // 2
                painter.setBrush(QColor(0, 255, 65))
                painter.drawEllipse(center - 2, center - 2, 4, 4)
                
                # 绘制一些装饰线条
                if size >= 64:
                    # 绘制四个角的装饰
                    corner_size = size // 4
                    painter.setPen(QColor(0, 200, 50))  # 稍暗的绿色
                    # 左上角
                    painter.drawLine(4, 4, corner_size, 4)
                    painter.drawLine(4, 4, 4, corner_size)
                    # 右上角
                    painter.drawLine(size - 4, 4, size - corner_size, 4)
                    painter.drawLine(size - 4, 4, size - 4, corner_size)
                    # 左下角
                    painter.drawLine(4, size - 4, corner_size, size - 4)
                    painter.drawLine(4, size - 4, 4, size - corner_size)
                    # 右下角
                    painter.drawLine(size - 4, size - 4, size - corner_size, size - 4)
                    painter.drawLine(size - 4, size - 4, size - 4, size - corner_size)
            
            painter.end()
            icon.addPixmap(pixmap)
        
        return icon
    
    def _get_modern_style(self):
        """获取黑客帝国风格样式表"""
        return """
        /* 主窗口样式 - 深色背景 */
        QMainWindow {
            background-color: #000000;
        }
        
        /* 分组框样式 - 矩阵绿色边框 */
        QGroupBox {
            font-weight: 600;
            font-size: 13px;
            color: #00ff41;
            border: 2px solid #00ff41;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 15px;
            padding-bottom: 15px;
            background-color: #0a0a0a;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            padding: 0 8px;
            background-color: #000000;
            color: #00ff41;
        }
        
        /* 标签样式 - 绿色文字 */
        QLabel {
            color: #00ff41;
            font-size: 13px;
            min-width: 100px;
        }
        
        /* 输入框样式 - 深色背景，绿色边框 */
        QLineEdit {
            border: 2px solid #003311;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: #0a0a0a;
            color: #00ff41;
            selection-background-color: #00ff41;
            selection-color: #000000;
        }
        
        QLineEdit:focus {
            border: 2px solid #00ff41;
            background-color: #001a0a;
        }
        
        QLineEdit:disabled {
            background-color: #050505;
            color: #006622;
            border: 2px solid #002211;
        }
        
        /* 下拉框样式 */
        QComboBox {
            border: 2px solid #003311;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: #0a0a0a;
            color: #00ff41;
            min-width: 150px;
        }
        
        QComboBox:hover {
            border: 2px solid #00ff41;
        }
        
        QComboBox:focus {
            border: 2px solid #00ff41;
            background-color: #001a0a;
        }
        
        QComboBox:disabled {
            background-color: #050505;
            color: #006622;
            border: 2px solid #002211;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 30px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background-color: transparent;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #00ff41;
            width: 0;
            height: 0;
        }
        
        QComboBox QAbstractItemView {
            border: 2px solid #00ff41;
            border-radius: 6px;
            background-color: #0a0a0a;
            selection-background-color: #00ff41;
            selection-color: #000000;
            padding: 4px;
            color: #00ff41;
        }
        
        /* 按钮样式 - 绿色主题 */
        QPushButton {
            background-color: #003311;
            color: #00ff41;
            border: 2px solid #00ff41;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
            min-width: 100px;
        }
        
        QPushButton:hover {
            background-color: #00ff41;
            color: #000000;
            border: 2px solid #00ff41;
        }
        
        QPushButton:pressed {
            background-color: #00cc33;
            color: #000000;
        }
        
        QPushButton:disabled {
            background-color: #001a0a;
            color: #006622;
            border: 2px solid #003311;
        }
        
        /* 停止按钮特殊样式 - 红色警告 */
        QPushButton[text="停止"] {
            background-color: #330000;
            color: #ff0044;
            border: 2px solid #ff0044;
        }
        
        QPushButton[text="停止"]:hover {
            background-color: #ff0044;
            color: #000000;
        }
        
        QPushButton[text="停止"]:pressed {
            background-color: #cc0033;
            color: #000000;
        }
        
        /* 清空日志按钮样式 */
        QPushButton[text="清空日志"] {
            background-color: #1a1a1a;
            color: #888888;
            border: 2px solid #444444;
        }
        
        QPushButton[text="清空日志"]:hover {
            background-color: #444444;
            color: #00ff41;
            border: 2px solid #00ff41;
        }
        
        /* 复选框样式 */
        QCheckBox {
            color: #00ff41;
            font-size: 13px;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border: 2px solid #00ff41;
            border-radius: 4px;
            background-color: #0a0a0a;
        }
        
        QCheckBox::indicator:hover {
            background-color: #001a0a;
        }
        
        QCheckBox::indicator:checked {
            background-color: #00ff41;
            border: 2px solid #00ff41;
            image: none;
        }
        
        QCheckBox::indicator:checked::after {
            content: "✓";
            color: #000000;
            font-size: 14px;
            font-weight: bold;
        }
        
        /* 文本编辑框样式（日志） - 矩阵风格 */
        QTextEdit {
            border: 2px solid #00ff41;
            border-radius: 6px;
            padding: 12px;
            font-size: 12px;
            background-color: #000000;
            color: #00ff41;
            selection-background-color: #00ff41;
            selection-color: #000000;
        }
        
        QTextEdit:focus {
            border: 2px solid #00ff41;
        }
        
        /* 滚动条样式 - 绿色主题 */
        QScrollBar:vertical {
            border: none;
            background-color: #0a0a0a;
            width: 12px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #003311;
            border: 1px solid #00ff41;
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #00ff41;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        
        QScrollBar:horizontal {
            border: none;
            background-color: #0a0a0a;
            height: 12px;
            margin: 0;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #003311;
            border: 1px solid #00ff41;
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #00ff41;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }
        
        /* 布局间距 */
        QVBoxLayout {
            spacing: 10px;
        }
        
        QHBoxLayout {
            spacing: 10px;
        }
        """
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用黑客帝国风格图标
        try:
            icon = self._create_matrix_icon()
            self.tray_icon.setIcon(icon)
        except:
            # 如果创建图标失败，使用默认图标
            try:
                icon = QIcon()
                if hasattr(QApplication, 'style'):
                    icon = self.style().standardIcon(self.style().SP_ComputerIcon)
                self.tray_icon.setIcon(icon)
            except:
                pass
        
        self.tray_icon.setToolTip(APP_TITLE)
        
        # 创建右键菜单
        tray_menu = QMenu(self)
        
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏窗口", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 双击托盘图标显示/隐藏窗口
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
    
    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """退出应用程序"""
        # 关闭前清理系统代理
        if self.system_proxy_enabled:
            self._set_system_proxy(False)
        
        # 停止进程
        if self.process_thread and self.process_thread.is_running:
            self.process_thread.stop()
            self.process_thread.wait()
        
        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()
        
        QApplication.quit()
    
    def load_china_ip_list_async(self, silent=False):
        """异步加载中国IP列表（从离线文件读取）
        
        Args:
            silent: 是否静默模式（失败时不显示错误）
        """
        def load_in_thread():
            try:
                if not silent:
                    self.append_log("[系统] 正在加载中国IP列表（离线版本）...\n")
                ranges = self._load_china_ip_list()
                if ranges:
                    self.china_ip_ranges = ranges
                    if not silent:
                        self.append_log(f"[系统] 已加载中国IP列表，共 {len(ranges)} 个IP段\n")
                # 失败时不显示错误（静默模式）
            except Exception as e:
                # 静默模式：不显示错误
                if not silent:
                    self.append_log(f"[系统] 加载中国IP列表出错: {e}\n")
        
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()
    
    def _load_china_ip_list(self):
        """从程序目录读取并解析中国IP列表（离线版本）"""
        try:
            # 尝试从缓存读取（永久有效，不检查过期时间）
            cache_file = self.config_manager.config_dir / "china_ip_list.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        ranges = cached_data.get('ranges', [])
                        if ranges:
                            return ranges
                except:
                    pass
            
            # 从程序目录读取IP列表文件（离线版本）
            app_dir = get_app_dir()
            ip_list_file = app_dir / CHINA_IP_LIST_FILE
            
            if not ip_list_file.exists():
                # 如果文件不存在，返回 None（静默失败）
                return None
            
            # 读取文件内容
            with open(ip_list_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析IP范围
            ranges = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    start_ip = parts[0]
                    end_ip = parts[1]
                    try:
                        start = ipaddress.IPv4Address(start_ip)
                        end = ipaddress.IPv4Address(end_ip)
                        ranges.append((int(start), int(end)))
                    except:
                        continue
            
            # 保存到缓存（永久有效）
            try:
                import time
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'ranges': ranges
                    }, f)
            except:
                pass
            
            return ranges
        except Exception as e:
            # 静默失败，不打印错误
            return None
    
    def _convert_ip_ranges_to_wildcards(self, ranges):
        """将IP范围转换为Windows ProxyOverride通配符格式"""
        if not ranges:
            return []
        
        wildcards = set()
        
        for start, end in ranges:
            start_ip = ipaddress.IPv4Address(start)
            end_ip = ipaddress.IPv4Address(end)
            
            start_parts = [int(x) for x in str(start_ip).split('.')]
            end_parts = [int(x) for x in str(end_ip).split('.')]
            
            # 如果整个A段相同
            if start_parts[0] == end_parts[0]:
                # 检查是否是整个A段 (0.0.0.0 - 255.255.255.255)
                if start_parts[1] == 0 and end_parts[1] == 255 and \
                   start_parts[2] == 0 and end_parts[2] == 255 and \
                   start_parts[3] == 0 and end_parts[3] == 255:
                    wildcards.add(f"{start_parts[0]}.*")
                # 检查是否是整个B段 (0.0.0.0 - 0.255.255.255)
                elif start_parts[2] == 0 and end_parts[2] == 255 and \
                     start_parts[3] == 0 and end_parts[3] == 255:
                    wildcards.add(f"{start_parts[0]}.{start_parts[1]}.*")
                # 检查是否是整个C段 (0.0.0.0 - 0.0.255.255)
                elif start_parts[3] == 0 and end_parts[3] == 255:
                    wildcards.add(f"{start_parts[0]}.{start_parts[1]}.{start_parts[2]}.*")
                else:
                    # 部分C段，添加所有涉及的IP
                    # 为了减少数量，只添加C段通配符
                    for c in range(start_parts[2], end_parts[2] + 1):
                        wildcards.add(f"{start_parts[0]}.{start_parts[1]}.{c}.*")
        
        # 优化：合并可以合并的通配符
        # 例如：1.0.*, 1.1.*, ..., 1.255.* 可以合并为 1.*
        optimized = set()
        a_segments = {}  # {A: set(B segments)}
        
        for wc in wildcards:
            parts = wc.split('.')
            if len(parts) == 2 and parts[1] == '*':
                # A.* 格式，直接添加
                optimized.add(wc)
            elif len(parts) == 3 and parts[2] == '*':
                # A.B.* 格式
                a = parts[0]
                if a not in a_segments:
                    a_segments[a] = set()
                a_segments[a].add(parts[1])
            else:
                # 其他格式，直接添加
                optimized.add(wc)
        
        # 检查每个A段是否覆盖了所有B段（0-255），如果是则合并为A.*
        for a, b_set in a_segments.items():
            if len(b_set) >= 250:  # 如果覆盖了大部分B段，使用A.*
                optimized.add(f"{a}.*")
            else:
                for b in b_set:
                    optimized.add(f"{a}.{b}.*")
        
        return sorted(list(optimized))
    
    def create_label_edit(self, label_text, edit_widget):
        """创建标签和输入框"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = QLabel(label_text)
        label.setMinimumWidth(120)
        label.setStyleSheet("font-weight: 500;")
        layout.addWidget(label)
        layout.addWidget(edit_widget, 1)
        return widget
    
    def init_server_combo(self):
        """初始化服务器下拉框（首次加载）"""
        # 暂时断开信号，避免触发 on_server_changed
        try:
            self.server_combo.currentIndexChanged.disconnect()
        except:
            pass
        
        self.server_combo.clear()
        sorted_servers = sorted(self.config_manager.servers, key=lambda x: x['name'])
        for server in sorted_servers:
            self.server_combo.addItem(server['name'], server['id'])
        
        # 选中当前服务器
        current = self.config_manager.get_current_server()
        if current:
            for i in range(self.server_combo.count()):
                if self.server_combo.itemData(i) == current['id']:
                    self.server_combo.setCurrentIndex(i)
                    break
        
        # 重新连接信号
        self.server_combo.currentIndexChanged.connect(self.on_server_changed)
    
    def load_server_config(self):
        """加载服务器配置"""
        # 只更新界面，不刷新 combo（避免递归）
        server = self.config_manager.get_current_server()
        if server:
            self.server_edit.setText(server.get('server', ''))
            self.listen_edit.setText(server.get('listen', ''))
            self.token_edit.setText(server.get('token', ''))
            self.ip_edit.setText(server.get('ip', ''))
            self.dns_edit.setText(server.get('dns', ''))
            self.ech_edit.setText(server.get('ech', ''))
            # 加载分流模式
            routing_mode = server.get('routing_mode', 'bypass_cn')
            for i in range(self.routing_combo.count()):
                if self.routing_combo.itemData(i) == routing_mode:
                    self.routing_combo.setCurrentIndex(i)
                    break
    
    def refresh_server_combo(self):
        """刷新服务器下拉框"""
        # 暂时断开信号连接，避免递归
        try:
            self.server_combo.currentIndexChanged.disconnect()
        except:
            pass
        
        self.server_combo.clear()
        
        # 确保有服务器
        if not self.config_manager.servers:
            # 如果没有服务器，添加默认服务器
            self.config_manager.add_default_server()
        
        sorted_servers = sorted(self.config_manager.servers, key=lambda x: x['name'])
        for server in sorted_servers:
            self.server_combo.addItem(server['name'], server['id'])
        
        # 确保有当前服务器
        current = self.config_manager.get_current_server()
        if current:
            # 查找并选中当前服务器
            found = False
            for i in range(self.server_combo.count()):
                if self.server_combo.itemData(i) == current['id']:
                    self.server_combo.setCurrentIndex(i)
                    found = True
                    break
            
            # 如果找不到当前服务器，选中第一个
            if not found and self.server_combo.count() > 0:
                self.server_combo.setCurrentIndex(0)
                # 更新当前服务器ID
                if self.server_combo.itemData(0):
                    self.config_manager.current_server_id = self.server_combo.itemData(0)
        else:
            # 如果没有当前服务器，选中第一个
            if self.server_combo.count() > 0:
                self.server_combo.setCurrentIndex(0)
                # 更新当前服务器ID
                if self.server_combo.itemData(0):
                    self.config_manager.current_server_id = self.server_combo.itemData(0)
        
        # 重新连接信号
        self.server_combo.currentIndexChanged.connect(self.on_server_changed)
    
    def get_control_values(self):
        """获取界面输入值"""
        server = self.config_manager.get_current_server()
        if not server:
            # 如果没有当前服务器，创建一个临时配置
            import uuid
            server = {
                'id': str(uuid.uuid4()),
                'name': '临时配置',
            }
        
        # 创建副本并更新为界面当前值
            server = server.copy()
            server['server'] = self.server_edit.text()
            server['listen'] = self.listen_edit.text()
            server['token'] = self.token_edit.text()
            server['ip'] = self.ip_edit.text()
            server['dns'] = self.dns_edit.text()
            server['ech'] = self.ech_edit.text()
        # 保存分流模式
        routing_mode = self.routing_combo.currentData()
        if routing_mode:
            server['routing_mode'] = routing_mode
        else:
            # 如果没有选择，使用默认值
            server['routing_mode'] = server.get('routing_mode', 'bypass_cn')
        return server
    
    def on_server_changed(self):
        """服务器选择改变"""
        if self.process_thread and self.process_thread.is_running:
            # 暂时断开信号，恢复选择
            self.server_combo.currentIndexChanged.disconnect()
            current = self.config_manager.get_current_server()
            if current:
                for i in range(self.server_combo.count()):
                    if self.server_combo.itemData(i) == current['id']:
                        self.server_combo.setCurrentIndex(i)
                        break
            self.server_combo.currentIndexChanged.connect(self.on_server_changed)
            QMessageBox.warning(self, "提示", "请先停止当前连接后再切换服务器")
            return
        
        index = self.server_combo.currentIndex()
        if index >= 0:
            server_id = self.server_combo.itemData(index)
            if server_id and server_id != self.config_manager.current_server_id:
                # 先保存当前编辑框的值到当前服务器（如果有的话）
                current_server = self.config_manager.get_current_server()
                if current_server:
                    # 将当前编辑框的值保存到当前服务器
                    current_server['server'] = self.server_edit.text()
                    current_server['listen'] = self.listen_edit.text()
                    current_server['token'] = self.token_edit.text()
                    current_server['ip'] = self.ip_edit.text()
                    current_server['dns'] = self.dns_edit.text()
                    current_server['ech'] = self.ech_edit.text()
                    # 保存分流模式
                    routing_mode = self.routing_combo.currentData()
                    if routing_mode:
                        current_server['routing_mode'] = routing_mode
                    self.config_manager.update_server(current_server)
                
                # 切换到新服务器
                self.config_manager.current_server_id = server_id
                # 暂时断开信号，避免递归
                self.server_combo.currentIndexChanged.disconnect()
                # 加载新服务器的配置到界面
                self.load_server_config()
                self.server_combo.currentIndexChanged.connect(self.on_server_changed)
                # 保存配置
                self.config_manager.save_config()
    
    def add_server(self):
        """添加服务器"""
        name, ok = QInputDialog.getText(self, "新增服务器", "请输入服务器名称:", text="新服务器")
        if ok and name.strip():
            name = name.strip()
            if any(s['name'] == name for s in self.config_manager.servers):
                QMessageBox.warning(self, "提示", "服务器名称已存在")
                return
            
            # 获取当前界面输入的值作为新服务器的默认值
            current = self.get_control_values()
            # 创建新服务器，只复制配置值，不复制 id 和 name
            new_server = {
                'server': current.get('server', '') if current else '',
                'listen': current.get('listen', '127.0.0.1:30000') if current else '127.0.0.1:30000',
                'token': current.get('token', '') if current else '',
                'ip': current.get('ip', 'saas.sin.fan') if current else 'saas.sin.fan',
                'dns': current.get('dns', 'dns.alidns.com/dns-query') if current else 'dns.alidns.com/dns-query',
                'ech': current.get('ech', 'cloudflare-ech.com') if current else 'cloudflare-ech.com',
                'routing_mode': current.get('routing_mode', 'bypass_cn') if current else 'bypass_cn',
                'name': name
            }
            # 添加服务器（会自动生成新的 id）
            self.config_manager.add_server(new_server)
            self.config_manager.save_config()
            self.refresh_server_combo()
            # 切换到新添加的服务器
            for i in range(self.server_combo.count()):
                if self.server_combo.itemText(i) == name:
                    self.server_combo.setCurrentIndex(i)
                    break
            self.load_server_config()
            self.append_log(f"[系统] 已添加新服务器: {name}\n")
    
    def save_server(self):
        """保存服务器配置"""
        server = self.get_control_values()
        if server:
            self.config_manager.update_server(server)
            self.config_manager.save_config()
            self.append_log(f"[系统] 服务器 \"{server['name']}\" 配置已保存\n")
    
    def delete_server(self):
        """删除服务器"""
        if len(self.config_manager.servers) <= 1:
            QMessageBox.warning(self, "提示", "至少需要保留一个服务器配置")
            return
        
        server = self.config_manager.get_current_server()
        if server:
            reply = QMessageBox.question(self, "确认删除", f"确定要删除服务器 \"{server['name']}\" 吗？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                name = server['name']
                deleted_id = server['id']
                
                # 删除服务器
                self.config_manager.delete_server(deleted_id)
                self.config_manager.save_config()
                
                # 刷新下拉框（会自动选中新的当前服务器）
                self.refresh_server_combo()
                
                # 加载新当前服务器的配置
                self.load_server_config()
                
                self.append_log(f"[系统] 已删除服务器: {name}\n")
    
    def rename_server(self):
        """重命名服务器"""
        server = self.config_manager.get_current_server()
        if server:
            new_name, ok = QInputDialog.getText(self, "重命名服务器", "请输入新的服务器名称:", text=server['name'])
            if ok and new_name.strip():
                new_name = new_name.strip()
                if any(s['name'] == new_name and s['id'] != server['id'] for s in self.config_manager.servers):
                    QMessageBox.warning(self, "提示", "服务器名称已存在")
                    return
                
                old_name = server['name']
                server['name'] = new_name
                self.config_manager.update_server(server)
                self.config_manager.save_config()
                self.refresh_server_combo()
                self.append_log(f"[系统] 服务器已重命名: {old_name} -> {new_name}\n")
    
    def start_process(self):
        """启动进程"""
        server = self.get_control_values()
        
        if not server.get('server'):
            QMessageBox.warning(self, "提示", "请输入服务地址")
            return
        
        if not server.get('listen'):
            QMessageBox.warning(self, "提示", "请输入监听地址")
            return
        
        self.config_manager.update_server(server)
        self.config_manager.save_config()
        
        self.process_thread = ProcessThread(server)
        self.process_thread.log_output.connect(self.append_log)
        self.process_thread.process_finished.connect(self.on_process_finished)
        self.process_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.proxy_btn.setEnabled(True)  # 启动后可以设置系统代理
        self.server_edit.setEnabled(False)
        self.listen_edit.setEnabled(False)
        self.server_combo.setEnabled(False)
        self.append_log(f"[系统] 已启动服务器: {server['name']}\n")
        
        # 如果中国IP列表未加载，尝试加载（从离线文件）
        if self.china_ip_ranges is None:
            self.load_china_ip_list_async(silent=True)
    
    def stop_process(self):
        """停止进程"""
        if self.process_thread:
            self.process_thread.stop()
            self.process_thread.wait()
        self.on_process_finished()
    
    def on_process_finished(self):
        """进程结束"""
        # 停止时自动清理系统代理
        if self.system_proxy_enabled:
            self._set_system_proxy(False)
            self.system_proxy_enabled = False
            self.proxy_btn.setText("设置系统代理")
            self.append_log("[系统] 已自动清理系统代理\n")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.proxy_btn.setEnabled(False)  # 停止后禁用系统代理按钮
        self.server_edit.setEnabled(True)
        self.listen_edit.setEnabled(True)
        self.server_combo.setEnabled(True)
        self.append_log("[系统] 进程已停止。\n")
    
    def on_auto_start_changed(self):
        """开机启动改变"""
        enabled = self.auto_start_check.isChecked()
        if self._set_auto_start(enabled):
            self.append_log(f"[系统] {'已设置' if enabled else '已取消'}开机启动\n")
        else:
            self.auto_start_check.setChecked(not enabled)
            QMessageBox.warning(self, "错误", "设置开机启动失败")
    
    def _set_auto_start(self, enabled):
        """设置开机启动（跨平台）"""
        try:
            if sys.platform == 'win32':
                # Windows: 使用注册表
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                app_name = "ECHWorkersClient"
                
                if enabled:
                    # 获取程序路径（支持打包后的可执行文件）
                    app_path = get_app_dir() / "gui.py"
                    if not app_path.exists() and getattr(sys, 'frozen', False):
                        # 如果是打包后的可执行文件，直接使用可执行文件路径
                        app_path = Path(sys.executable)
                        cmd = f'"{app_path}"'
                    else:
                        # 开发模式：使用 Python 运行脚本
                        python_path = sys.executable
                        cmd = f'"{python_path}" "{app_path}"'
                    
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                        winreg.CloseKey(key)
                        return True
                    except Exception as e:
                        print(f"设置开机启动失败: {e}")
                        return False
                else:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                        winreg.DeleteValue(key, app_name)
                        winreg.CloseKey(key)
                        return True
                    except FileNotFoundError:
                        # 如果值不存在，也算成功
                        return True
                    except Exception as e:
                        print(f"删除开机启动失败: {e}")
                        return False
            else:
                # macOS/Linux: 使用 LaunchAgents 或 systemd
                if sys.platform == 'darwin':
                    # macOS
                    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.echworkers.client.plist"
                    if enabled:
                        # 获取程序路径（支持打包后的可执行文件）
                        app_path = get_app_dir() / "gui.py"
                        if not app_path.exists() and getattr(sys, 'frozen', False):
                            # 如果是打包后的可执行文件，直接使用可执行文件路径
                            app_path = Path(sys.executable)
                            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.echworkers.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
        <string>-autostart</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
                        else:
                            # 开发模式：使用 Python 运行脚本
                            python_path = sys.executable
                            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.echworkers.client</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{app_path}</string>
        <string>-autostart</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
                        try:
                            plist_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(plist_path, 'w') as f:
                                f.write(plist_content)
                            return True
                        except Exception as e:
                            print(f"创建启动项失败: {e}")
                            return False
                    else:
                        try:
                            if plist_path.exists():
                                plist_path.unlink()
                            return True
                        except Exception as e:
                            print(f"删除启动项失败: {e}")
                            return False
                else:
                    # Linux: 使用 systemd user service（简化实现）
                    return False  # Linux 暂不支持
        except Exception as e:
            print(f"设置开机启动失败: {e}")
            return False
    
    def _is_auto_start_enabled(self):
        """检查是否已启用开机启动"""
        try:
            if sys.platform == 'win32':
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                app_name = "ECHWorkersClient"
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                    winreg.QueryValueEx(key, app_name)
                    winreg.CloseKey(key)
                    return True
                except FileNotFoundError:
                    return False
            elif sys.platform == 'darwin':
                plist_path = Path.home() / "Library" / "LaunchAgents" / "com.echworkers.client.plist"
                return plist_path.exists()
            else:
                return False
        except:
            return False
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def append_log(self, text):
        """追加日志"""
        self.log_text.append(text)
        # 限制日志长度（使用更安全的方式，避免 QTextCursor 信号问题）
        if self.log_text.document().blockCount() > 1000:
            try:
                # 获取文档内容
                doc = self.log_text.document()
                # 删除前100行
                cursor = QTextCursor(doc)
                cursor.movePosition(QTextCursor.Start)
                for _ in range(100):
                    cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
                cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
            except:
                # 如果出错，直接清空并保留最后900行
                try:
                    content = self.log_text.toPlainText()
                    lines = content.split('\n')
                    if len(lines) > 900:
                        self.log_text.setPlainText('\n'.join(lines[-900:]))
                except:
                    pass
    
    def update_auto_start_checkbox(self):
        """更新开机启动复选框状态"""
        self.auto_start_check.setChecked(self._is_auto_start_enabled())
    
    def on_routing_changed(self):
        """分流模式改变"""
        # 如果已经设置了系统代理，重新设置以应用新的绕过规则
        if self.system_proxy_enabled:
            routing_mode = self.routing_combo.currentData()
            if routing_mode == 'none':
                # 如果切换到"不改变代理"，自动关闭系统代理
                if self._set_system_proxy(False):
                    self.system_proxy_enabled = False
                    self.proxy_btn.setText("设置系统代理")
                    self.append_log("[系统] 分流模式已切换为\"不改变代理\"，已关闭系统代理\n")
            else:
                # 重新设置系统代理以应用新的绕过规则
                if self._set_system_proxy(True):
                    mode_name = self.routing_combo.currentText()
                    self.append_log(f"[系统] 分流模式已切换为\"{mode_name}\"，已更新系统代理设置\n")
    
    def toggle_system_proxy(self):
        """切换系统代理"""
        routing_mode = self.routing_combo.currentData()
        if routing_mode == 'none':
            QMessageBox.information(self, "提示", "当前分流模式为\"不改变代理\"，无法设置系统代理")
            return
        
        if self.system_proxy_enabled:
            # 关闭系统代理
            if self._set_system_proxy(False):
                self.system_proxy_enabled = False
                self.proxy_btn.setText("设置系统代理")
                self.append_log("[系统] 已关闭系统代理\n")
            else:
                QMessageBox.warning(self, "错误", "关闭系统代理失败")
        else:
            # 开启系统代理
            if self._set_system_proxy(True):
                self.system_proxy_enabled = True
                self.proxy_btn.setText("关闭系统代理")
                self.append_log("[系统] 已设置系统代理\n")
            else:
                QMessageBox.warning(self, "错误", "设置系统代理失败")
    
    def _set_system_proxy(self, enabled):
        """设置系统代理（跨平台）"""
        try:
            # 获取当前监听地址
            listen = self.listen_edit.text()
            if not listen and enabled:
                self.append_log("[系统] 监听地址为空，无法设置系统代理\n")
                return False
            
            # 获取分流模式
            routing_mode = self.routing_combo.currentData()
            if not routing_mode:
                routing_mode = 'bypass_cn'  # 默认值
            
            # 如果是"不改变代理"模式，不设置系统代理
            if routing_mode == 'none':
                if enabled:
                    self.append_log("[系统] 分流模式为\"不改变代理\"，跳过系统代理设置\n")
                return True
            
            # 注意：分流功能已在 Go 程序中实现，系统代理只需设置为全局代理
            # Go 程序会根据 -routing 参数自动处理分流
            
            if sys.platform == 'win32':
                return self._set_windows_proxy(enabled, listen, routing_mode)
            elif sys.platform == 'darwin':
                return self._set_macos_proxy(enabled, listen, routing_mode)
            else:
                self.append_log("[系统] Linux 暂不支持自动设置系统代理\n")
                return False
        except Exception as e:
            self.append_log(f"[系统] 设置系统代理失败: {e}\n")
            import traceback
            self.append_log(f"[系统] 错误详情: {traceback.format_exc()}\n")
            return False
    
    def _get_proxy_bypass_list(self, routing_mode):
        """获取代理绕过列表（分流已在 Go 程序中实现，这里只设置本地和内网绕过）"""
        # 基础绕过列表（本地和内网）
        # 注意：分流功能已在 Go 程序中实现，系统代理设置为全局代理
        # Go 程序会根据分流模式自动决定哪些流量走代理，哪些直连
        base_bypass = "localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;192.168.*;<local>"
        return base_bypass
    
    def _set_windows_proxy(self, enabled, listen, routing_mode):
        """设置 Windows 系统代理"""
        try:
            import winreg
            
            # Internet Settings 注册表路径
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enabled:
                # Windows 11 需要直接使用 IP:端口 格式，不使用 socks= 前缀
                # 解析监听地址，提取 IP 和端口
                if ':' in listen:
                    proxy_server = listen
                else:
                    proxy_server = f"127.0.0.1:{listen}"
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                # 根据分流模式设置绕过列表
                bypass_list = self._get_proxy_bypass_list(routing_mode)
                self.append_log(f"[系统] 设置绕过列表，长度: {len(bypass_list)} 字符\n")
                winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, bypass_list)
                self.append_log(f"[系统] Windows 代理已设置: {proxy_server}, 分流模式: {routing_mode}\n")
            else:
                # 关闭代理
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            winreg.CloseKey(key)
            
            # 通知系统代理设置已更改
            try:
                from ctypes import windll
                INTERNET_OPTION_SETTINGS_CHANGED = 39
                INTERNET_OPTION_REFRESH = 37
                windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
                windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
            except:
                pass
            
            return True
        except Exception as e:
            self.append_log(f"[系统] Windows 代理设置失败: {e}\n")
            return False
    
    def _get_macos_bypass_list(self, routing_mode):
        """获取 macOS 代理绕过列表（分流已在 Go 程序中实现，这里只设置本地和内网绕过）"""
        # 基础绕过列表（本地和内网）
        # 注意：分流功能已在 Go 程序中实现，系统代理设置为全局代理
        # Go 程序会根据分流模式自动决定哪些流量走代理，哪些直连
        base_bypass = [
            "localhost", "127.*", "10.*", "172.16.*", "172.17.*", "172.18.*",
            "172.19.*", "172.20.*", "172.21.*", "172.22.*", "172.23.*", "172.24.*",
            "172.25.*", "172.26.*", "172.27.*", "172.28.*", "172.29.*", "172.30.*",
            "172.31.*", "192.168.*", "*.local", "169.254.*"
        ]
        return base_bypass
    
    def _set_macos_proxy(self, enabled, listen, routing_mode):
        """设置 macOS 系统代理"""
        try:
            # 解析监听地址
            if ':' in listen:
                host, port = listen.rsplit(':', 1)
            else:
                host, port = '127.0.0.1', listen
            
            # 获取当前网络服务名称
            result = subprocess.run(
                ['networksetup', '-listallnetworkservices'],
                capture_output=True, text=True
            )
            
            # 解析网络服务列表（跳过第一行说明）
            services = [line.strip() for line in result.stdout.strip().split('\n')[1:] 
                       if line.strip() and not line.startswith('*')]
            
            # 获取绕过列表
            bypass_list = self._get_macos_bypass_list(routing_mode)
            bypass_string = " ".join(bypass_list)
            
            for service in services:
                try:
                    if enabled:
                        # 设置 SOCKS 代理
                        subprocess.run(
                            ['networksetup', '-setsocksfirewallproxy', service, host, port],
                            capture_output=True, check=True
                        )
                        # 设置绕过列表
                        subprocess.run(
                            ['networksetup', '-setsocksfirewallproxybypassdomains', service] + bypass_list,
                            capture_output=True, check=True
                        )
                        subprocess.run(
                            ['networksetup', '-setsocksfirewallproxystate', service, 'on'],
                            capture_output=True, check=True
                        )
                    else:
                        # 关闭 SOCKS 代理
                        subprocess.run(
                            ['networksetup', '-setsocksfirewallproxystate', service, 'off'],
                            capture_output=True, check=True
                        )
                except subprocess.CalledProcessError:
                    # 某些网络服务可能不支持代理设置，忽略错误
                    pass
            
            return True
        except Exception as e:
            self.append_log(f"[系统] macOS 代理设置失败: {e}\n")
            return False
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果系统托盘可用，最小化到托盘而不是关闭
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                APP_TITLE,
                "程序已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            # 如果没有托盘图标，正常关闭
            # 关闭前清理系统代理
            if self.system_proxy_enabled:
                self._set_system_proxy(False)
                self.append_log("[系统] 程序关闭，已清理系统代理\n")
            
            # 停止进程
            if self.process_thread and self.process_thread.is_running:
                self.process_thread.stop()
                self.process_thread.wait()
            
            event.accept()
    
    def auto_start(self):
        """自动启动"""
        if not (self.process_thread and self.process_thread.is_running):
            server = self.get_control_values()
            if server and server.get('server') and server.get('listen'):
                self.start_process()
                self.append_log("[系统] 开机自动启动代理\n")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
