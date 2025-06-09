// ComfyUI 卡密验证拦截器
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

})();