#!/bin/bash
# ComfyUI 许可证管理器 - 服务器安装脚本

echo "🚀 开始安装 ComfyUI 许可证管理器..."

# 检查参数
COMFYUI_PATH="${1}"
if [ -z "$COMFYUI_PATH" ]; then
    echo "❌ 请指定ComfyUI安装路径"
    echo "💡 用法: ./install.sh /path/to/ComfyUI"
    exit 1
fi

if [ ! -d "$COMFYUI_PATH" ]; then
    echo "❌ ComfyUI路径不存在: $COMFYUI_PATH"
    exit 1
fi

# 设置插件目录
PLUGIN_DIR="$COMFYUI_PATH/custom_nodes/ComfyUI-License-Manager"

# 创建插件目录
echo "📁 创建插件目录..."
mkdir -p "$PLUGIN_DIR"

# 复制文件
echo "📋 复制插件文件..."
cp -r ./* "$PLUGIN_DIR/"

# 安装依赖
echo "📦 安装Python依赖..."
cd "$PLUGIN_DIR"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
fi

# 设置权限
echo "🔐 设置文件权限..."
chmod -R 755 "$PLUGIN_DIR"

echo "🎉 安装完成！"
echo "💡 请重启ComfyUI以加载插件"
echo "📝 访问 http://your-server:port 查看许可证验证页面"
