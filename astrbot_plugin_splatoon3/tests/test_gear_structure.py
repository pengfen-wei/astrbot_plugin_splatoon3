"""检查gear.json中的装备数据结构"""
import asyncio
import aiohttp
import json

async def test_gear_structure():
    url = "https://splatoon3.ink/data/gear.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                gears = data.get("data", {}).get("gesotown", {}).get("limitedGears", [])
                
                if gears:
                    print("=== 装备数据结构 ===")
                    gear = gears[0]
                    print(json.dumps(gear, ensure_ascii=False, indent=2))
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_gear_structure())
