"""检查API返回的武器ID是否与locale中的键匹配"""
import asyncio
import aiohttp
import json

async def test_weapon_id_match():
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
                
                # 获取schedules数据
                async with session.get(schedules_url, headers=headers) as response2:
                    if response2.status == 200:
                        schedules_data = await response2.json()
                        schedules = schedules_data.get("data", {}).get("coopGroupingSchedule", {}).get("regularSchedules", {}).get("nodes", [])
                        
                        if schedules:
                            schedule = schedules[0]
                            setting = schedule.get("setting", {})
                            weapons = setting.get("weapons", [])
                            
                            print("=== 检查武器ID匹配 ===")
                            for i, weapon in enumerate(weapons):
                                splat3ink_id = weapon.get("__splatoon3ink_id", "")
                                english_name = weapon.get("name", "")
                                
                                # 检查locale中是否有这个ID
                                if splat3ink_id in weapons_locale:
                                    chinese_name = weapons_locale[splat3ink_id].get("name", "")
                                    print(f"\n武器 {i+1}:")
                                    print(f"  __splatoon3ink_id: {splat3ink_id}")
                                    print(f"  英文名: {english_name}")
                                    print(f"  中文名: {chinese_name}")
                                else:
                                    print(f"\n武器 {i+1}:")
                                    print(f"  __splatoon3ink_id: {splat3ink_id}")
                                    print(f"  英文名: {english_name}")
                                    print(f"  ❌ 在locale中未找到")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_weapon_id_match())
