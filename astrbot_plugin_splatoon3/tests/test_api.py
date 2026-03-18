"""测试API数据结构"""
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from splatoon3_client import Splatoon3Client

async def test_api_structures():
    """测试API数据结构"""
    print("=== 测试API数据结构 ===")
    
    # 创建客户端
    client = Splatoon3Client(language="zh-CN", debug=True)
    
    try:
        # 测试获取所有地图轮换
        print("\n1. 测试获取所有地图轮换...")
        stages = await client.get_stages()
        assert stages is not None, "获取地图轮换失败"
        assert isinstance(stages, dict), "地图轮换数据类型错误"
        assert all(key in stages for key in ["regular", "bankara", "x", "fest"]), "地图轮换数据结构错误"
        print(f"地图轮换数据获取成功: {list(stages.keys())}")
        
        # 测试获取鲑鱼跑数据结构
        print("\n2. 测试获取鲑鱼跑数据结构...")
        salmon_run = await client.get_salmon_run()
        assert isinstance(salmon_run, list), "鲑鱼跑数据类型错误"
        if salmon_run:
            first_coop = salmon_run[0]
            assert all(key in first_coop for key in ["start_time", "end_time", "stage", "weapons"]), "鲑鱼跑数据结构错误"
            print("鲑鱼跑数据结构正确")
        
        # 测试获取挑战活动数据结构
        print("\n3. 测试获取挑战活动数据结构...")
        challenges = await client.get_challenges()
        assert isinstance(challenges, list), "挑战活动数据类型错误"
        if challenges:
            first_challenge = challenges[0]
            assert all(key in first_challenge for key in ["name", "description", "start_time", "end_time"]), "挑战活动数据结构错误"
            print("挑战活动数据结构正确")
        
        # 测试获取装备数据结构
        print("\n4. 测试获取装备数据结构...")
        gears = await client.get_splatnet_gear()
        assert isinstance(gears, list), "装备数据类型错误"
        if gears:
            first_gear = gears[0]
            assert all(key in first_gear for key in ["name", "brand", "price", "rarity"]), "装备数据结构错误"
            print("装备数据结构正确")
        
        # 测试获取祭典数据结构
        print("\n5. 测试获取祭典数据结构...")
        upcoming_fests = await client.get_upcoming_splatfests()
        assert isinstance(upcoming_fests, list), "祭典数据类型错误"
        if upcoming_fests:
            first_fest = upcoming_fests[0]
            assert all(key in first_fest for key in ["title", "region", "start_time", "end_time", "teams"]), "祭典数据结构错误"
            print("祭典数据结构正确")
        
        print("\n=== 测试完成 ===")
        print("API数据结构测试通过")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    finally:
        # 确保关闭客户端，释放资源
        await client.close()
        print("\n客户端已关闭")

if __name__ == "__main__":
    # 设置超时，避免测试无限挂起
    asyncio.run(asyncio.wait_for(test_api_structures(), timeout=60))
