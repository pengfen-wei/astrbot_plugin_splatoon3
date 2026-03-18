"""测试API连接和数据获取"""
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from splatoon3_client import Splatoon3Client

async def test_api_connection():
    print("=== 测试API连接 ===")
    
    # 创建客户端（启用debug模式）
    client = Splatoon3Client(language="zh-CN", debug=True)
    
    try:
        # 测试获取当前地图
        print("\n1. 测试获取当前地图...")
        current_stages = await client.get_current_stages()
        assert current_stages is not None, "当前地图数据获取失败"
        print(f"当前地图数据: {current_stages}")
        for key, value in current_stages.items():
            if value:
                print(f"  {key}: {value.get('stages', [])}")
            else:
                print(f"  {key}: 无数据")
        
        # 测试获取鲑鱼跑
        print("\n2. 测试获取鲑鱼跑...")
        salmon_run = await client.get_salmon_run()
        assert isinstance(salmon_run, list), "鲑鱼跑数据获取失败"
        print(f"鲑鱼跑数据: {salmon_run}")
        
        # 测试获取挑战活动
        print("\n3. 测试获取挑战活动...")
        challenges = await client.get_challenges()
        assert isinstance(challenges, list), "挑战活动数据获取失败"
        print(f"挑战活动数量: {len(challenges)}")
        for challenge in challenges:
            print(f"  {challenge['name']}")
        
        # 测试获取祭典
        print("\n4. 测试获取祭典...")
        upcoming_fests = await client.get_upcoming_splatfests()
        assert isinstance(upcoming_fests, list), "祭典数据获取失败"
        print(f"即将开始的祭典数量: {len(upcoming_fests)}")
        for fest in upcoming_fests:
            print(f"  {fest['title']} ({fest['region']})")
        
        # 测试获取装备
        print("\n5. 测试获取装备...")
        gears = await client.get_splatnet_gear()
        assert isinstance(gears, list), "装备数据获取失败"
        print(f"装备数量: {len(gears)}")
        for gear in gears[:3]:  # 只显示前3个
            print(f"  {gear['name']}")
        
        print("\n=== 测试完成 ===")
        print("API连接正常，可以获取数据")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    finally:
        # 确保关闭客户端，释放资源
        await client.close()
        print("\n客户端已关闭")

if __name__ == "__main__":
    # 设置超时，避免测试无限挂起
    asyncio.run(asyncio.wait_for(test_api_connection(), timeout=60))
