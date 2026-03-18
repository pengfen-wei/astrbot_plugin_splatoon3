"""测试调试模式和日志输出"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from splatoon3_client import Splatoon3Client

async def test_debug_mode():
    print("=== 测试调试模式 ===")
    
    # 测试1: debug=False
    print("\n1. 测试 debug=False...")
    client_no_debug = Splatoon3Client(language="zh-CN", debug=False)
    print(f"客户端debug设置: {client_no_debug.debug}")
    
    # 测试2: debug=True
    print("\n2. 测试 debug=True...")
    client_with_debug = Splatoon3Client(language="zh-CN", debug=True)
    print(f"客户端debug设置: {client_with_debug.debug}")
    
    # 测试3: 测试日志输出
    print("\n3. 测试日志输出...")
    try:
        await client_with_debug.get_current_stages()
        print("✅ API调用成功，应该有日志输出")
    except Exception as e:
        print(f"❌ API调用失败: {e}")
    
    print("\n=== 测试完成 ===")
    
    # 关闭客户端，释放资源
    await client_no_debug.close()
    await client_with_debug.close()
    print("客户端已关闭")

if __name__ == "__main__":
    asyncio.run(test_debug_mode())
