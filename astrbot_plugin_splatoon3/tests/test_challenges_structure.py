"""检查挑战活动数据结构"""
import asyncio
import aiohttp
import json

async def test_challenges_structure():
    url = "https://splatoon3.ink/data/schedules.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                event_schedules = data.get("data", {}).get("eventSchedules", {}).get("nodes", [])
                
                print("=== 挑战活动数据结构 ===")
                print(f"活动数量: {len(event_schedules)}")
                
                if event_schedules:
                    for i, challenge in enumerate(event_schedules):
                        print(f"\n挑战 {i+1}:")
                        print(json.dumps(challenge, ensure_ascii=False, indent=2))
                else:
                    print("暂无挑战活动")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_challenges_structure())
