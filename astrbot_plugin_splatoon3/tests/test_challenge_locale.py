"""检查挑战活动的翻译数据"""
import asyncio
import aiohttp
from test_config import LOCALE_URLS

async def test_challenge_locale():
    locale_url = LOCALE_URLS["zh-CN"]
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(locale_url, headers=headers) as response:
            if response.status == 200:
                locale_data = await response.json()
                
                print("=== 检查挑战活动翻译数据 ===")
                
                # 检查是否有events字段
                events = locale_data.get("events", {})
                print(f"events 数量: {len(events)}")
                
                if events:
                    # 显示前几个事件
                    count = 0
                    for event_id, event_info in events.items():
                        if count < 5:
                            print(f"\nID: {event_id}")
                            print(f"Name: {event_info.get('name', '')}")
                            print(f"Desc: {event_info.get('desc', '')}")
                            count += 1
                        else:
                            break
                else:
                    print("没有找到events翻译数据")
                    
                # 检查是否有其他可能的字段
                print("\n=== 检查其他可能的翻译字段 ===")
                for key, value in locale_data.items():
                    if isinstance(value, dict) and len(value) > 0:
                        print(f"{key}: {len(value)} 个条目")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_challenge_locale())
