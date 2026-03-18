"""测试 schedules.json 中的鲑鱼跑数据结构"""
import asyncio
import aiohttp
import json

async def test_salmon_structure():
    url = "https://splatoon3.ink/data/schedules.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("=== schedules.json 中的鲑鱼跑数据 ===")
                
                # 查找鲑鱼跑相关数据
                coop_schedules = data.get("data", {}).get("coopGroupingSchedule", {})
                print(json.dumps(coop_schedules, ensure_ascii=False, indent=2))
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_salmon_structure())
