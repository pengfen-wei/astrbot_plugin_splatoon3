"""通过name匹配武器翻译"""
import asyncio
import aiohttp
import json

async def test_weapon_name_match():
    # 获取中文locale
    locale_url = "https://splatoon3.ink/data/locale/zh-CN.json"
    # 获取schedules数据
    schedules_url = "https://splatoon3.ink/data/schedules.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        # 获取locale数据
        async with session.get(locale_url, headers=headers) as response:
            if response.status == 200:
                locale_data = await response.json()
                weapons_locale = locale_data.get("weapons", {})
                
                # 创建name到翻译的映射
                name_to_translation = {}
                for weapon_id, weapon_info in weapons_locale.items():
                    name = weapon_info.get("name", "")
                    if name:
                        name_to_translation[name] = name
                
                print(f"=== 创建了 {len(name_to_translation)} 个武器名称映射 ===")
                
                # 获取schedules数据
                async with session.get(schedules_url, headers=headers) as response2:
                    if response2.status == 200:
                        schedules_data = await response2.json()
                        schedules = schedules_data.get("data", {}).get("coopGroupingSchedule", {}).get("regularSchedules", {}).get("nodes", [])
                        
                        if schedules:
                            schedule = schedules[0]
                            setting = schedule.get("setting", {})
                            weapons = setting.get("weapons", [])
                            
                            print("\n=== 武器翻译测试 ===")
                            for i, weapon in enumerate(weapons):
                                english_name = weapon.get("name", "")
                                chinese_name = name_to_translation.get(english_name, english_name)
                                
                                print(f"\n武器 {i+1}:")
                                print(f"  英文名: {english_name}")
                                print(f"  中文名: {chinese_name}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_weapon_name_match())
