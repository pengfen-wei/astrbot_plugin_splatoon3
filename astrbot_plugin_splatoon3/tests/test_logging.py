"""测试日志输出机制"""
import asyncio
import sys
import os
import json

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

async def test_logging():
    print("=== 测试日志输出机制 ===")
    
    # 测试1: 测试logger导入
    print("\n1. 测试logger导入...")
    try:
        from astrbot.api.all import logger
        print("✅ 成功导入 astrbot.api.all.logger")
        logger.info("[测试] 这是一条测试日志")
    except ImportError as e:
        print(f"❌ 导入 astrbot.api.all.logger 失败: {e}")
        
        # 测试2: 尝试使用标准logging
        print("\n2. 测试标准logging...")
        try:
            from logging import getLogger
            logger = getLogger("Splatoon3")
            print("✅ 成功创建标准logger")
            logger.info("[测试] 这是一条测试日志")
        except Exception as e2:
            print(f"❌ 创建标准logger失败: {e2}")
    
    # 测试3: 测试API客户端的日志输出
    print("\n3. 测试API客户端日志输出...")
    from splatoon3_client import Splatoon3Client
    
    # 创建测试数据
    test_data = {"test": "data", "value": 123}
    
    # 创建客户端并测试日志
    client = Splatoon3Client(language="zh-CN", debug=True)
    print(f"客户端debug设置: {client.debug}")
    
    # 手动调用日志方法
    print("\n4. 手动调用日志方法...")
    client._log_api_data("test_endpoint", test_data)
    
    # 测试5: 实际API调用
    print("\n5. 实际API调用...")
    try:
        await client.get_current_stages()
        print("✅ API调用成功")
    except Exception as e:
        print(f"❌ API调用失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_logging())
