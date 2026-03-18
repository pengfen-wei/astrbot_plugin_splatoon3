"""测试挑战活动翻译"""
import asyncio
from splatoon3_client import Splatoon3Client

async def test_challenge_translation():
    client = Splatoon3Client(language="zh-CN", debug=True)
    
    try:
        challenges = await client.get_challenges()
        
        print("=== 挑战活动翻译测试 ===")
        for i, challenge in enumerate(challenges):
            print(f"\n挑战 {i+1}:")
            print(f"  名称: {challenge['name']}")
            print(f"  描述: {challenge['description']}")
            print(f"  时间: {challenge['start_time']} ~ {challenge['end_time']}")
            print(f"  规则: {challenge['regulation']}")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        await client.close()
        print("\n客户端已关闭")

if __name__ == "__main__":
    asyncio.run(test_challenge_translation())
