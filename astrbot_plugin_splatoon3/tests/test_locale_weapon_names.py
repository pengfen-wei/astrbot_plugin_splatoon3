"""检查locale中武器的name字段内容"""
import asyncio
import aiohttp
import json

async def test_locale_weapon_names():
    locale_url = "https://splatoon3.ink/data/locale/zh-CN.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(locale_url, headers=headers) as response:
            if response.status == 200:
                locale_data = await response.json()
                weapons = locale_data.get("weapons", {})
                
                print("=== locale中的武器name字段 ===")
                print(f"武器总数: {len(weapons)}")
                
                # 显示所有武器的name
                for key, weapon in weapons.items():
                    name = weapon.get("name", "")
                    print(f"{name}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_locale_weapon_names())
