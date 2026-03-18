"""检查festivals.json完整数据（包括顶层字段）"""
import asyncio
import aiohttp
import json

async def test_festivals_top_level():
    url = "https://splatoon3.ink/data/festivals.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                print("=== festivals.json 顶层字段 ===")
                print(f"顶层键: {list(data.keys())}")
                
                # 检查每个顶层字段
                for key in data.keys():
                    value = data[key]
                    print(f"\n{key}:")
                    print(f"  类型: {type(value)}")
                    
                    if isinstance(value, dict):
                        print(f"  键: {list(value.keys())}")
                        if "nodes" in value:
                            nodes = value["nodes"]
                            print(f"  nodes 数量: {len(nodes)}")
                            if nodes:
                                print(f"  第一个节点的 state: {nodes[0].get('state')}")
                    elif isinstance(value, list):
                        print(f"  长度: {len(value)}")
                        if value:
                            print(f"  第一个元素类型: {type(value[0])}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_festivals_top_level())
