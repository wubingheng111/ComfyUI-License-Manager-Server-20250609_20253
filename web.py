"""
ComfyUI License Manager Web API模块
"""

import json
import os
from aiohttp import web

try:
    from .license_manager import license_validator
except ImportError:
    from license_manager import license_validator

def setup_license_routes(app):
    """设置许可证相关的所有路由"""
    
    # 获取当前文件夹路径
    current_dir = os.path.dirname(__file__)
    static_dir = os.path.join(current_dir, "static")
    
    # 确保静态文件目录存在
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 创建所有静态文件（如果不存在）
    create_static_files()
    
    # 主页卡密验证脚本注入路由
    async def get_license_injection_script(request):
        """返回用于注入主页的卡密验证脚本"""
        script_path = os.path.join(static_dir, "license_injection.js")
        
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            response = web.Response(text=content, content_type='application/javascript')
            response.headers['Cache-Control'] = 'no-cache'
            return response
        else:
            return web.Response(status=404)
    
    # 卡密管理页面路由
    async def get_license_dialog(request):
        """返回卡密管理页面"""
        dialog_path = os.path.join(static_dir, "license_dialog.html")
        
        if os.path.exists(dialog_path):
            with open(dialog_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            response = web.Response(text=content, content_type='text/html')
            response.headers['Cache-Control'] = 'no-cache'
            return response
        else:
            return web.Response(status=404)
    
    # CSS文件路由
    async def get_license_css(request):
        """返回CSS样式文件"""
        css_path = os.path.join(static_dir, "style.css")
        
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            response = web.Response(text=content, content_type='text/css')
            response.headers['Cache-Control'] = 'no-cache'
            return response
        else:
            return web.Response(status=404)
    
    # API路由
    async def validate_license_api(request):
        """验证卡密API"""
        json_data = await request.json()
        license_key = json_data.get("license_key")
        
        if not license_key:
            return web.json_response({"error": "卡密不能为空"}, status=400)
        
        is_valid, result = license_validator.validate_license(license_key)
        
        if is_valid:
            license_info = result
            message = "验证成功"
        else:
            license_info = None
            message = result
        
        if is_valid:
            return web.json_response({
                "valid": True,
                "message": message,
                "license_info": license_info
            })
        else:
            return web.json_response({
                "valid": False,
                "message": message,
                "license_info": license_info
            }, status=401)
    
    async def get_license_config(request):
        """获取许可证配置信息"""
        config_info = license_validator.get_config_info()
        return web.json_response(config_info)
    
    async def check_license_info(request):
        """查询卡密信息"""
        json_data = await request.json()
        license_key = json_data.get("license_key")
        
        if not license_key:
            return web.json_response({"error": "卡密不能为空"}, status=400)
        
        is_valid, result = license_validator.get_license_info(license_key)
        
        if is_valid:
            return web.json_response(result)
        else:
            return web.json_response({"error": result}, status=400)
    
    # 添加路由
    app.router.add_get('/license_injection.js', get_license_injection_script)
    app.router.add_get('/license_dialog.html', get_license_dialog)
    app.router.add_get('/license_static/style.css', get_license_css)
    
    app.router.add_post('/license/validate', validate_license_api)
    app.router.add_get('/license/config', get_license_config)
    app.router.add_post('/license/info', check_license_info)

def create_static_files():
    """创建所有必要的静态文件"""
    current_dir = os.path.dirname(__file__)
    static_dir = os.path.join(current_dir, "static")
    
    # 确保目录存在
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 创建JavaScript注入脚本
    js_content = '''// ComfyUI 卡密验证拦截器
(function() {
    'use strict';

    let originalFetch = window.fetch;
    let licenseKey = localStorage.getItem('comfyui_license_key') || '';

    // 重写fetch函数来拦截prompt请求
    window.fetch = function(url, options) {
        // 检查是否是prompt提交请求
        if (url.includes('/prompt') && options && options.method === 'POST') {
            // 如果没有卡密，显示输入对话框
            if (!licenseKey) {
                showLicenseDialog();
                return Promise.reject(new Error('需要提供有效的卡密才能使用'));
            }

            // 在请求中添加license_key
            if (options.body) {
                try {
                    const body = JSON.parse(options.body);
                    body.license_key = licenseKey;
                    options.body = JSON.stringify(body);
                } catch (e) {
                    console.error('Error adding license key to request:', e);
                }
            }
        }

        return originalFetch.call(this, url, options);
    };

    // 显示卡密输入对话框
    function showLicenseDialog() {
        // 检查是否已经有对话框
        if (document.getElementById('licenseDialog')) {
            return;
        }

        const dialog = document.createElement('div');
        dialog.id = 'licenseDialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            ">
                <div style="
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    max-width: 500px;
                    width: 90%;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                ">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <div style="font-size: 48px; margin-bottom: 15px;">🔐</div>
                        <h2 style="margin: 0; color: #333;">需要卡密验证</h2>
                        <p style="color: #666; margin-top: 10px;">请输入您的授权卡密以继续使用ComfyUI</p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; color: #555; font-weight: 600;">卡密:</label>
                        <input type="text" id="licenseInput" placeholder="请输入您的卡密..." style="
                            width: 100%;
                            padding: 15px;
                            border: 2px solid #e1e1e1;
                            border-radius: 8px;
                            font-size: 16px;
                            box-sizing: border-box;
                        ">
                    </div>
                    
                    <div style="display: flex; gap: 15px;">
                        <button id="validateBtn" style="
                            flex: 1;
                            padding: 15px 25px;
                            border: none;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: 600;
                            cursor: pointer;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                        ">验证卡密</button>
                        <button id="licensePageBtn" style="
                            flex: 1;
                            padding: 15px 25px;
                            border: 2px solid #e9ecef;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: 600;
                            cursor: pointer;
                            background: #f8f9fa;
                            color: #6c757d;
                        ">卡密管理</button>
                    </div>
                    
                    <div id="dialogStatus" style="
                        margin-top: 15px;
                        padding: 10px;
                        border-radius: 5px;
                        text-align: center;
                        display: none;
                    "></div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // 绑定事件
        const input = document.getElementById('licenseInput');
        const validateBtn = document.getElementById('validateBtn');
        const licensePageBtn = document.getElementById('licensePageBtn');
        const status = document.getElementById('dialogStatus');

        // 加载保存的卡密
        if (licenseKey) {
            input.value = licenseKey;
        }

        // 验证按钮事件
        validateBtn.onclick = async function() {
            const key = input.value.trim();
            if (!key) {
                showDialogStatus('请输入卡密', 'error');
                return;
            }

            showDialogStatus('正在验证...', 'loading');
            
            try {
                const response = await originalFetch('/license/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ license_key: key })
                });

                const result = await response.json();
                
                if (result.valid) {
                    licenseKey = key;
                    localStorage.setItem('comfyui_license_key', key);
                    showDialogStatus('✅ 验证成功！', 'success');
                    setTimeout(() => {
                        document.body.removeChild(dialog);
                    }, 1500);
                } else {
                    showDialogStatus('❌ ' + (result.message || '验证失败'), 'error');
                }
            } catch (error) {
                showDialogStatus('❌ 验证请求失败', 'error');
            }
        };

        // 卡密管理页面按钮事件
        licensePageBtn.onclick = function() {
            window.open('/license_dialog.html', '_blank');
        };

        // 回车键验证
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                validateBtn.click();
            }
        });

        function showDialogStatus(message, type) {
            status.textContent = message;
            status.style.display = 'block';
            status.style.background = type === 'success' ? '#d4edda' : 
                                     type === 'error' ? '#f8d7da' : '#d1ecf1';
            status.style.color = type === 'success' ? '#155724' : 
                                type === 'error' ? '#721c24' : '#0c5460';
            status.style.border = type === 'success' ? '1px solid #c3e6cb' : 
                                 type === 'error' ? '1px solid #f5c6cb' : '1px solid #bee5eb';
        }
    }

    // 页面加载时检查卡密状态
    document.addEventListener('DOMContentLoaded', function() {
        if (licenseKey) {
            // 验证已保存的卡密
            originalFetch('/license/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ license_key: licenseKey })
            }).then(response => response.json())
            .then(result => {
                if (!result.valid) {
                    localStorage.removeItem('comfyui_license_key');
                    licenseKey = '';
                }
            }).catch(() => {
                // 网络错误时保持卡密
            });
        }

        // 添加卡密管理按钮到菜单
        addLicenseButton();
    });

    // 添加卡密管理按钮
    function addLicenseButton() {
        setTimeout(() => {
            const menuBar = document.querySelector('.comfy-menu') || document.querySelector('#app');
            if (menuBar && !document.getElementById('licenseMenuBtn')) {
                const button = document.createElement('button');
                button.id = 'licenseMenuBtn';
                button.innerHTML = '🔐 卡密管理';
                button.style.cssText = `
                    margin-left: 10px;
                    padding: 5px 10px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 12px;
                `;
                button.onclick = () => window.open('/license_dialog.html', '_blank');
                menuBar.appendChild(button);
            }
        }, 2000);
    }

})();'''
    
    js_path = os.path.join(static_dir, "license_injection.js")
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    # 创建CSS样式文件
    css_content = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #333;
}

.container {
    background: white;
    border-radius: 20px;
    box-shadow: 0 25px 60px rgba(0,0,0,0.2);
    padding: 40px;
    width: 100%;
    max-width: 600px;
    margin: 20px;
}

.header {
    text-align: center;
    margin-bottom: 40px;
}

.header h1 {
    font-size: 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
}

.header p {
    color: #666;
    font-size: 16px;
}

.section {
    margin-bottom: 40px;
    padding: 30px;
    background: #f8f9fa;
    border-radius: 15px;
    border-left: 5px solid #667eea;
}

.section h3 {
    color: #667eea;
    margin-bottom: 20px;
    font-size: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.form-group {
    margin-bottom: 25px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #555;
}

.form-group input {
    width: 100%;
    padding: 15px;
    border: 2px solid #e1e1e1;
    border-radius: 10px;
    font-size: 16px;
    transition: all 0.3s ease;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-right: 15px;
    margin-bottom: 10px;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
    background: #6c757d;
}

.btn-danger {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
}

.status {
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
    font-weight: 500;
    display: none;
}

.status.success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.status.info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

.license-info {
    background: #e3f2fd;
    padding: 20px;
    border-radius: 10px;
    margin-top: 20px;
}

.license-info h4 {
    color: #1565c0;
    margin-bottom: 15px;
}

.license-info p {
    margin-bottom: 8px;
    color: #1976d2;
}

.contact-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-left: none;
}

.contact-section h3 {
    color: white;
}

.contact-links {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.contact-item {
    background: rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    transition: all 0.3s ease;
}

.contact-item:hover {
    background: rgba(255,255,255,0.2);
    transform: translateY(-2px);
}

.contact-item .icon {
    font-size: 30px;
    margin-bottom: 10px;
}

.contact-item .label {
    font-weight: 600;
    margin-bottom: 5px;
}

.contact-item .value {
    font-size: 14px;
    opacity: 0.9;
}'''
    
    css_path = os.path.join(static_dir, "style.css")
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print("[ComfyUI-License-Manager] 静态文件已创建")

# 在模块加载时创建静态文件
create_static_files() 