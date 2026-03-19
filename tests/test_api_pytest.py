"""API测试（使用pytest框架）"""
import pytest
from splatoon3_client import Splatoon3Client


@pytest.mark.asyncio
async def test_api_connection():
    """测试API连接"""
    client = Splatoon3Client(language="zh-CN", debug=False)
    
    try:
        # 测试获取当前地图
        current_stages = await client.get_current_stages()
        assert current_stages is not None
        assert isinstance(current_stages, dict)
        assert "regular" in current_stages
        
        # 测试获取鲑鱼跑
        salmon_run = await client.get_salmon_run()
        assert isinstance(salmon_run, list)
        
        # 测试获取挑战活动
        challenges = await client.get_challenges()
        assert isinstance(challenges, list)
        
        # 测试获取装备
        gear = await client.get_splatnet_gear()
        assert isinstance(gear, list)
        
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_locale_translation():
    """测试语言翻译"""
    client = Splatoon3Client(language="zh-CN", debug=False)
    
    try:
        # 测试获取本地化数据
        locale = await client._get_locale()
        assert isinstance(locale, dict)
        assert "stages" in locale
        assert "weapons" in locale
        
    finally:
        await client.close()
