"""检查地图和Boss的ID字段"""
import asyncio
import aiohttp
import json

async def test_stage_boss_ids():
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
                stages_locale = locale_data.get("stages", {})
                bosses_locale = locale_data.get("bosses", {})
                
                # 获取schedules数据
                async with session.get(schedules_url, headers=headers) as response2:
                    if response2.status == 200:
                        schedules_data = await response2.json()
                        schedules = schedules_data.get("data", {}).get("coopGroupingSchedule", {}).get("regularSchedules", {}).get("nodes", [])
                        
                        if schedules:
                            schedule = schedules[0]
                            setting = schedule.get("setting", {})
                            stage = setting.get("coopStage", {})
                            boss = setting.get("boss", {})
                            
                            print("=== 检查地图ID ===")
                            stage_id = stage.get("id", "")
                            stage_splat3ink_id = stage.get("__splatoon3ink_id", "")
                            print(f"  id: {stage_id}")
                            print(f"  __splatoon3ink_id: {stage_splat3ink_id}")
                            
                            if stage_id in stages_locale:
                                print(f"  通过id找到: {stages_locale[stage_id].get('name', '')}")
                            if stage_splat3ink_id in stages_locale:
                                print(f"  通过__splatoon3ink_id找到: {stages_locale[stage_splat3ink_id].get('name', '')}")
                            
                            print("\n=== 检查Boss ID ===")
                            boss_id = boss.get("id", "")
                            boss_splat3ink_id = boss.get("__splatoon3ink_id", "")
                            print(f"  id: {boss_id}")
                            print(f"  __splatoon3ink_id: {boss_splat3ink_id}")
                            
                            if boss_id in bosses_locale:
                                print(f"  通过id找到: {bosses_locale[boss_id].get('name', '')}")
                            if boss_splat3ink_id in bosses_locale:
                                print(f"  通过__splatoon3ink_id找到: {bosses_locale[boss_splat3ink_id].get('name', '')}")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_stage_boss_ids())
