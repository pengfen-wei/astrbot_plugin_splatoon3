"""检查locale中武器的键结构"""
import asyncio
import aiohttp
import json

async def test_weapon_keys():
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
                
                print("=== 武器键结构 ===")
                # 显示前10个武器的键
                keys = list(weapons.keys())[:10]
                for key in keys:
                    weapon = weapons[key]
                    print(f"\nKey: {key}")
                    print(f"Name: {weapon.get('name', '')}")
                    
                    # 检查是否有 __splatoon3ink_id
                    if "__splatoon3ink_id" in weapon:
                        print(f"__splatoon3ink_id: {weapon['__splatoon3ink_id']}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_weapon_keys())
