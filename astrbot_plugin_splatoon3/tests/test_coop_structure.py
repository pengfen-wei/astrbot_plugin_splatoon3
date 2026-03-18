"""测试 coop.json 数据结构"""
import asyncio
import aiohttp
import json

async def test_coop_structure():
    url = "https://splatoon3.ink/data/coop.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("=== coop.json 数据结构 ===")
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_coop_structure())
