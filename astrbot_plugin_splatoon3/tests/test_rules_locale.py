"""检查规则翻译数据"""
import asyncio
import aiohttp
import json

async def test_rules_locale():
    locale_url = "https://splatoon3.ink/data/locale/zh-CN.json"
    headers = {
        "User-Agent": "AstrBot-Splatoon3-Plugin/1.0",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(locale_url, headers=headers) as response:
            if response.status == 200:
                locale_data = await response.json()
                
                print("=== 检查规则翻译数据 ===")
                
                # 检查是否有rules字段
                rules = locale_data.get("rules", {})
                print(f"rules 数量: {len(rules)}")
                
                if rules:
                    for rule_id, rule_info in rules.items():
                        print(f"\nID: {rule_id}")
                        print(f"Name: {rule_info.get('name', '')}")
                else:
                    print("没有找到rules翻译数据")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_rules_locale())
