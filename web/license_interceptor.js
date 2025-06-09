/**
 * ComfyUI License Manager - 前端许可证拦截器
 * 自动拦截API请求，检查并添加许可证验证
 */

(function() {
    'use strict';
    
    // 许可证管理器类
    class LicenseManager {
        constructor() {
            this.licenseKey = localStorage.getItem('comfyui_license_key');
            this.isValidating = false;
            this.pendingRequests = [];
            
            // 初始化
            this.init();
        }
        
        init() {
            // 拦截fetch请求
            this.interceptFetch();
            
            // 添加许可证管理按钮
            this.addLicenseButton();
            
            // 监听存储变化
            this.listenStorageChanges();
        }
        
        interceptFetch() {
            const originalFetch = window.fetch;
            const self = this;
            
            window.fetch = async function(...args) {
                const [url, options = {}] = args;
                
                // 只拦截POST /prompt请求
                if (url.includes('/prompt') && options.method === 'POST') {
                    return self.handlePromptRequest(originalFetch, url, options);
                }
                
                return originalFetch.apply(this, args);
            };
        }
        
        async handlePromptRequest(originalFetch, url, options) {
            // 如果正在验证许可证，将请求加入队列
            if (this.isValidating) {
                return new Promise((resolve, reject) => {
                    this.pendingRequests.push({ originalFetch, url, options, resolve, reject });
                });
            }
            
            // 检查许可证
            if (!this.licenseKey) {
                await this.showLicenseDialog();
                
                // 验证失败，拒绝请求
                if (!this.licenseKey) {
                    throw new Error('需要有效的许可证才能执行此操作');
                }
            }
            
            // 添加许可证到请求
            const body = JSON.parse(options.body || '{}');
            body.license_key = this.licenseKey;
            options.body = JSON.stringify(body);
            
            try {
                const response = await originalFetch(url, options);
                
                // 检查响应
                if (response.status === 403) {
                    const errorData = await response.json();
                    if (errorData.license_required) {
                        // 许可证无效，清除并重新验证
                        this.clearLicense();
                        await this.showLicenseDialog();
                        
                        if (this.licenseKey) {
                            // 重新发送请求
                            const newBody = JSON.parse(options.body);
                            newBody.license_key = this.licenseKey;
                            options.body = JSON.stringify(newBody);
                            return originalFetch(url, options);
                        } else {
                            throw new Error(errorData.error || '许可证验证失败');
                        }
                    }
                }
                
                return response;
            } catch (error) {
                console.error('License Manager: 请求失败', error);
                throw error;
            }
        }
        
        async showLicenseDialog() {
            if (this.isValidating) return;
            
            this.isValidating = true;
            
            try {
                // 创建模态对话框
                const dialog = this.createLicenseDialog();
                document.body.appendChild(dialog);
                
                // 等待用户操作
                await this.waitForLicenseInput(dialog);
                
            } finally {
                this.isValidating = false;
                // 处理pending的请求
                this.processPendingRequests();
            }
        }
        
        createLicenseDialog() {
            const dialog = document.createElement('div');
            dialog.id = 'license-dialog';
            dialog.innerHTML = `
                <div class="license-overlay">
                    <div class="license-modal">
                        <div class="license-header">
                            <h2>🔐 许可证验证</h2>
                            <p>请输入有效的许可证密钥来继续使用</p>
                        </div>
                        
                        <div class="license-form">
                            <input type="text" id="license-input" placeholder="请输入许可证密钥..." />
                            <div class="license-buttons">
                                <button id="validate-btn" class="btn-primary">验证许可证</button>
                                <button id="cancel-btn" class="btn-secondary">取消</button>
                                <button id="contact-btn" class="btn-contact">购买许可证</button>
                            </div>
                            <div id="license-message" class="license-message"></div>
                        </div>
                    </div>
                </div>
            `;
            
            // 添加样式
            const style = document.createElement('style');
            style.textContent = `
                .license-overlay {
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
                    backdrop-filter: blur(5px);
                }
                
                .license-modal {
                    background: white;
                    padding: 30px;
                    border-radius: 15px;
                    max-width: 500px;
                    width: 90%;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                    animation: licenseSlideIn 0.3s ease-out;
                }
                
                @keyframes licenseSlideIn {
                    from {
                        opacity: 0;
                        transform: translateY(-30px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .license-header {
                    text-align: center;
                    margin-bottom: 25px;
                }
                
                .license-header h2 {
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 1.5rem;
                }
                
                .license-header p {
                    color: #666;
                    margin: 0;
                }
                
                .license-form {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                
                #license-input {
                    padding: 12px 15px;
                    border: 2px solid #e1e8ed;
                    border-radius: 8px;
                    font-size: 14px;
                    transition: border-color 0.3s ease;
                }
                
                #license-input:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                .license-buttons {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                
                .license-buttons button {
                    flex: 1;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    min-width: 120px;
                }
                
                .btn-primary {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                }
                
                .btn-primary:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
                }
                
                .btn-secondary {
                    background: #f8f9fa;
                    color: #667eea;
                    border: 2px solid #667eea;
                }
                
                .btn-secondary:hover {
                    background: #667eea;
                    color: white;
                }
                
                .btn-contact {
                    background: #28a745;
                    color: white;
                }
                
                .btn-contact:hover {
                    background: #218838;
                    transform: translateY(-2px);
                }
                
                .license-message {
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                    font-size: 14px;
                    min-height: 20px;
                }
                
                .license-message.success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .license-message.error {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                
                @media (max-width: 600px) {
                    .license-buttons {
                        flex-direction: column;
                    }
                    
                    .license-buttons button {
                        min-width: auto;
                    }
                }
            `;
            dialog.appendChild(style);
            
            return dialog;
        }
        
        async waitForLicenseInput(dialog) {
            return new Promise((resolve) => {
                const input = dialog.querySelector('#license-input');
                const validateBtn = dialog.querySelector('#validate-btn');
                const cancelBtn = dialog.querySelector('#cancel-btn');
                const contactBtn = dialog.querySelector('#contact-btn');
                const message = dialog.querySelector('#license-message');
                
                // 填入已保存的许可证
                if (this.licenseKey) {
                    input.value = this.licenseKey;
                }
                
                // 自动聚焦
                setTimeout(() => input.focus(), 100);
                
                // 验证许可证
                const validateLicense = async () => {
                    const licenseKey = input.value.trim();
                    if (!licenseKey) {
                        this.showMessage(message, '请输入许可证密钥', 'error');
                        return;
                    }
                    
                    validateBtn.textContent = '验证中...';
                    validateBtn.disabled = true;
                    
                    try {
                        const response = await fetch('/api/license/validate', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ license_key: licenseKey })
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            this.licenseKey = licenseKey;
                            localStorage.setItem('comfyui_license_key', licenseKey);
                            this.showMessage(message, '许可证验证成功！', 'success');
                            
                            setTimeout(() => {
                                this.closeLicenseDialog(dialog);
                                resolve(true);
                            }, 1000);
                        } else {
                            this.showMessage(message, result.error || '许可证验证失败', 'error');
                        }
                    } catch (error) {
                        this.showMessage(message, '网络错误，请稍后重试', 'error');
                    } finally {
                        validateBtn.textContent = '验证许可证';
                        validateBtn.disabled = false;
                    }
                };
                
                // 取消操作
                const cancelOperation = () => {
                    this.closeLicenseDialog(dialog);
                    resolve(false);
                };
                
                // 联系购买
                const contactForLicense = () => {
                    window.open('/license', '_blank');
                };
                
                // 绑定事件
                validateBtn.addEventListener('click', validateLicense);
                cancelBtn.addEventListener('click', cancelOperation);
                contactBtn.addEventListener('click', contactForLicense);
                
                // 回车键验证
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        validateLicense();
                    }
                });
                
                // ESC键取消
                document.addEventListener('keydown', function escHandler(e) {
                    if (e.key === 'Escape') {
                        document.removeEventListener('keydown', escHandler);
                        cancelOperation();
                    }
                });
            });
        }
        
        showMessage(element, text, type) {
            element.textContent = text;
            element.className = `license-message ${type}`;
        }
        
        closeLicenseDialog(dialog) {
            if (dialog && dialog.parentNode) {
                dialog.remove();
            }
        }
        
        clearLicense() {
            this.licenseKey = null;
            localStorage.removeItem('comfyui_license_key');
        }
        
        addLicenseButton() {
            // 延迟添加按钮，等待界面加载完成
            setTimeout(() => {
                const existingBtn = document.getElementById('license-manager-btn');
                if (existingBtn) return;
                
                const button = document.createElement('button');
                button.id = 'license-manager-btn';
                button.innerHTML = '🔐 许可证管理';
                button.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    z-index: 1000;
                    padding: 8px 15px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                    transition: all 0.3s ease;
                `;
                
                button.addEventListener('mouseover', () => {
                    button.style.transform = 'translateY(-2px)';
                    button.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.3)';
                });
                
                button.addEventListener('mouseout', () => {
                    button.style.transform = 'translateY(0)';
                    button.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
                });
                
                button.addEventListener('click', () => {
                    window.open('/license', '_blank');
                });
                
                document.body.appendChild(button);
            }, 2000);
        }
        
        listenStorageChanges() {
            window.addEventListener('storage', (e) => {
                if (e.key === 'comfyui_license_key') {
                    this.licenseKey = e.newValue;
                }
            });
        }
        
        processPendingRequests() {
            const requests = [...this.pendingRequests];
            this.pendingRequests = [];
            
            requests.forEach(({ originalFetch, url, options, resolve, reject }) => {
                this.handlePromptRequest(originalFetch, url, options)
                    .then(resolve)
                    .catch(reject);
            });
        }
    }
    
    // 初始化许可证管理器
    if (typeof window !== 'undefined') {
        window.addEventListener('DOMContentLoaded', () => {
            window.comfyLicenseManager = new LicenseManager();
            console.log('🔐 ComfyUI License Manager 已加载');
        });
        
        // 如果DOM已经加载完成
        if (document.readyState === 'loading') {
            // DOM还在加载
        } else {
            // DOM已经加载完成
            setTimeout(() => {
                if (!window.comfyLicenseManager) {
                    window.comfyLicenseManager = new LicenseManager();
                    console.log('🔐 ComfyUI License Manager 已加载');
                }
            }, 1000);
        }
    }
    
})(); 