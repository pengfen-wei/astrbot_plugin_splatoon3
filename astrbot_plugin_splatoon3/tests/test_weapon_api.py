"""检查API返回的武器数据结构"""
import asyncio
import aiohttp
import json

async def test_weapon_api():
    url = "https://splatoon3.ink/data/schedules.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                # 获取鲑鱼跑数据
                schedules = data.get("data", {}).get("coopGroupingSchedule", {}).get("regularSchedules", {}).get("nodes", [])
                
                if schedules:
                    schedule = schedules[0]
                    setting = schedule.get("setting", {})
                    weapons = setting.get("weapons", [])
                    
                    print("=== API返回的武器数据 ===")
                    for i, weapon in enumerate(weapons):
                        print(f"\n武器 {i+1}:")
                        print(json.dumps(weapon, ensure_ascii=False, indent=2))
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_weapon_api())
