"""检查武器ID和locale数据"""
import asyncio
import aiohttp
import json

async def test_weapon_translation():
    # 获取中文locale
    locale_url = "https://splatoon3.ink/data/locale/zh-CN.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        # 获取locale数据
        async with session.get(locale_url, headers=headers) as response:
            if response.status == 200:
                locale_data = await response.json()
                
                # 查看武器数据结构
                weapons = locale_data.get("weapons", {})
                print("=== 武器翻译数据结构 ===")
                print(f"武器数量: {len(weapons)}")
                
                # 显示前几个武器
                count = 0
                for weapon_id, weapon_info in weapons.items():
                    if count < 5:
                        print(f"\nID: {weapon_id}")
                        print(f"Name: {weapon_info.get('name', '')}")
                        count += 1
                    else:
                        break
                        
                # 检查是否有 __splatoon3ink_id 相关的数据
                print("\n=== 检查 __splatoon3ink_id ===")
                for weapon_id, weapon_info in weapons.items():
                    if "c100f88e8b925e1c" in str(weapon_info):
                        print(f"找到匹配: {weapon_id}")
                        print(json.dumps(weapon_info, ensure_ascii=False, indent=2))
                        break
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_weapon_translation())
