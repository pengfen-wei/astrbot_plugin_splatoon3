"""测试插件集成环境"""
import sys
import os
from splatoon3_client import Splatoon3Client

# 模拟插件配置
test_config = {
    "debug": True
}

class MockContext:
    """模拟Context对象"""
    pass

class MockEvent:
    """模拟AstrMessageEvent对象"""
    def __init__(self, sender_id="test_user"):
        self.sender_id = sender_id
        self.platform = "test"
    
    def plain_result(self, text):
        """模拟plain_result方法"""
        return text

async def test_plugin_integration():
    print("=== 测试插件集成环境 ===")
    
    # 测试API客户端
    print("\n1. 测试API客户端初始化...")
    client = Splatoon3Client(language="zh-CN", debug=True)
    
    # 测试API调用
    print("\n2. 测试API调用...")
    try:
        # 测试获取当前地图
        current_stages = await client.get_current_stages()
        print(f"当前地图: {current_stages}")
        
        # 测试获取鲑鱼跑
        salmon_run = await client.get_salmon_run()
        print(f"鲑鱼跑: {salmon_run}")
        
        # 测试获取挑战活动
        challenges = await client.get_challenges()
        print(f"挑战活动: {challenges}")
        
        # 测试获取祭典
        upcoming_fests = await client.get_upcoming_splatfests()
        print(f"即将开始的祭典: {upcoming_fests}")
        
        # 测试获取装备
        gears = await client.get_splatnet_gear()
        print(f"装备: {gears}")
        
        print("\n=== 测试完成 ===")
        print("API调用正常，可以获取数据")
        
    except Exception as e:
        print(f"\n❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_plugin_integration())
