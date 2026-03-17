"""Splatoon3 查询插件

基于 splatoon3.ink API 的 AstrBot 插件
实现了 splatoon3api npm 包的所有功能
"""

import json
import time
from typing import Dict, List
import asyncio

from astrbot.api import logger
from astrbot.api.star import Star, Context, StarTools
from astrbot.api.event import filter
from astrbot.api.event import AstrMessageEvent

from .splatoon3_client import Splatoon3Client


class Splatoon3Plugin(Star):
    """Splatoon3 斯普拉遁3查询插件

    功能：
    1. 查询当前/下一时段地图轮换
    2. 查询鲑鱼跑日程
    3. 查询挑战活动
    4. 查询Splatnet商店装备
    5. 查询祭典信息（进行中/即将开始/已结束）
    6. 支持多语言切换
    """

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config if config else {}

        # 数据目录
        self.data_dir = StarTools.get_data_dir()
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 用户配置文件路径
        self.user_config_file = self.data_dir / "user_configs.json"
        # 文件操作锁，防止并发写入
        self._config_lock = asyncio.Lock()
        # 客户端缓存锁，防止并发创建客户端
        self._client_lock = asyncio.Lock()
        self.user_configs = self._load_user_configs()

        # 调试模式（从配置中读取，默认关闭）
        self.debug = self.config.get("debug", False)
        
        # 客户端缓存，按用户ID存储
        self.clients: Dict[str, Splatoon3Client] = {}
        # 客户端最后使用时间，用于回收策略
        self.clients_last_used: Dict[str, float] = {}
        # 客户端回收时间（秒），默认1小时
        self.client_ttl = self.config.get("client_ttl", 3600)
        # 清理间隔（秒），默认10分钟
        self.cleanup_interval = self.config.get("cleanup_interval", 600)
        # 清理任务
        self._cleanup_task = None
        
        # 输出配置信息（用于调试）
        logger.info(f"[Splatoon3] 插件配置: {self.config}")
        logger.info(f"[Splatoon3] 调试模式: {self.debug}")
        logger.info(f"[Splatoon3] 客户端TTL: {self.client_ttl}秒")
        logger.info(f"[Splatoon3] 清理间隔: {self.cleanup_interval}秒")

        if self.debug:
            logger.info("[Splatoon3] 调试模式已启用，API源数据将输出到日志")
        
        # 清理任务启动标志
        self._cleanup_started = False

    def _load_user_configs(self) -> Dict:
        """加载用户配置"""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[Splatoon3] 加载用户配置失败: {str(e)}")
        return {}

    async def _save_user_configs(self):
        """保存用户配置"""
        async with self._config_lock:
            try:
                with open(self.user_config_file, "w", encoding="utf-8") as f:
                    json.dump(self.user_configs, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"[Splatoon3] 保存用户配置失败: {str(e)}")

    def _get_user_id(self, event: AstrMessageEvent) -> str:
        """获取用户唯一标识"""
        platform = getattr(event, 'platform', getattr(event, 'platform_name', 'unknown'))
        sender_id = None
        # 尝试获取用户ID的不同属性名
        for attr in ['sender_id', 'user_id', 'from_user', 'from_user_id']:
            if hasattr(event, attr):
                value = getattr(event, attr)
                if value is not None and value != '':
                    # 确保值是字符串类型，避免对象引用导致的不稳定
                    sender_id = str(value)
                    break
        
        if sender_id is None:
            raise ValueError(f"无法从事件中获取用户ID，平台: {platform}")
        
        return f"{platform}_{sender_id}"

    async def _get_user_language(self, user_id: str) -> str:
        """获取用户设置的语言"""
        async with self._config_lock:
            if user_id not in self.user_configs:
                self.user_configs[user_id] = {"language": "zh-CN"}
                # 在锁内保存配置，避免并发覆盖
                try:
                    with open(self.user_config_file, "w", encoding="utf-8") as f:
                        json.dump(self.user_configs, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(f"[Splatoon3] 保存用户配置失败: {str(e)}")
            return self.user_configs[user_id].get("language", "zh-CN")

    async def _set_user_language(self, user_id: str, language: str):
        """设置用户语言"""
        async with self._config_lock:
            if user_id not in self.user_configs:
                self.user_configs[user_id] = {}
            self.user_configs[user_id]["language"] = language
            # 在锁内保存配置，避免并发覆盖
            try:
                with open(self.user_config_file, "w", encoding="utf-8") as f:
                    json.dump(self.user_configs, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"[Splatoon3] 保存用户配置失败: {str(e)}")
        
        # 清除缓存的客户端实例，确保下次获取时使用新语言
        client_to_close = None
        async with self._client_lock:
            if user_id in self.clients:
                client_to_close = self.clients[user_id]
                del self.clients[user_id]
            # 同步清理最后使用时间
            if user_id in self.clients_last_used:
                del self.clients_last_used[user_id]
        
        # 在锁外部关闭客户端，避免锁内等待
        if client_to_close and hasattr(client_to_close, 'close'):
            try:
                await client_to_close.close()
            except Exception as e:
                logger.error(f"[Splatoon3] 关闭客户端 {user_id} 失败: {str(e)}")

    async def close(self):
        """关闭所有客户端实例，释放资源"""
        # 停止定时清理任务
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("[Splatoon3] 定时清理任务已停止")
        
        # 收集所有客户端
        clients_to_close = []
        async with self._client_lock:
            clients_to_close = list(self.clients.values())
            self.clients.clear()
            self.clients_last_used.clear()
        
        # 在锁外部并发关闭所有客户端
        if clients_to_close:
            close_tasks = []
            for i, client in enumerate(clients_to_close):
                if hasattr(client, 'close'):
                    close_tasks.append(self._close_client_async(i, client))
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
    
    async def _close_client_async(self, index: int, client):
        """异步关闭客户端"""
        try:
            await client.close()
        except Exception as e:
            logger.error(f"[Splatoon3] 关闭客户端 {index} 失败: {str(e)}")

    async def _get_client(self, user_id: str) -> Splatoon3Client:
        """获取指定用户的API客户端"""
        
        # 延迟启动定时清理任务，确保事件循环已就绪
        if not self._cleanup_started:
            async with self._client_lock:
                # 再次检查，防止竞态条件
                if not self._cleanup_started:
                    self._start_cleanup_task()
                    self._cleanup_started = True
        
        # 先检查缓存
        async with self._client_lock:
            if user_id in self.clients:
                # 更新最后使用时间
                self.clients_last_used[user_id] = time.time()
                return self.clients[user_id]
        
        # 如果缓存中没有，获取语言设置并创建客户端
        language = await self._get_user_language(user_id)
        
        # 再次检查并创建客户端
        async with self._client_lock:
            if user_id not in self.clients:
                self.clients[user_id] = Splatoon3Client(language=language, debug=self.debug)
                self.clients_last_used[user_id] = time.time()
            else:
                # 更新最后使用时间
                self.clients_last_used[user_id] = time.time()
            return self.clients[user_id]

    async def _cleanup_expired_clients(self):
        """清理过期的客户端实例"""
        current_time = time.time()
        expired_users = []
        clients_to_close = []
        
        # 收集过期客户端
        async with self._client_lock:
            for user_id, last_used in self.clients_last_used.items():
                if current_time - last_used > self.client_ttl:
                    expired_users.append(user_id)
                    if user_id in self.clients:
                        clients_to_close.append((user_id, self.clients[user_id]))
            
            # 从缓存中删除过期客户端
            for user_id in expired_users:
                if user_id in self.clients:
                    del self.clients[user_id]
                if user_id in self.clients_last_used:
                    del self.clients_last_used[user_id]
        
        # 在锁外部关闭客户端
        if clients_to_close:
            close_tasks = []
            for user_id, client in clients_to_close:
                if hasattr(client, 'close'):
                    close_tasks.append(self._close_client_async(user_id, client))
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
        
        if expired_users:
            logger.info(f"[Splatoon3] 清理了 {len(expired_users)} 个过期客户端")

    async def _cleanup_task_loop(self):
        """定时清理任务循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_clients()
            except asyncio.CancelledError:
                logger.info("[Splatoon3] 定时清理任务被取消")
                raise
            except Exception as e:
                logger.error(f"[Splatoon3] 定时清理任务失败: {str(e)}")

    def _start_cleanup_task(self):
        """启动定时清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_task_loop())
            logger.info("[Splatoon3] 定时清理任务已启动")

    @filter.command("splat3帮助")
    async def splat3_help(self, event: AstrMessageEvent):
        """显示Splatoon3插件帮助信息"""
        help_text = """🦑 Splatoon3 查询插件

📋 命令列表：

🗺️ 地图相关：
  /splat3当前 - 查询当前地图
  /splat3下一 - 查询下一时段地图
  /splat3全部 - 查询所有地图轮换

🐟 鲑鱼跑：
  /splat3鲑鱼 - 查询鲑鱼跑日程

⚔️ 挑战活动：
  /splat3挑战 - 查询挑战活动

🛍️ 装备商店：
  /splat3装备 - 查询Splatnet装备

🎉 祭典信息：
  /splat3祭典 - 祭典信息汇总（进行中、即将开始、过去的）
  /splat3祭典进行 - 正在进行的祭典
  /splat3祭典即将 - 即将开始的祭典
  /splat3祭典过去 - 过去的祭典

⚙️ 设置：
  /splat3语言 - 查看支持的语言列表
  /splat3语言 <语言代码> - 切换语言

💡 提示：祭典区域说明
  US: 美洲、澳洲、新西兰
  EU: 欧洲
  JP: 日本
  AP: 香港、韩国（亚太）

🔧 调试模式：
  在插件配置中设置 debug: true 可启用API源数据日志输出
"""

        yield event.plain_result(help_text)

    # 注意：由于 AstrBot 版本限制，暂时移除自然语言支持
    # 后续版本更新后可重新添加

    @filter.command("splat3语言")
    async def splat3_lang(self, event: AstrMessageEvent, lang_code: str = None):
        """设置或查看语言"""
        user_id = self._get_user_id(event)

        if not lang_code:
            # 显示支持的语言列表
            current_lang = await self._get_user_language(user_id)
            lang_list = "\n".join([f"  {code}: {name}" for code, name in Splatoon3Client.LANGUAGES.items()])
            yield event.plain_result(f"🌐 当前语言: {current_lang}\n\n支持的语言：\n{lang_list}\n\n使用 /splat3语言 <语言代码> 切换语言")
            return

        # 切换语言
        lang_code = lang_code.strip()
        if lang_code not in Splatoon3Client.LANGUAGES:
            yield event.plain_result(f"❌ 不支持的语言代码: {lang_code}\n请使用 /splat3语言 查看支持的语言列表")
            return

        # 切换语言
        await self._set_user_language(user_id, lang_code)
        yield event.plain_result(f"✅ 语言已切换为: {Splatoon3Client.LANGUAGES[lang_code]}")

    def _format_stages(self, stages: Dict, title: str) -> str:
        """格式化地图数据

        Args:
            stages: 地图数据
            title: 标题

        Returns:
            格式化后的字符串
        """
        result = f"🗺️ {title}\n" + "=" * 30 + "\n\n"

        # 涂地模式
        if stages.get("regular"):
            r = stages["regular"]
            result += f"🎨 涂地模式\n"
            result += f"⏰ {r['start_time']} ~ {r['end_time']}\n"
            result += f"📍 {' / '.join(r['stages'])}\n\n"

        # 真格模式
        if stages.get("bankara"):
            b = stages["bankara"]
            result += f"🏆 真格模式\n"
            result += f"⏰ {b['start_time']} ~ {b['end_time']}\n"
            if b.get("open") and b["open"].get("stages"):
                result += f"🟢 开放: {' / '.join(b['open']['stages'])} ({b['open']['mode']})\n"
            if b.get("challenge") and b["challenge"].get("stages"):
                result += f"🔴 挑战: {' / '.join(b['challenge']['stages'])} ({b['challenge']['mode']})\n"
            result += "\n"

        # X赛
        if stages.get("x") and stages["x"]:
            x = stages["x"]
            result += f"❌ X赛\n"
            result += f"⏰ {x['start_time']} ~ {x['end_time']}\n"
            result += f"📍 {' / '.join(x['stages'])} ({x['mode']})\n\n"

        # 祭典
        if stages.get("fest") and stages["fest"]:
            f = stages["fest"]
            result += f"🎉 祭典模式\n"
            result += f"⏰ {f['start_time']} ~ {f['end_time']}\n"
            result += f"📍 {' / '.join(f['stages'])}\n\n"

        return result.strip()

    @filter.command("splat3当前")
    async def splat3_current(self, event: AstrMessageEvent):
        """查询当前地图"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            stages = await client.get_current_stages()
            result = self._format_stages(stages, "当前地图轮换")
            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"[Splatoon3] 获取地图信息失败: {str(e)}")
            yield event.plain_result("❌ 获取地图信息失败，请稍后重试")

    @filter.command("splat3下一")
    async def splat3_next(self, event: AstrMessageEvent):
        """查询下一时段地图"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            stages = await client.get_next_stages()
            result = self._format_stages(stages, "下一时段地图轮换")
            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"[Splatoon3] 获取地图信息失败: {str(e)}")
            yield event.plain_result("❌ 获取地图信息失败，请稍后重试")

    @filter.command("splat3全部")
    async def splat3_all(self, event: AstrMessageEvent, mode: str = "regular"):
        """查询所有地图轮换

        Args:
            mode: 模式类型 (regular, bankara, x, fest)
        """
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            stages = await client.get_stages()

            mode_names = {
                "regular": "涂地模式",
                "bankara": "真格模式",
                "x": "X赛",
                "fest": "祭典模式"
            }

            mode_name = mode_names.get(mode, mode)

            if mode not in stages or not stages[mode]:
                yield event.plain_result(f"❌ 没有找到 {mode_name} 的数据")
                return

            result = f"🗺️ {mode_name} - 未来轮换\n" + "=" * 30 + "\n\n"

            # 只显示前5个时段
            for i, s in enumerate(stages[mode][:5]):
                result += f"⏰ {s['start_time']} ~ {s['end_time']}\n"

                if mode == "bankara":
                    if s.get("open") and s["open"].get("stages"):
                        result += f"🟢 开放: {' / '.join(s['open']['stages'])} ({s['open']['mode']})\n"
                    if s.get("challenge") and s["challenge"].get("stages"):
                        result += f"🔴 挑战: {' / '.join(s['challenge']['stages'])} ({s['challenge']['mode']})\n"
                else:
                    result += f"📍 {' / '.join(s['stages'])}\n"

                if mode == "x" and s.get("mode"):
                    result += f"🎮 规则: {s['mode']}\n"

                result += "\n"

            yield event.plain_result(result.strip())

        except Exception as e:
            logger.error(f"[Splatoon3] 获取地图信息失败: {str(e)}")
            yield event.plain_result("❌ 获取地图信息失败，请稍后重试")

    @filter.command("splat3鲑鱼")
    async def splat3_coop(self, event: AstrMessageEvent):
        """查询鲑鱼跑日程"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            schedules = await client.get_salmon_run()

            if not schedules:
                yield event.plain_result("🐟 暂无鲑鱼跑日程")
                return

            result = "🐟 鲑鱼跑日程\n" + "=" * 30 + "\n\n"

            for i, s in enumerate(schedules[:4]):  # 显示前4个
                result += f"🏷️ 类型: {s.get('type', '鲑鱼跑')}\n"
                result += f"⏰ {s['start_time']} ~ {s['end_time']}\n"
                result += f"📍 地图: {s['stage']}\n"
                result += f"👹 Boss: {s['boss']}\n"
                result += f"🔫 武器: {' / '.join(s['weapons'])}\n"
                result += "\n"

            yield event.plain_result(result.strip())

        except Exception as e:
            logger.error(f"[Splatoon3] 获取鲑鱼跑信息失败: {str(e)}")
            yield event.plain_result("❌ 获取鲑鱼跑信息失败，请稍后重试")

    @filter.command("splat3挑战")
    async def splat3_challenge(self, event: AstrMessageEvent):
        """查询挑战活动"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            challenges = await client.get_challenges()

            if not challenges:
                yield event.plain_result("⚔️ 暂无挑战活动")
                return

            result = "⚔️ 挑战活动\n" + "=" * 30 + "\n\n"

            for c in challenges:
                result += f"🏷️ {c['name']}\n"
                result += f"📝 {c['description']}\n"
                result += f"⏰ {c['start_time']} ~ {c['end_time']}\n"
                if c.get('regulation'):
                    result += f"📋 规则: {c['regulation']}\n"
                result += "\n"

            yield event.plain_result(result.strip())

        except Exception as e:
            logger.error(f"[Splatoon3] 获取挑战活动失败: {str(e)}")
            yield event.plain_result("❌ 获取挑战活动失败，请稍后重试")

    @filter.command("splat3装备")
    async def splat3_gear(self, event: AstrMessageEvent):
        """查询Splatnet装备"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            gears = await client.get_splatnet_gear()

            if not gears:
                yield event.plain_result("🛍️ 暂无Splatnet装备")
                return

            result = "🛍️ Splatnet 装备商店\n" + "=" * 30 + "\n\n"

            for g in gears[:6]:  # 显示前6个
                result += f"👕 {g['name']}\n"
                result += f"🏷️ 品牌: {g['brand']}\n"
                result += f"💰 价格: {g['price']} 金币\n"
                rarity = g.get('rarity', 0)
                if rarity:
                    result += f"⭐ 稀有度: {'★' * rarity}\n"
                result += f"🔷 主技能: {g['primary_ability']}\n"
                if g.get('secondary_abilities'):
                    result += f"🔹 副技能: {' / '.join(g['secondary_abilities'])}\n"
                result += f"⏰ 截止时间: {g['end_time']}\n"
                result += "\n"

            yield event.plain_result(result.strip())

        except Exception as e:
            logger.error(f"[Splatoon3] 获取装备信息失败: {str(e)}")
            yield event.plain_result("❌ 获取装备信息失败，请稍后重试")

    def _format_festivals(self, festivals: List[Dict], title: str) -> str:
        """格式化祭典信息
        
        Args:
            festivals: 祭典数据列表
            title: 标题（如果为空字符串则不显示标题）
            
        Returns:
            格式化后的字符串
        """
        if not festivals:
            return f"{title}\n\n暂无相关祭典信息" if title else "暂无相关祭典信息"
        
        result = ""
        if title:
            result = f"{title}\n" + "=" * 30 + "\n\n"
        
        for f in festivals:
            result += f"🎯 {f['title']}\n"
            result += f"🌍 区域: {f['region']}\n"
            result += f"⏰ {f['start_time']} ~ {f['end_time']}\n"
            
            if f.get('teams'):
                teams_text = " vs ".join([f"{t['name']}" for t in f['teams']])
                result += f"👥 阵营: {teams_text}\n"
            
            result += "\n"
        
        return result.strip()

    @filter.command("splat3祭典进行")
    async def splat3_fest_running(self, event: AstrMessageEvent, region: str = None):
        """查询正在进行的祭典"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            festivals = await client.get_running_splatfests(region)
            title = "🎉 正在进行的祭典"
            result = self._format_festivals(festivals, title)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"[Splatoon3] 获取祭典信息失败: {str(e)}")
            yield event.plain_result("❌ 获取祭典信息失败，请稍后重试")

    @filter.command("splat3祭典即将")
    async def splat3_fest_upcoming(self, event: AstrMessageEvent, region: str = None):
        """查询即将开始的祭典"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            festivals = await client.get_upcoming_splatfests(region)
            title = "📅 即将开始的祭典"
            result = self._format_festivals(festivals, title)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"[Splatoon3] 获取祭典信息失败: {str(e)}")
            yield event.plain_result("❌ 获取祭典信息失败，请稍后重试")

    @filter.command("splat3祭典过去")
    async def splat3_fest_past(self, event: AstrMessageEvent, region: str = None):
        """查询过去的祭典"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            festivals = await client.get_past_splatfests(region)
            title = "📜 过去的祭典"
            result = self._format_festivals(festivals, title)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"[Splatoon3] 获取祭典信息失败: {str(e)}")
            yield event.plain_result("❌ 获取祭典信息失败，请稍后重试")

    @filter.command("splat3祭典")
    async def splat3_fest_all(self, event: AstrMessageEvent, region: str = None):
        """查询所有祭典信息（进行中、即将开始、过去的）"""
        user_id = self._get_user_id(event)
        client = await self._get_client(user_id)

        try:
            # 获取所有祭典数据
            running_festivals = await client.get_running_splatfests(region)
            upcoming_festivals = await client.get_upcoming_splatfests(region)
            past_festivals = await client.get_past_splatfests(region)

            result = "🎪 祭典信息汇总\n" + "=" * 30 + "\n\n"

            # 进行中的祭典
            if running_festivals:
                result += "🎉 正在进行的祭典\n" + "-" * 20 + "\n\n"
                result += self._format_festivals(running_festivals, "")
            else:
                result += "🎉 正在进行的祭典\n" + "-" * 20 + "\n暂无相关祭典信息\n\n"

            # 即将开始的祭典
            if upcoming_festivals:
                result += "📅 即将开始的祭典\n" + "-" * 20 + "\n\n"
                result += self._format_festivals(upcoming_festivals, "")
            else:
                result += "📅 即将开始的祭典\n" + "-" * 20 + "\n暂无相关祭典信息\n\n"

            # 过去的祭典（只显示最近3个）
            if past_festivals:
                result += "📜 最近的祭典\n" + "-" * 20 + "\n\n"
                result += self._format_festivals(past_festivals[:3], "")  # 只显示最近3个
            else:
                result += "📜 最近的祭典\n" + "-" * 20 + "\n暂无相关祭典信息\n\n"

            yield event.plain_result(result.strip())

        except Exception as e:
            logger.error(f"[Splatoon3] 获取祭典信息失败: {str(e)}")
            yield event.plain_result("❌ 获取祭典信息失败，请稍后重试")
