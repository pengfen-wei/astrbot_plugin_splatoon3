"""Splatoon3 API Client

基于 splatoon3.ink API 的 Python 封装
实现了 splatoon3api npm 包的所有功能
"""

import aiohttp
import time
import json
import asyncio
from typing import Optional, Any
from datetime import datetime, timezone

from astrbot.api import logger


class Splatoon3APIError(Exception):
    """Splatoon3 API 异常基类"""
    pass


class Splatoon3NetworkError(Splatoon3APIError):
    """网络请求异常"""
    pass


class Splatoon3DataError(Splatoon3APIError):
    """数据处理异常"""
    pass


class Splatoon3Client:
    """Splatoon3 API 客户端"""

    # 支持的语言
    LANGUAGES = {
        "en-US": "English (US)",
        "en-GB": "English (GB)",
        "de-DE": "Deutsch",
        "nl-NL": "Nederlands",
        "fr-FR": "Français (FR)",
        "fr-CA": "Français (CA)",
        "es-ES": "Español (ES)",
        "es-MX": "Español (MX)",
        "it-IT": "Italiano",
        "ru-RU": "Русский",
        "ja-JP": "日本語",
        "ko-KR": "한국어",
        "zh-CN": "中文(简体)",
        "zh-TW": "中文(台灣)",
    }

    # 祭典区域
    SPLATFEST_REGIONS = {
        "US": "The Americas, Australia, New Zealand",
        "EU": "Europe",
        "JP": "Japan",
        "AP": "Hong Kong, South Korea (Asia/Pacific)",
    }

    # API 基础URL
    BASE_URL = "https://splatoon3.ink/data"

    def __init__(self, language: str = "zh-CN", user_agent: str = None, cache_enabled: bool = True, cache_ttl: int = 60, max_cache_size: int = 50, debug: bool = False):
        """初始化客户端

        Args:
            language: 语言代码，默认中文简体
            user_agent: 自定义User-Agent
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存过期时间（秒）
            max_cache_size: 最大缓存条目数
            debug: 是否启用调试模式（输出API源数据到日志）
        """
        if language not in self.LANGUAGES:
            raise ValueError(f"不支持的语言: {language}。支持的语言: {list(self.LANGUAGES.keys())}")

        self.language = language
        self.user_agent = user_agent or "AstrBot-Splatoon3-Plugin/1.0"
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.debug = debug
        self._cache: dict[str, dict[str, Any]] = {}
        self._locale_cache: dict[str, dict] = {}
        self._session = None
        self._session_lock = asyncio.Lock()
        # 缓存锁，保护缓存字典的并发访问
        self._cache_lock = asyncio.Lock()
        # 缓存访问时间，用于主动驱逐
        self._cache_access_time: dict[str, float] = {}
        # 请求锁，防止并发请求同一资源时产生重复外部请求
        self._request_locks: dict[str, asyncio.Lock] = {}

    def _log_api_data(self, endpoint: str, data: dict):
        """记录API源数据到日志

        Args:
            endpoint: API端点
            data: API返回的原始数据
        """
        if not self.debug:
            return

        try:
            # 将数据格式化为JSON字符串（限制长度避免日志过大）
            data_str = json.dumps(data, ensure_ascii=False, indent=2)
            # 限制日志长度，避免输出过多
            if len(data_str) > 3000:
                data_str = data_str[:3000] + "\n... (数据已截断)"
            logger.info(f"[Splatoon3 API] 端点: {endpoint}, 原始数据:\n{data_str}")
        except (TypeError, ValueError):
            # JSON序列化失败，忽略
            pass

    def _get_cache_key(self, endpoint: str) -> str:
        """生成缓存键"""
        return f"{self.language}_{endpoint}"

    async def _get_cached_data(self, endpoint: str) -> Optional[dict]:
        """获取缓存数据"""
        if not self.cache_enabled:
            return None

        cache_key = self._get_cache_key(endpoint)
        async with self._cache_lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached["timestamp"] < self.cache_ttl:
                    # 更新访问时间
                    self._cache_access_time[cache_key] = time.time()
                    return cached["data"]
                # 缓存过期，删除
                del self._cache[cache_key]
                if cache_key in self._cache_access_time:
                    del self._cache_access_time[cache_key]
        return None

    async def _cleanup_expired_cache(self):
        """清理过期的缓存"""
        if not self.cache_enabled:
            return

        current_time = time.time()
        expired_keys = []
        least_recently_used = []
        
        async with self._cache_lock:
            # 清理过期缓存
            for cache_key, cached in self._cache.items():
                if current_time - cached["timestamp"] >= self.cache_ttl:
                    expired_keys.append(cache_key)
                else:
                    # 收集未过期的缓存，用于LRU淘汰
                    access_time = self._cache_access_time.get(cache_key, cached["timestamp"])
                    least_recently_used.append((access_time, cache_key))
            
            # 删除过期缓存
            for cache_key in expired_keys:
                del self._cache[cache_key]
                if cache_key in self._cache_access_time:
                    del self._cache_access_time[cache_key]
            
            # 当缓存大小超过阈值时，使用LRU策略删除最久未使用的缓存
            if len(self._cache) > self.max_cache_size:
                # 按访问时间排序，删除最久未使用的
                least_recently_used.sort(key=lambda x: x[0])
                to_remove = least_recently_used[:len(self._cache) - self.max_cache_size]
                for _, cache_key in to_remove:
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        if cache_key in self._cache_access_time:
                            del self._cache_access_time[cache_key]
                        expired_keys.append(cache_key)
        
        if expired_keys:
            logger.info(f"[Splatoon3] 清理了 {len(expired_keys)} 个缓存（过期+LRU淘汰）")

    async def _get_session(self):
        """获取或创建aiohttp ClientSession"""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                )
        return self._session

    async def close(self):
        """关闭ClientSession"""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

    async def _set_cached_data(self, endpoint: str, data: dict):
        """设置缓存数据"""
        if not self.cache_enabled:
            return

        cache_key = self._get_cache_key(endpoint)
        trigger_cleanup = False
        async with self._cache_lock:
            self._cache[cache_key] = {
                "data": data,
                "timestamp": time.time(),
            }
            # 记录访问时间
            self._cache_access_time[cache_key] = time.time()
            # 检查是否需要触发清理（每10次设置缓存操作触发一次）
            if len(self._cache) % 10 == 0:
                trigger_cleanup = True
        
        # 在锁外部执行清理操作，避免死锁
        if trigger_cleanup:
            await self._cleanup_expired_cache()

    async def _fetch_data(self, endpoint: str) -> dict:
        """从API获取数据"""
        # 先尝试从缓存获取
        cached = await self._get_cached_data(endpoint)
        if cached is not None:
            self._log_api_data(f"{endpoint} (cached)", cached)
            return cached

        # 获取请求锁，防止并发请求同一资源
        cache_key = self._get_cache_key(endpoint)
        if cache_key not in self._request_locks:
            self._request_locks[cache_key] = asyncio.Lock()
        request_lock = self._request_locks[cache_key]

        async with request_lock:
            # 再次检查缓存，可能在等待锁的过程中已经被其他请求缓存
            cached = await self._get_cached_data(endpoint)
            if cached is not None:
                self._log_api_data(f"{endpoint} (cached after lock)", cached)
                return cached

            url = f"{self.BASE_URL}/{endpoint}"

            # 使用复用的ClientSession
            session = await self._get_session()
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Splatoon3DataError(f"API请求失败: {response.status}")
                    try:
                        data = await response.json()
                    except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
                        raise Splatoon3DataError(f"JSON解析失败: {str(e)}") from e
                    await self._set_cached_data(endpoint, data)
                    self._log_api_data(endpoint, data)
                    return data
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                raise Splatoon3NetworkError(f"网络请求失败: {str(e)}") from e
            except Exception as e:
                if not isinstance(e, Splatoon3APIError):
                    raise Splatoon3DataError(f"获取数据失败: {str(e)}") from e
                raise

    async def _get_locale(self) -> dict:
        """获取本地化数据"""
        # 先尝试从缓存获取
        async with self._cache_lock:
            if self.language in self._locale_cache:
                return self._locale_cache[self.language]

        # 获取请求锁，防止并发请求同一语言的本地化数据
        locale_key = f"locale_{self.language}"
        if locale_key not in self._request_locks:
            self._request_locks[locale_key] = asyncio.Lock()
        request_lock = self._request_locks[locale_key]

        async with request_lock:
            # 再次检查缓存，可能在等待锁的过程中已经被其他请求缓存
            async with self._cache_lock:
                if self.language in self._locale_cache:
                    return self._locale_cache[self.language]

            url = f"{self.BASE_URL}/locale/{self.language}.json"

            # 使用复用的ClientSession
            session = await self._get_session()
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        try:
                            locale_data = await response.json()
                        except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
                            raise Splatoon3DataError(f"JSON解析失败: {str(e)}") from e
                        async with self._cache_lock:
                            self._locale_cache[self.language] = locale_data
                        self._log_api_data(f"locale/{self.language}.json", locale_data)
                        return locale_data
                    else:
                        raise Splatoon3DataError(f"获取本地化数据失败: {response.status}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                raise Splatoon3NetworkError(f"网络请求失败: {str(e)}") from e
            except Exception as e:
                if not isinstance(e, Splatoon3APIError):
                    raise Splatoon3DataError(f"获取本地化数据失败: {str(e)}") from e
                raise

    def _translate_by_id(self, item_id: str, locale: dict, category: str = "stages", field: str = "name") -> str:
        """根据ID翻译

        Args:
            item_id: 项目ID
            locale: 本地化数据
            category: 类别（stages, rules, weapons等）
            field: 字段名（name, desc等）
        """
        if not item_id or not locale:
            return ""

        category_data = locale.get(category, {})
        item = category_data.get(item_id, {})

        if isinstance(item, dict):
            return item.get(field, "")
        return str(item) if item else ""

    def _get_nested(self, data: dict, *keys, default=None):
        """安全获取嵌套字典值

        Args:
            data: 字典数据
            *keys: 嵌套键路径
            default: 默认值

        Returns:
            获取的值或默认值
        """
        result = data
        for i, key in enumerate(keys):
            if isinstance(result, dict):
                # 如果不是最后一个键，使用 {} 作为中间默认值
                # 如果是最后一个键，使用调用方指定的默认值
                if i == len(keys) - 1:
                    result = result.get(key, default)
                else:
                    result = result.get(key, {})
            else:
                return default
        return result

    def _format_time(self, timestamp: int | float | str | None) -> str:
        """格式化时间戳

        Args:
            timestamp: 时间戳，可以是整数、浮点数或字符串
        """
        if timestamp is None:
            return "未知"
        try:
            # 处理字符串类型的时间戳
            if isinstance(timestamp, str):
                # 尝试解析 ISO 格式时间字符串
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d %H:%M")
                # 尝试转换为数字
                timestamp = float(timestamp)
            # 使用 UTC 时区处理时间戳，与 API 返回的 UTC 时间保持一致
            dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError, OSError) as e:
            try:
                logger.warning(f"[Splatoon3] 时间格式化失败: {str(e)}, 时间戳: {timestamp}")
            except Exception:
                # 记录失败，忽略
                pass
            return str(timestamp) if timestamp else "未知"

    async def get_stages(self) -> dict:
        """获取所有地图轮换（当前+未来11个）

        包括涂地、真格、X赛、祭典模式
        """
        data = await self._fetch_data("schedules.json")
        locale = await self._get_locale()

        result = {
            "regular": [],  # 涂地
            "bankara": [],  # 真格
            "x": [],  # X赛
            "fest": [],  # 祭典
        }

        # 处理涂地模式
        for match in self._get_nested(data, "data", "regularSchedules", "nodes", default=[]):
            setting = match.get("regularMatchSetting", {})
            stages = setting.get("vsStages", [])
            rule = setting.get("vsRule", {})

            result["regular"].append({
                "start_time": self._format_time(match.get("startTime")),
                "end_time": self._format_time(match.get("endTime")),
                "stages": [self._translate_by_id(s.get("id"), locale, "stages") or s.get("name", "") for s in stages],
                "mode": self._translate_by_id(rule.get("id"), locale, "rules") or rule.get("name", ""),
            })

        # 处理真格模式
        for match in self._get_nested(data, "data", "bankaraSchedules", "nodes", default=[]):
            settings = match.get("bankaraMatchSettings", [])
            open_match = settings[0] if len(settings) > 0 else {}
            challenge_match = settings[1] if len(settings) > 1 else {}

            open_rule = open_match.get("vsRule", {}) if open_match else {}
            challenge_rule = challenge_match.get("vsRule", {}) if challenge_match else {}

            result["bankara"].append({
                "start_time": self._format_time(match.get("startTime")),
                "end_time": self._format_time(match.get("endTime")),
                "open": {
                    "stages": [self._translate_by_id(s.get("id"), locale, "stages") or s.get("name", "") for s in open_match.get("vsStages", [])],
                    "mode": self._translate_by_id(open_rule.get("id"), locale, "rules") or open_rule.get("name", ""),
                },
                "challenge": {
                    "stages": [self._translate_by_id(s.get("id"), locale, "stages") or s.get("name", "") for s in challenge_match.get("vsStages", [])],
                    "mode": self._translate_by_id(challenge_rule.get("id"), locale, "rules") or challenge_rule.get("name", ""),
                },
            })

        # 处理X赛
        for match in self._get_nested(data, "data", "xSchedules", "nodes", default=[]):
            setting = match.get("xMatchSetting", {})
            stages = setting.get("vsStages", [])
            rule = setting.get("vsRule", {})

            result["x"].append({
                "start_time": self._format_time(match.get("startTime")),
                "end_time": self._format_time(match.get("endTime")),
                "stages": [self._translate_by_id(s.get("id"), locale, "stages") or s.get("name", "") for s in stages],
                "mode": self._translate_by_id(rule.get("id"), locale, "rules") or rule.get("name", ""),
            })

        # 处理祭典
        for match in self._get_nested(data, "data", "festSchedules", "nodes", default=[]):
            setting = match.get("festMatchSetting", {})
            stages = setting.get("vsStages", []) if setting else []

            result["fest"].append({
                "start_time": self._format_time(match.get("startTime")),
                "end_time": self._format_time(match.get("endTime")),
                "stages": [self._translate_by_id(s.get("id"), locale, "stages") or s.get("name", "") for s in stages],
            })

        return result

    async def get_current_stages(self) -> dict:
        """获取当前地图"""
        all_stages = await self.get_stages()
        return {
            "regular": all_stages["regular"][0] if all_stages["regular"] else None,
            "bankara": all_stages["bankara"][0] if all_stages["bankara"] else None,
            "x": all_stages["x"][0] if all_stages["x"] else None,
            "fest": all_stages["fest"][0] if all_stages["fest"] else None,
        }

    async def get_next_stages(self) -> dict:
        """获取下一时段地图"""
        all_stages = await self.get_stages()
        return {
            "regular": all_stages["regular"][1] if len(all_stages["regular"]) > 1 else None,
            "bankara": all_stages["bankara"][1] if len(all_stages["bankara"]) > 1 else None,
            "x": all_stages["x"][1] if len(all_stages["x"]) > 1 else None,
            "fest": all_stages["fest"][1] if len(all_stages["fest"]) > 1 else None,
        }

    def _parse_salmon_run_schedule(self, schedule: dict, locale: dict, run_type: str) -> dict:
        """解析鲑鱼跑日程
        
        Args:
            schedule: 日程数据
            locale: 语言数据
            run_type: 鲑鱼跑类型
            
        Returns:
            解析后的鲑鱼跑数据
        """
        setting = schedule.get("setting", {})
        stage = setting.get("coopStage", {})
        boss = setting.get("boss", {})

        return {
            "start_time": self._format_time(schedule.get("startTime")),
            "end_time": self._format_time(schedule.get("endTime")),
            "start_timestamp": schedule.get("startTime"),  # 添加原始时间戳用于排序
            "stage": self._translate_by_id(stage.get("id"), locale, "stages") or stage.get("name", ""),
            "weapons": [self._translate_by_id(w.get("__splatoon3ink_id"), locale, "weapons") or w.get("name", "") for w in setting.get("weapons", [])],
            "boss": self._translate_by_id(boss.get("id"), locale, "bosses") or boss.get("name", ""),
            "type": run_type
        }

    async def get_salmon_run(self) -> list[dict]:
        """获取鲑鱼跑（Salmon Run）日程"""
        data = await self._fetch_data("schedules.json")
        locale = await self._get_locale()

        result = []

        # 获取常规鲑鱼跑
        regular_schedules = self._get_nested(data, "data", "coopGroupingSchedule", "regularSchedules", "nodes", default=[])
        for schedule in regular_schedules:
            result.append(self._parse_salmon_run_schedule(schedule, locale, "常规鲑鱼跑"))

        # 获取大规模鲑鱼跑（Big Run）
        big_run_schedules = self._get_nested(data, "data", "coopGroupingSchedule", "bigRunSchedules", "nodes", default=[])
        for schedule in big_run_schedules:
            result.append(self._parse_salmon_run_schedule(schedule, locale, "大规模鲑鱼跑"))

        # 按原始时间戳排序，避免格式化字符串排序问题
        result.sort(key=lambda x: x.get("start_timestamp", 0))

        return result

    async def get_challenges(self) -> list[dict]:
        """获取挑战（Challenges）"""
        data = await self._fetch_data("schedules.json")
        locale = await self._get_locale()

        result = []
        for challenge in self._get_nested(data, "data", "eventSchedules", "nodes", default=[]):
            league_match_setting = challenge.get("leagueMatchSetting", {})
            event = league_match_setting.get("leagueMatchEvent", {})
            time_periods = challenge.get("timePeriods", [])

            # 为每个时间段创建一个挑战条目
            for period in time_periods:
                result.append({
                    "name": self._translate_by_id(event.get("id"), locale, "events") or event.get("name", ""),
                    "description": self._translate_by_id(event.get("id"), locale, "events", "desc") or event.get("desc", ""),
                    "start_time": self._format_time(period.get("startTime")),
                    "end_time": self._format_time(period.get("endTime")),
                    "regulation": event.get("regulation", ""),
                })

        return result

    async def get_splatnet_gear(self) -> list[dict]:
        """获取Splatnet商店装备"""
        data = await self._fetch_data("gear.json")
        locale = await self._get_locale()

        result = []
        for gear in self._get_nested(data, "data", "gesotown", "limitedGears", default=[]):
            gear_data = gear.get("gear", {})
            brand = gear_data.get("brand", {})
            primary_power = gear_data.get("primaryGearPower", {})
            secondary_powers = gear_data.get("additionalGearPowers", [])

            result.append({
                "name": self._translate_by_id(gear_data.get("__splatoon3ink_id"), locale, "gear") or gear_data.get("name", ""),
                "brand": self._translate_by_id(brand.get("id"), locale, "brands") or brand.get("name", ""),
                "price": gear.get("price"),
                "rarity": gear_data.get("rarity"),
                "primary_ability": self._translate_by_id(primary_power.get("__splatoon3ink_id"), locale, "powers") or primary_power.get("name", ""),
                "secondary_abilities": [self._translate_by_id(p.get("__splatoon3ink_id"), locale, "powers") or p.get("name", "") for p in secondary_powers],
                "end_time": self._format_time(gear.get("saleEndTime")),
                "image": gear_data.get("image", {}).get("url"),
            })

        return result

    async def _get_splatfests(self, states: list, region: str = None) -> list[dict]:
        """获取指定状态的祭典

        Args:
            states: 祭典状态列表
            region: 区域代码 (US, EU, JP, AP)，None表示所有区域
        
        Raises:
            ValueError: 如果区域代码无效
        """
        if region and region.upper() not in self.SPLATFEST_REGIONS:
            raise ValueError(f"无效的区域代码: {region}。支持的区域: {list(self.SPLATFEST_REGIONS.keys())}")
        
        data = await self._fetch_data("festivals.json")
        locale = await self._get_locale()

        result = []
        if region:
            regions_to_check = [region.lower()]
        else:
            regions_to_check = ["us", "eu", "jp", "ap"]

        for reg in regions_to_check:
            for fest in self._get_nested(data, "data", reg, "nodes", default=[]):
                if fest.get("state") in states:
                    teams = fest.get("teams", [])
                    team_data = []
                    for t in teams:
                        team_info = {
                            "name": self._translate_by_id(t.get("id"), locale, "festivals") or t.get("name", ""),
                            "color": t.get("color"),
                        }
                        # 只有过去的祭典才有结果
                        if fest.get("state") == "CLOSED":
                            team_info["result"] = t.get("result")
                        team_data.append(team_info)
                    
                    fest_info = {
                        "title": self._translate_by_id(fest.get("id"), locale, "festivals") or fest.get("title", ""),
                        "region": reg.upper(),
                        "start_time": self._format_time(fest.get("startTime")),
                        "end_time": self._format_time(fest.get("endTime")),
                        "teams": team_data,
                    }
                    # 正在进行的祭典需要包含状态
                    if fest.get("state") in ["FIRST_HALF", "SECOND_HALF"]:
                        fest_info["state"] = fest.get("state")
                    
                    result.append(fest_info)

        return result

    async def get_running_splatfests(self, region: str = None) -> list[dict]:
        """获取正在进行的祭典

        Args:
            region: 区域代码 (US, EU, JP, AP)，None表示所有区域
        
        Raises:
            ValueError: 如果区域代码无效
        """
        return await self._get_splatfests(["FIRST_HALF", "SECOND_HALF"], region)

    async def get_upcoming_splatfests(self, region: str = None) -> list[dict]:
        """获取即将开始的祭典

        Args:
            region: 区域代码 (US, EU, JP, AP)，None表示所有区域
        
        Raises:
            ValueError: 如果区域代码无效
        """
        return await self._get_splatfests(["SCHEDULED"], region)

    async def get_past_splatfests(self, region: str = None) -> list[dict]:
        """获取过去的祭典

        Args:
            region: 区域代码 (US, EU, JP, AP)，None表示所有区域
        
        Raises:
            ValueError: 如果区域代码无效
        """
        return await self._get_splatfests(["CLOSED"], region)
