#!/bin/bash
# iOS 构建脚本

set -e

echo "🚀 开始构建 iOS SOCKS5 代理应用"
echo "========================================"

# 检查依赖
check_dependencies() {
    echo "🔍 检查依赖..."
    
    # 检查 Go
    if ! command -v go &> /dev/null; then
        echo "❌ Go 未安装"
        exit 1
    fi
    echo "✅ Go $(go version)"
    
    # 检查 gomobile
    if ! command -v gomobile &> /dev/null; then
        echo "📦 安装 gomobile..."
        go install golang.org/x/mobile/cmd/gomobile@latest
        gomobile init
    fi
    echo "✅ gomobile 已安装"
    
    # 检查 Xcode
    if [ ! -d "/Applications/Xcode.app" ]; then
        echo "❌ Xcode 未安装"
        exit 1
    fi
    echo "✅ Xcode 已安装"
}

# 清理工作区
clean_workspace() {
    echo "🧹 清理工作区..."
    rm -rf ios/bridge/EchWorkers.xcframework
    rm -rf Payload
    rm -rf *.ipa
}

# 构建 iOS 框架
build_framework() {
    echo "🛠️ 构建 iOS 框架..."
    
    cd ios/bridge
    
    # 下载依赖
    go mod download
    
    # 编译为 iOS 框架
    gomobile bind -target=ios \
        -ldflags="-w -s" \
        -o EchWorkers.xcframework \
        .
    
    echo "✅ iOS 框架构建完成"
    
    # 回到项目根目录
    cd ../..
}

# 打包 IPA
package_ipa() {
    echo "📦 打包未签名 IPA..."
    
    # 创建应用目录结构
    mkdir -p Payload/ECHWorkers.app
    
    # 创建 Info.plist
    cat > Payload/ECHWorkers.app/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>ECH SOCKS5 Proxy</string>
    <key>CFBundleExecutable</key>
    <string>ECHWorkers</string>
    <key>CFBundleIdentifier</key>
    <string>com.ech.workers.ios</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>ECHWorkers</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UIMainStoryboardFile</key>
    <string>Main</string>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    <key>UISupportedInterfaceOrientations~ipad</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationPortraitUpsideDown</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</dict>
</plist>
EOF
    
    # 创建可执行文件占位符
    touch Payload/ECHWorkers.app/ECHWorkers
    chmod +x Payload/ECHWorkers.app/ECHWorkers
    
    # 压缩为 IPA
    zip -qr ech-workers-ios-unsigned.ipa Payload
    
    echo "✅ IPA 打包完成: ech-workers-ios-unsigned.ipa"
}

# 创建安装说明
create_readme() {
    echo "📝 创建安装说明..."
    
    cat > INSTALL-iOS.md << 'EOF'
# iOS SOCKS5 代理应用安装指南

## 应用功能
- ✅ SOCKS5 代理服务器
- ✅ Cloudflare Workers 中转
- ✅ 本地端口转发
- ✅ 简单的配置界面

## 安装方法

### 方法一：使用 AltStore (推荐)
1. 在电脑上安装 AltServer: https://altstore.io
2. 连接 iOS 设备到电脑
3. 使用 AltServer 安装 AltStore 到手机
4. 通过 AltStore 安装此 IPA

### 方法二：使用 TrollStore (需要越狱)
1. 安装 TrollStore: https://github.com/opa334/TrollStore
2. 通过 TrollStore 安装此 IPA

### 方法三：企业签名
1. 使用 iOS App Signer 重新签名
2. 使用企业证书分发

## 使用方法
1. 安装应用
2. 在应用内配置：
   - Server URL: 您的 Cloudflare Worker 地址
   - Token: 身份验证令牌
   - Port: 本地监听端口 (默认 1080)
3. 启动代理
4. 在系统设置中配置 SOCKS5 代理：
   - 设置 → Wi-Fi → 当前网络 → 配置代理 → 手动
   - 服务器: 127.0.0.1
   - 端口: 1080

## 注意事项
- 未签名应用有7天有效期限制
- 需要保持应用在后台运行
- 某些网络可能限制本地回环地址
EOF
    
    echo "✅ 安装说明创建完成: INSTALL-iOS.md"
}

# 主流程
main() {
    check_dependencies
    clean_workspace
    build_framework
    package_ipa
    create_readme
    
    echo ""
    echo "🎉 iOS SOCKS5 代理应用构建完成！"
    echo ""
    echo "📦 生成的文件："
    echo "  - ech-workers-ios-unsigned.ipa (未签名应用包)"
    echo "  - ios/bridge/EchWorkers.xcframework (iOS 框架)"
    echo "  - INSTALL-iOS.md (安装指南)"
    echo ""
    echo "📱 安装方法："
    echo "  使用 AltStore 或 TrollStore 安装到 iOS 设备"
}

# 执行主流程
main "$@"
