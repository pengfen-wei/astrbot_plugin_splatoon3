"""检查festivals.json的data字段"""
import asyncio
import aiohttp
import json

async def test_festivals_data():
    url = "https://splatoon3.ink/data/festivals.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                print("=== festivals.json data 字段 ===")
                data_field = data.get("data", {})
                print(f"类型: {type(data_field)}")
                print(f"键: {list(data_field.keys()) if isinstance(data_field, dict) else 'N/A'}")
                print(f"长度: {len(data_field) if hasattr(data_field, '__len__') else 'N/A'}")
                
                if isinstance(data_field, dict):
                    for key, value in data_field.items():
                        print(f"\n{key}:")
                        if isinstance(value, dict):
                            print(f"  类型: dict")
                            print(f"  键: {list(value.keys())}")
                            if "nodes" in value:
                                nodes = value["nodes"]
                                print(f"  nodes 数量: {len(nodes)}")
                        else:
                            print(f"  类型: {type(value)}")
                            print(f"  值: {str(value)[:100]}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_festivals_data())
