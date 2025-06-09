"""
ComfyUI 许可证管理器插件
一个即插即用的ComfyUI许可证验证系统

作者: 翼创未来软件科技有限公司
联系方式: YCWL0426
版本: 1.0.0
描述: 为ComfyUI提供完整的许可证验证和管理功能,未经许可禁止修改代码
"""

try:
    from .license_manager import LicenseValidator
    from .web import setup_license_routes
except ImportError:
    # 如果相对导入失败，使用绝对导入
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    sys.path.append(current_dir)
    from license_manager import LicenseValidator
    from web import setup_license_routes

# 导入插件信息
WEB_DIRECTORY = "js"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# 设置Web路由和主页拦截
try:
    from server import PromptServer
    import os
    from aiohttp import web
    
    # 添加许可证路由
    setup_license_routes(PromptServer.instance.app)
    
    # 创建新的主页处理器，注入许可证验证脚本
    async def get_root_with_license_injection(request):
        """返回注入了卡密验证脚本的主页"""
        # 获取原始web根目录
        web_root = PromptServer.instance.web_root
        index_path = os.path.join(web_root, "index.html")
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 注入我们的脚本
            script_tag = '<script src="/license_injection.js"></script>'
            
            if '</head>' in content:
                content = content.replace('</head>', f'{script_tag}\n</head>')
            else:
                content = content.replace('</body>', f'{script_tag}\n</body>')
            
            response = web.Response(text=content, content_type='text/html')
            response.headers['Cache-Control'] = 'no-cache'
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        else:
            return web.Response(status=404)
    
    # 添加我们的主页路由（会覆盖默认的）
    PromptServer.instance.app.router.add_get('/', get_root_with_license_injection)

    # 拦截关键API端点，确保需要许可证验证
    original_prompt_handler = None
    original_queue_handler = None

    # 查找并替换现有的prompt处理器
    for route in PromptServer.instance.app.router._resources:
        if hasattr(route, '_path') and route._path == '/prompt':
            for method_handler in route._routes:
                if method_handler.method == 'POST':
                    original_prompt_handler = method_handler._handler
                    break

    async def license_protected_prompt(request):
        """需要许可证验证的prompt处理器"""
        try:
            # 检查请求中是否包含license_key
            if request.content_type == 'application/json':
                data = await request.json()
                license_key = data.get('license_key')

                if not license_key:
                    return web.json_response({
                        'error': '需要有效的许可证密钥',
                        'code': 'LICENSE_REQUIRED'
                    }, status=401)

                # 验证许可证
                from .license_manager import license_validator
                is_valid, result = license_validator.validate_license(license_key)

                if not is_valid:
                    return web.json_response({
                        'error': f'许可证验证失败: {result}',
                        'code': 'LICENSE_INVALID'
                    }, status=401)

                # 移除license_key，避免传递给原始处理器
                if 'license_key' in data:
                    del data['license_key']

                # 重新构造请求
                import json
                new_body = json.dumps(data).encode()
                request._payload = new_body
                request._body = new_body

            # 调用原始处理器
            if original_prompt_handler:
                return await original_prompt_handler(request)
            else:
                return web.json_response({'error': '原始处理器未找到'}, status=500)

        except Exception as e:
            return web.json_response({
                'error': f'处理请求时出错: {str(e)}',
                'code': 'PROCESSING_ERROR'
            }, status=500)

    # 替换prompt处理器
    if original_prompt_handler:
        PromptServer.instance.app.router.add_post('/prompt', license_protected_prompt)
        print("[ComfyUI-License-Manager] 已拦截 /prompt 端点")

    # 同样拦截其他重要端点
    async def license_protected_queue(request):
        """需要许可证验证的队列处理器"""
        # 这里可以添加队列相关的许可证检查
        # 暂时允许通过，因为队列操作通常不需要额外验证
        return web.json_response({'status': 'queue operations require license'}, status=401)

    # 添加队列拦截（如果需要）
    # PromptServer.instance.app.router.add_post('/queue', license_protected_queue)
    
    print("[ComfyUI-License-Manager] 许可证系统已启动")
    print("[ComfyUI-License-Manager] 主页已注入卡密验证脚本")
    print("[ComfyUI-License-Manager] 访问 /license_dialog.html 进行卡密管理")
    
except ImportError as e:
    print(f"[ComfyUI-License-Manager] 警告: 无法导入PromptServer - {e}")
except Exception as e:
    print(f"[ComfyUI-License-Manager] 设置错误: {e}")

print("[ComfyUI-License-Manager] 插件加载完成")

print("🔐 ComfyUI License Manager v1.0.0 已加载")
print("💡 访问 /license 查看许可证管理界面") 