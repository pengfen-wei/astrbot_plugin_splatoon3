"""测试配置文件

存储测试相关的配置信息，如API URL等
"""

# API 基础 URL
API_BASE_URL = "https://splatoon3.ink/data"

# 各种API端点
ENDPOINTS = {
    "schedules": f"{API_BASE_URL}/schedules.json",
    "festivals": f"{API_BASE_URL}/festivals.json",
    "gear": f"{API_BASE_URL}/gear.json",
    "coop": f"{API_BASE_URL}/coop.json",
}

# 语言文件URL
LOCALE_URLS = {
    "zh-CN": f"{API_BASE_URL}/locale/zh-CN.json",
    "zh_CN": f"{API_BASE_URL}/locale/zh_CN.json",
    "ja-JP": f"{API_BASE_URL}/locale/ja-JP.json",
    "en-US": f"{API_BASE_URL}/locale/en-US.json",
}
