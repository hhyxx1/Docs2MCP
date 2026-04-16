#!/bin/bash

# Docs2MCP Flutter环境设置脚本
echo "============================================="
echo "Docs2MCP Flutter 环境设置"
echo "============================================="

# Flutter路径
FLUTTER_PATH="/home/hyx/Projects/clone/flutter/bin"

# 检查Flutter路径
if [ ! -d "$FLUTTER_PATH" ]; then
    echo "错误: Flutter路径不存在: $FLUTTER_PATH"
    exit 1
fi

# 设置环境变量
export PATH="$FLUTTER_PATH:$PATH"
export FLUTTER_ROOT="$FLUTTER_PATH/.."

echo ""
echo "Flutter 环境变量已设置"
echo "  FLUTTER_ROOT: $FLUTTER_ROOT"
echo "  PATH: $FLUTTER_PATH"
echo ""

# 检查Flutter是否可用
echo "正在检查Flutter..."
flutter --version

if [ $? -ne 0 ]; then
    echo "错误: Flutter无法正常运行"
    exit 1
fi

echo ""
echo "============================================="
echo "Flutter环境设置完成！"
echo "============================================="
echo ""
echo "下一步:"
echo "  1. 进入flutter-app目录"
echo "  2. 运行 flutter pub get 安装依赖"
echo "  3. 运行 flutter create . 生成平台文件（如果需要）"
echo "  4. 运行 flutter build linux 或 flutter build apk"
echo ""
