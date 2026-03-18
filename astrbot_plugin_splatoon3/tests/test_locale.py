"""测试本地化数据"""
import asyncio
import aiohttp
import json

async def fetch_locale():
    """获取本地化数据"""
    # 尝试获取本地化文件
    urls = [
        "https://splatoon3.ink/data/locale/zh-CN.json",
        "https://splatoon3.ink/data/locale/zh_CN.json",
        "https://splatoon3.ink/data/locale/ja-JP.json",
        "https://splatoon3.ink/data/locale/en-US.json",
    ]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url) as response:
                    print(f"\n=== {url} ===")
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print("Keys:", list(data.keys())[:10])
                        if "stages" in data:
                            print("Stages sample:", dict(list(data["stages"].items())[:3]))
                        if "rules" in data:
                            print("Rules sample:", dict(list(data["rules"].items())[:3]))
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_locale())
