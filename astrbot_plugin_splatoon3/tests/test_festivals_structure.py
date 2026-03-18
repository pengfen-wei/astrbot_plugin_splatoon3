"""检查祭典数据结构"""
import asyncio
import aiohttp
import json

async def test_festivals_structure():
    url = "https://splatoon3.ink/data/festivals.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                print("=== 祭典数据结构 ===")
                print(f"顶层键: {list(data.get('data', {}).keys())}")
                
                # 检查每个区域的数据
                for region in ["us", "eu", "jp", "ap"]:
                    region_data = data.get("data", {}).get(region, {})
                    nodes = region_data.get("nodes", [])
                    print(f"\n{region.upper()} 区域:")
                    print(f"  祭典数量: {len(nodes)}")
                    
                    if nodes:
                        for i, fest in enumerate(nodes):
                            print(f"\n  祭典 {i+1}:")
                            print(f"    state: {fest.get('state')}")
                            print(f"    title: {fest.get('title')}")
                            print(f"    startTime: {fest.get('startTime')}")
                            print(f"    endTime: {fest.get('endTime')}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_festivals_structure())
