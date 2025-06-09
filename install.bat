@echo off
REM ComfyUI 许可证管理器 - 服务器安装脚本

echo 🚀 开始安装 ComfyUI 许可证管理器...

REM 检查参数
if "%1"=="" (
    echo ❌ 请指定ComfyUI安装路径
    echo 💡 用法: install.bat "C:\path\to\ComfyUI"
    pause
    exit /b 1
)

set COMFYUI_PATH=%~1
if not exist "%COMFYUI_PATH%" (
    echo ❌ ComfyUI路径不存在: %COMFYUI_PATH%
    pause
    exit /b 1
)

REM 设置插件目录
set PLUGIN_DIR=%COMFYUI_PATH%\custom_nodes\ComfyUI-License-Manager

REM 创建插件目录
echo 📁 创建插件目录...
mkdir "%PLUGIN_DIR%" 2>nul

REM 复制文件
echo 📋 复制插件文件...
xcopy /E /H /Y *.* "%PLUGIN_DIR%\"

REM 安装依赖
echo 📦 安装Python依赖...
cd /d "%PLUGIN_DIR%"
if exist requirements.txt (
    pip install -r requirements.txt
    echo ✅ 依赖安装完成
)

echo 🎉 安装完成！
echo 💡 请重启ComfyUI以加载插件
echo 📝 访问 http://your-server:port 查看许可证验证页面
pause
