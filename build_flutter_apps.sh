#!/bin/bash

# Docs2MCP Flutter应用构建脚本
set -e

echo "============================================="
echo "Docs2MCP Flutter 应用构建"
echo "============================================="

# Flutter路径
FLUTTER_PATH="/home/hyx/Projects/clone/flutter/bin"
export PATH="$FLUTTER_PATH:$PATH"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/flutter-app"
cd "$PROJECT_DIR"

echo ""
echo "项目目录: $PROJECT_DIR"
echo "============================================="
echo ""

# 检查是否有平台文件
echo "[1/5] 检查项目平台文件..."
if [ ! -d "android" ] || [ ! -d "linux" ]; then
    echo "  平台文件不存在，正在生成..."
    flutter create . --platforms=android,linux
else
    echo "  平台文件已存在"
fi
echo ""

# 安装依赖
echo "[2/5] 安装Flutter依赖..."
flutter pub get
echo ""

# 构建Linux版本
echo "[3/5] 构建Linux版本..."
flutter build linux --release
if [ $? -eq 0 ]; then
    echo "  ✅ Linux构建成功!"
    echo "  输出目录: $PROJECT_DIR/build/linux/x64/release/bundle/"
else
    echo "  ❌ Linux构建失败"
fi
echo ""

# 构建Android版本
echo "[4/5] 构建Android APK..."
flutter build apk --release
if [ $? -eq 0 ]; then
    echo "  ✅ Android APK构建成功!"
    echo "  输出文件: $PROJECT_DIR/build/app/outputs/flutter-apk/app-release.apk"
else
    echo "  ❌ Android APK构建失败"
fi
echo ""

echo "============================================="
echo "构建完成!"
echo "============================================="
echo ""
echo "输出位置:"
echo "  Linux: $PROJECT_DIR/build/linux/x64/release/bundle/"
echo "  Android: $PROJECT_DIR/build/app/outputs/flutter-apk/app-release.apk"
echo ""
