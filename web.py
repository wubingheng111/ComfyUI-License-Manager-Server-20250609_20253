"""
ComfyUI License Manager Web API模块 - 完整版本
"""

import json
import os
from aiohttp import web

try:
    from .license_manager import license_validator
except ImportError:
    from license_manager import license_validator

def setup_license_routes(app):
    """设置许可证相关的路由"""
    current_dir = os.path.dirname(__file__)
    static_dir = os.path.join(current_dir, "static")
    
    # 确保目录存在
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 创建静态文件
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
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
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
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
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
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        else:
            return web.Response(status=404)
    
    # API路由
    async def validate_license_api(request):
        """验证卡密API"""
        try:
            json_data = await request.json()
            license_key = json_data.get("license_key", "").strip()
        except Exception as e:
            return web.json_response({"error": f"JSON解析失败: {str(e)}"}, status=400)
        
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
        try:
            json_data = await request.json()
            license_key = json_data.get("license_key", "").strip()
        except Exception as e:
            return web.json_response({"error": f"JSON解析失败: {str(e)}"}, status=400)
        
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
    
    # 创建完整的JavaScript注入脚本
    js_content = create_license_injection_script()
    
    js_path = os.path.join(static_dir, "license_injection.js")
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    # 创建CSS样式文件
    css_content = create_css_styles()
    
    css_path = os.path.join(static_dir, "style.css")
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print("[ComfyUI-License-Manager] 静态文件已创建")

def create_license_injection_script():
    """创建许可证注入脚本"""
    return '''// ComfyUI 卡密验证拦截器 - 完整版本
(function() {
    'use strict';

    let originalFetch = window.fetch;
    let licenseKey = '';  // 不从localStorage读取，每次都需要重新输入
    let dialogShown = false;

    // 重写fetch函数来拦截所有请求
    window.fetch = function(url, options) {
        console.log('[License] 拦截请求:', url, options?.method);
        
        // 检查是否是需要验证的请求
        const needsLicense = (
            (url.includes('/prompt') && options?.method === 'POST') ||
            (url.includes('/queue') && options?.method === 'POST') ||
            (url.includes('/interrupt') && options?.method === 'POST') ||
            (url.includes('/api/') && options?.method === 'POST') ||
            url.includes('/upload/') ||
            url.includes('/view') ||
            url.includes('/history')
        );
        
        if (needsLicense) {
            console.log('[License] 需要验证的请求:', url);
            
            if (!licenseKey) {
                console.log('[License] 没有卡密，显示对话框');
                showLicenseDialog();
                return Promise.reject(new Error('🔒 需要提供有效的卡密才能使用ComfyUI'));
            }

            if (options && options.body) {
                try {
                    const body = JSON.parse(options.body);
                    body.license_key = licenseKey;
                    options.body = JSON.stringify(body);
                    console.log('[License] 已添加卡密到请求');
                } catch (e) {
                    console.error('[License] 添加卡密失败:', e);
                }
            } else if (options) {
                options.body = JSON.stringify({ license_key: licenseKey });
                options.headers = options.headers || {};
                options.headers['Content-Type'] = 'application/json';
            }
        }

        return originalFetch.call(this, url, options);
    };

    // 拦截所有交互事件
    ['click', 'mousedown', 'keydown', 'submit'].forEach(eventType => {
        document.addEventListener(eventType, function(e) {
            if (!licenseKey && !e.target.closest('#licenseDialog')) {
                if (eventType === 'keydown') {
                    const allowedKeys = ['Tab', 'F5', 'F12', 'Escape', 'Enter'];
                    if (allowedKeys.includes(e.key) || e.ctrlKey) return;
                }
                
                console.log('[License] 拦截事件:', eventType);
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                showLicenseDialog();
                return false;
            }
        }, true);
    });

    // 定期检查保护状态
    setInterval(function() {
        if (!licenseKey) {
            hidePageContent();
            if (!dialogShown) {
                showLicenseDialog();
                dialogShown = true;
            }
        }
    }, 2000);

    // 显示卡密输入对话框
    function showLicenseDialog() {
        const existingDialog = document.getElementById('licenseDialog');
        if (existingDialog) {
            existingDialog.remove();
        }

        dialogShown = true;

        const dialog = document.createElement('div');
        dialog.id = 'licenseDialog';
        dialog.innerHTML = createDialogHTML();
        document.body.appendChild(dialog);

        setupDialogEvents(dialog);
    }

    function createDialogHTML() {
        return \`<div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%); display: flex; align-items: center; justify-content: center; z-index: 999999; backdrop-filter: blur(10px);">
            <div style="background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%); border-radius: 20px; padding: 40px; max-width: 550px; width: 90%; box-shadow: 0 25px 60px rgba(0,0,0,0.3);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 64px; margin-bottom: 20px;">🔐</div>
                    <h2 style="margin: 0; color: #2c3e50; font-size: 28px; font-weight: 700;">ComfyUI 授权验证</h2>
                    <p style="color: #7f8c8d; margin: 10px 0; font-size: 16px;">请输入您的授权卡密以继续使用<br><span style="color: #e74c3c; font-weight: 600;">每次使用都需要重新验证</span></p>
                </div>
                <div style="margin-bottom: 25px;">
                    <label style="display: block; margin-bottom: 12px; color: #2c3e50; font-weight: 700; font-size: 14px;">🔑 授权卡密</label>
                    <input type="text" id="licenseInput" placeholder="请输入您的授权卡密..." style="width: 100%; padding: 18px 20px; border: 3px solid #e9ecef; border-radius: 12px; font-size: 16px; font-family: 'Courier New', monospace; box-sizing: border-box;">
                </div>
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <button id="validateBtn" style="flex: 2; padding: 18px 30px; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">🚀 验证卡密</button>
                    <button id="licensePageBtn" style="flex: 1; padding: 18px 25px; border: 2px solid #e9ecef; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer; background: #f8f9fa; color: #6c757d;">📋 管理</button>
                </div>
                <div id="dialogStatus" style="margin-top: 20px; padding: 15px 20px; border-radius: 10px; text-align: center; display: none; font-weight: 600; font-size: 14px;"></div>
                <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; text-align: center;">
                    <p style="color: #95a5a6; font-size: 12px; margin: 0;">🛡️ 安全提示：每次使用都需要重新验证<br>💡 如需帮助，请联系管理员<br>⌨️ 快捷键：按 Enter 键快速验证</p>
                </div>
            </div>
        </div>\`;
    }

    function setupDialogEvents(dialog) {
        const input = document.getElementById('licenseInput');
        const validateBtn = document.getElementById('validateBtn');
        const licensePageBtn = document.getElementById('licensePageBtn');
        const status = document.getElementById('dialogStatus');

        input.focus();

        validateBtn.onclick = async function() {
            const key = input.value.trim();
            if (!key) {
                showDialogStatus('请输入卡密', 'error');
                return;
            }

            showDialogStatus('正在验证...', 'loading');
            validateBtn.disabled = true;
            validateBtn.innerHTML = '⏳ 验证中...';

            try {
                const response = await originalFetch('/license/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ license_key: key })
                });

                const result = await response.json();

                if (result.valid) {
                    licenseKey = key;
                    showDialogStatus('✅ 验证成功！', 'success');
                    validateBtn.innerHTML = '🎉 验证成功';

                    setTimeout(() => {
                        showPageContent();
                        dialog.style.opacity = '0';
                        setTimeout(() => {
                            document.body.removeChild(dialog);
                            dialogShown = false;
                        }, 500);
                    }, 2000);
                } else {
                    showDialogStatus('❌ ' + (result.message || '验证失败'), 'error');
                    validateBtn.disabled = false;
                    validateBtn.innerHTML = '🚀 验证卡密';
                }
            } catch (error) {
                showDialogStatus('❌ 验证请求失败', 'error');
                validateBtn.disabled = false;
                validateBtn.innerHTML = '🚀 验证卡密';
            }
        };

        licensePageBtn.onclick = function() {
            window.open('/license_dialog.html', '_blank');
        };

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                validateBtn.click();
            }
        });

        function showDialogStatus(message, type) {
            status.textContent = message;
            status.style.display = 'block';

            if (type === 'success') {
                status.style.background = 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)';
                status.style.color = '#155724';
                status.style.border = '2px solid #27ae60';
            } else if (type === 'error') {
                status.style.background = 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)';
                status.style.color = '#721c24';
                status.style.border = '2px solid #e74c3c';
            } else {
                status.style.background = 'linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%)';
                status.style.color = '#0c5460';
                status.style.border = '2px solid #3498db';
            }
        }
    }

    // 页面内容控制函数
    function hidePageContent() {
        if (!licenseKey) {
            const body = document.body;
            if (body && !body.classList.contains('license-hidden')) {
                body.style.filter = 'blur(5px)';
                body.style.pointerEvents = 'none';
                body.style.userSelect = 'none';
                body.classList.add('license-hidden');
            }
        }
    }

    function showPageContent() {
        const body = document.body;
        if (body && body.classList.contains('license-hidden')) {
            body.style.filter = '';
            body.style.pointerEvents = '';
            body.style.userSelect = '';
            body.classList.remove('license-hidden');
        }
    }

    // 页面加载时立即显示卡密对话框
    document.addEventListener('DOMContentLoaded', function() {
        if (!dialogShown) {
            showLicenseDialog();
            dialogShown = true;
        }
        hidePageContent();
    });

    // 页面可见性变化时重新验证
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            licenseKey = '';
            hidePageContent();
            if (!dialogShown) {
                setTimeout(() => {
                    showLicenseDialog();
                    dialogShown = true;
                }, 500);
            }
        }
    });

    // 窗口焦点变化时重新验证
    window.addEventListener('focus', function() {
        licenseKey = '';
        hidePageContent();
        if (!dialogShown) {
            setTimeout(() => {
                showLicenseDialog();
                dialogShown = true;
            }, 500);
        }
    });

})();'''

def create_css_styles():
    """创建CSS样式"""
    return '''/* ComfyUI License Manager 样式 */
* {
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
}'''

# 在模块加载时创建静态文件
create_static_files()
