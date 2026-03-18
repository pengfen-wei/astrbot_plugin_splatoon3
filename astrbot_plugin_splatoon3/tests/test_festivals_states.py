"""检查祭典状态"""
import asyncio
import aiohttp
import json

async def test_festivals_states():
    url = "https://splatoon3.ink/data/festivals.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                print("=== 祭典状态统计 ===")
                
                for region in ["us", "eu", "jp", "ap"]:
                    nodes = data.get("data", {}).get(region, {}).get("nodes", [])
                    
                    states = {}
                    for fest in nodes:
                        state = fest.get("state", "UNKNOWN")
                        states[state] = states.get(state, 0) + 1
                    
                    print(f"\n{region.upper()} 区域:")
                    print(f"  总数: {len(nodes)}")
                    for state, count in states.items():
                        print(f"  {state}: {count}")
                        
                    # 显示最近的几个祭典
                    if nodes:
                        print(f"\n  最近的祭典:")
                        for i, fest in enumerate(nodes[:3]):
                            print(f"    {i+1}. {fest.get('title')} ({fest.get('state')})")
                            print(f"       {fest.get('startTime')} ~ {fest.get('endTime')}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_festivals_states())
