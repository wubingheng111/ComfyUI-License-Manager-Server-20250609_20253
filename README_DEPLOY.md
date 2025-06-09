# ComfyUI 许可证管理器 - 服务器部署包

## 📦 包含文件

- `__init__.py` - 插件主文件
- `web.py` - Web验证界面
- `license_manager.py` - 许可证验证逻辑
- `license_config.json` - 服务器配置文件（包含加密密钥）
- `requirements.txt` - Python依赖
- `web/` - 验证页面模板
- `static/` - 静态资源文件
- `js/` - JavaScript文件
- `install.sh` - Linux安装脚本
- `install.bat` - Windows安装脚本

## 🚀 快速部署

### Linux/Mac 服务器

1. **上传文件**
   ```bash
   # 将整个文件夹上传到服务器
   scp -r ComfyUI-License-Manager user@server:/tmp/
   ```

2. **运行安装脚本**
   ```bash
   cd /tmp/ComfyUI-License-Manager
   chmod +x install.sh
   ./install.sh /path/to/ComfyUI
   ```

### Windows 服务器

1. **上传文件**
   - 将整个文件夹复制到服务器

2. **运行安装脚本**
   ```cmd
   cd ComfyUI-License-Manager
   install.bat "C:\path\to\ComfyUI"
   ```

## ⚙️ 手动安装

如果自动脚本有问题，可以手动安装：

1. **创建插件目录**
   ```bash
   mkdir -p /path/to/ComfyUI/custom_nodes/ComfyUI-License-Manager
   ```

2. **复制文件**
   ```bash
   cp -r ./* /path/to/ComfyUI/custom_nodes/ComfyUI-License-Manager/
   ```

3. **安装依赖**
   ```bash
   cd /path/to/ComfyUI/custom_nodes/ComfyUI-License-Manager
   pip install -r requirements.txt
   ```

4. **重启ComfyUI**

## 🔧 配置说明

- `license_config.json` 包含验证所需的加密密钥
- 此文件由管理员端生成，包含与生成的卡密匹配的密钥
- 不要修改此文件的内容

## 🌐 验证流程

1. 用户访问ComfyUI时会自动跳转到许可证验证页面
2. 用户输入管理员提供的卡密
3. 系统验证卡密的有效性、过期时间、使用次数
4. 验证成功后跳转到ComfyUI界面

## 📞 故障排除

### 插件无法加载
- 检查文件权限：`chmod -R 755 /path/to/plugin`
- 检查Python依赖是否安装成功
- 查看ComfyUI启动日志

### 验证页面无法访问
- 检查`license_config.json`是否存在
- 检查配置文件格式是否正确
- 确认端口没有被防火墙阻止

### 卡密验证失败
- 确认卡密没有过期
- 检查使用次数是否已用完
- 确认配置文件中的加密密钥正确

## 🔒 安全注意事项

1. **保护配置文件**
   - `license_config.json`包含重要的加密密钥
   - 不要将此文件暴露在公网
   - 定期备份配置文件

2. **网络安全**
   - 建议使用HTTPS访问
   - 配置防火墙规则
   - 定期更新系统补丁

3. **访问控制**
   - 限制服务器访问权限
   - 使用强密码
   - 启用日志记录

---

📅 生成时间: 2025-06-09 21:00:59
🔧 管理员工具版本: v1.0.0
