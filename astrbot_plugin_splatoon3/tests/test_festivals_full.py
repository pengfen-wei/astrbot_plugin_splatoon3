"""检查festivals.json完整数据结构"""
import asyncio
import aiohttp
import json

async def test_festivals_full():
    url = "https://splatoon3.ink/data/festivals.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                print("=== festivals.json 完整数据结构 ===")
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_festivals_full())
