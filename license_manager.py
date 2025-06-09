"""
ComfyUI License Manager 核心模块 - 服务器端验证器
仅负责验证许可证，不具备生成功能

安全说明：
1. 此模块运行在 ComfyUI 服务器上
2. 只包含验证许可证的功能
3. 不包含主密码或生成功能
4. encryption_key 由独立生成器提供
"""

import os
import json
import time
from datetime import datetime
from cryptography.fernet import Fernet

class LicenseValidator:
    """
    许可证验证器 - 仅验证功能
    不包含任何许可证生成能力，确保服务器端安全
    """
    def __init__(self, config_path="license_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # 验证配置完整性
        if not self.config.get("encryption_key"):
            raise ValueError("缺少加密密钥！请使用独立生成器生成配置文件。")
        
    def load_config(self):
        """加载许可证配置"""
        default_config = {
            "title": "ComfyUI 许可证验证",
            "description": "请输入有效的许可证密钥来使用此服务",
            "contact_info": {
                "qq": "123456789",
                "wechat": "your_wechat",
                "email": "contact@example.com",
                "website": "https://example.com"
            },
            "features": [
                "🎨 AI图像生成",
                "🎥 视频处理",
                "🔧 自定义工作流",
                "💫 高级功能"
            ],
            "encryption_key": None,  # 必须由独立生成器提供
            "salt": "comfyui_license_salt",
            "generator_info": "此配置应由独立生成器创建"
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                default_config.update(config)
            except Exception as e:
                print(f"[License Validator] 配置文件加载失败: {e}")
                raise ValueError("配置文件损坏或格式错误")
        else:
            print(f"[License Validator] 警告: 配置文件不存在，请使用独立生成器生成配置")
            raise FileNotFoundError("许可证配置文件不存在")
        
        return default_config
    
    def get_config_info(self):
        """获取配置信息（用于前端显示）"""
        return {
            "title": self.config.get("title", "ComfyUI 许可证验证"),
            "description": self.config.get("description", "请输入有效的许可证密钥"),
            "contact_info": self.config.get("contact_info", {}),
            "features": self.config.get("features", [])
        }
    
    def validate_license(self, license_key):
        """验证许可证"""
        if not license_key:
            return False, "许可证密钥不能为空"
        
        try:
            # 解密许可证
            fernet = Fernet(self.config["encryption_key"].encode())
            decrypted_data = fernet.decrypt(license_key.encode())
            license_data = json.loads(decrypted_data.decode())
            
            # 验证许可证结构
            required_fields = ['user_id', 'expire_time', 'max_uses', 'features']
            for field in required_fields:
                if field not in license_data:
                    return False, f"许可证格式错误：缺少{field}字段"
            
            # 检查过期时间
            if license_data['expire_time'] != -1:  # -1表示永不过期
                expire_time = datetime.fromtimestamp(license_data['expire_time'])
                if datetime.now() > expire_time:
                    return False, "许可证已过期"
            
            # 检查使用次数
            current_uses = license_data.get('current_uses', 0)
            if license_data['max_uses'] != -1 and current_uses >= license_data['max_uses']:
                return False, "许可证使用次数已耗尽"
            
            return True, license_data
            
        except Exception as e:
            return False, f"许可证验证失败: {str(e)}"
    
    def use_license(self, license_key):
        """使用许可证（扣除使用次数）"""
        is_valid, result = self.validate_license(license_key)
        if not is_valid:
            return False, result
        
        license_data = result
        
        # 增加使用次数
        license_data['current_uses'] = license_data.get('current_uses', 0) + 1
        
        # 重新加密许可证
        try:
            fernet = Fernet(self.config["encryption_key"].encode())
            encrypted_data = fernet.encrypt(json.dumps(license_data).encode())
            new_license_key = encrypted_data.decode()
            
            # 计算剩余使用次数
            remaining_uses = license_data['max_uses'] - license_data['current_uses']
            if license_data['max_uses'] == -1:
                remaining_uses = -1  # 无限使用
            
            return True, {
                'new_license_key': new_license_key,
                'remaining_uses': remaining_uses,
                'license_data': license_data
            }
            
        except Exception as e:
            return False, f"许可证更新失败: {str(e)}"
    
    def get_license_info(self, license_key):
        """获取许可证信息"""
        is_valid, result = self.validate_license(license_key)
        if not is_valid:
            return False, result
        
        license_data = result
        
        # 格式化信息
        info = {
            'user_id': license_data['user_id'],
            'features': license_data['features'],
            'current_uses': license_data.get('current_uses', 0),
            'max_uses': license_data['max_uses'],
            'remaining_uses': license_data['max_uses'] - license_data.get('current_uses', 0) if license_data['max_uses'] != -1 else -1,
            'expire_time': license_data['expire_time'],
            'is_expired': False
        }
        
        # 检查是否过期
        if license_data['expire_time'] != -1:
            expire_time = datetime.fromtimestamp(license_data['expire_time'])
            info['expire_time_str'] = expire_time.strftime('%Y-%m-%d %H:%M:%S')
            info['is_expired'] = datetime.now() > expire_time
        else:
            info['expire_time_str'] = '永不过期'
        
        return True, info

# 全局许可证验证器实例
license_validator = LicenseValidator() 