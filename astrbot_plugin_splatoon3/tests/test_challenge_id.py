"""检查挑战活动ID匹配"""
import asyncio
import aiohttp
from test_config import LOCALE_URLS, ENDPOINTS

async def test_challenge_id_match():
    # 获取中文locale
    locale_url = LOCALE_URLS["zh-CN"]
    # 获取schedules数据
    schedules_url = ENDPOINTS["schedules"]
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        # 获取locale数据
        async with session.get(locale_url, headers=headers) as response:
            if response.status == 200:
                locale_data = await response.json()
                events_locale = locale_data.get("events", {})
                
                # 获取schedules数据
                async with session.get(schedules_url, headers=headers) as response2:
                    if response2.status == 200:
                        schedules_data = await response2.json()
                        events = schedules_data.get("data", {}).get("eventSchedules", {}).get("nodes", [])
                        
                        print("=== 检查挑战活动ID匹配 ===")
                        assert len(events) > 0, "未找到挑战活动数据"
                        
                        for i, event in enumerate(events):
                            league_match_setting = event.get("leagueMatchSetting", {})
                            league_event = league_match_setting.get("leagueMatchEvent", {})
                            event_id = league_event.get("id", "")
                            event_name = league_event.get("name", "")
                            
                            print(f"\n挑战 {i+1}:")
                            print(f"  API ID: {event_id}")
                            print(f"  API Name: {event_name}")
                            
                            # 检查locale中是否有这个ID
                            if event_id in events_locale:
                                locale_name = events_locale[event_id].get("name", "")
                                locale_desc = events_locale[event_id].get("desc", "")
                                print(f"  中文名称: {locale_name}")
                                print(f"  中文描述: {locale_desc}")
                                # 添加断言确保翻译存在
                                assert locale_name, f"挑战活动 {event_id} 缺少中文名称"
                            else:
                                print(f"  ❌ 在locale中未找到")
                                assert False, f"挑战活动 ID {event_id} 在 locale 中未找到"
            else:
                print(f"请求失败: {response.status}")
                raise Exception(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_challenge_id_match())
