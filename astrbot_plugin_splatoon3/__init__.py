"""Splatoon3 查询插件

基于 splatoon3.ink API 的 AstrBot 插件
"""

from .main import Splatoon3Plugin

__all__ = ["Splatoon3Plugin"]

# 延迟导入 Splatoon3Client，避免在包导入时触发 aiohttp 依赖
# 只在需要时通过 main.py 中的方法获取客户端实例
