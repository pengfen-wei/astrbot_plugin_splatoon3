"""检查locale中武器是否包含__splatoon3ink_id"""
import asyncio
import aiohttp
import json

async def test_weapon_splat3ink_id():
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
                
                print("=== 检查武器对象中的 __splatoon3ink_id ===")
                
                # 查找是否有武器包含 __splatoon3ink_id
                found = False
                for key, weapon in weapons.items():
                    if "__splatoon3ink_id" in weapon:
                        print(f"\n找到包含 __splatoon3ink_id 的武器:")
                        print(f"Key: {key}")
                        print(f"Name: {weapon.get('name', '')}")
                        print(f"__splatoon3ink_id: {weapon['__splatoon3ink_id']}")
                        found = True
                        break
                
                if not found:
                    print("没有找到包含 __splatoon3ink_id 的武器")
                    print("\n武器对象结构示例:")
                    first_key = list(weapons.keys())[0]
                    print(json.dumps(weapons[first_key], ensure_ascii=False, indent=2))
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_weapon_splat3ink_id())
