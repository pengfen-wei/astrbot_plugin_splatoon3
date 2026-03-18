# Splatoon3 查询插件

基于 [splatoon3.ink](https://splatoon3.ink/) API 的 AstrBot 插件，实现了 [splatoon3api](https://github.com/KartoffelChipss/splatoon3api) npm 包的所有功能。

## 功能特性

- 🗺️ **地图轮换查询** - 查询当前、下一时段及所有地图轮换
- 🐟 **鲑鱼跑日程** - 查询鲑鱼跑时间表和武器配置
- ⚔️ **挑战活动** - 查询游戏内挑战活动信息
- 🛍️ **装备商店** - 查询 Splatnet 商店装备
- 🎉 **祭典信息** - 查询进行中、即将开始和过去的祭典
- 🌐 **多语言支持** - 支持14种语言切换
- 💾 **用户配置持久化** - 每个用户可独立设置语言偏好
- ⚡ **缓存机制** - API响应缓存，减少重复请求

## 安装

1. 将 `astrbot_plugin_splatoon3_new` 文件夹复制到 AstrBot 的 `data/plugins/` 目录
2. 在 AstrBot WebUI 的插件管理处启用该插件
3. 插件会自动安装依赖（aiohttp）

## 命令列表

### 基础命令

| 命令 | 说明 |
|------|------|
| `/splat3帮助` | 显示插件帮助信息 |

### 地图查询

| 命令 | 说明 |
|------|------|
| `/splat3当前` | 查询当前地图轮换 |
| `/splat3下一` | 查询下一时段地图轮换 |
| `/splat3全部` | 查询所有地图轮换（默认显示涂地模式） |

### 鲑鱼跑

| 命令 | 说明 |
|------|------|
| `/splat3鲑鱼` | 查询鲑鱼跑日程 |

### 挑战活动

| 命令 | 说明 |
|------|------|
| `/splat3挑战` | 查询挑战活动 |

### 装备商店

| 命令 | 说明 |
|------|------|
| `/splat3装备` | 查询 Splatnet 装备商店 |

### 祭典信息

| 命令 | 说明 |
|------|------|
| `/splat3祭典进行` | 查询正在进行的祭典 |
| `/splat3祭典即将` | 查询即将开始的祭典 |
| `/splat3祭典过去` | 查询过去的祭典 |

### 语言设置

| 命令 | 说明 |
|------|------|
| `/splat3语言` | 查看当前语言和支持的语言列表 |
| `/splat3语言 <语言代码>` | 切换语言 |

## 支持的语言

| 语言代码 | 语言名称 |
|----------|----------|
| `zh-CN` | 中文(简体) |
| `zh-TW` | 中文(台灣) |
| `en-US` | English (US) |
| `en-GB` | English (GB) |
| `ja-JP` | 日本語 |
| `ko-KR` | 한국어 |
| `de-DE` | Deutsch |
| `fr-FR` | Français (FR) |
| `fr-CA` | Français (CA) |
| `es-ES` | Español (ES) |
| `es-MX` | Español (MX) |
| `it-IT` | Italiano |
| `ru-RU` | Русский |
| `nl-NL` | Nederlands |

## 祭典区域说明

祭典分为四个区域：

| 区域代码 | 覆盖范围 |
|----------|----------|
| `US` | 美洲、澳洲、新西兰 |
| `EU` | 欧洲 |
| `JP` | 日本 |
| `AP` | 香港、韩国（亚太） |

## 使用示例

```
/splat3帮助
/splat3当前
/splat3下一
/splat3全部
/splat3鲑鱼
/splat3挑战
/splat3装备
/splat3祭典进行
/splat3祭典即将
/splat3祭典过去
/splat3语言
/splat3语言 ja-JP
```

## 插件结构

```
astrbot_plugin_splatoon3_new/
├── __init__.py          # 包初始化
├── main.py              # 插件主文件（命令接口）
├── splatoon3_client.py  # API客户端封装
├── metadata.yaml        # 插件元数据
├── requirements.txt     # 依赖列表
└── README.md           # 本文档
```

## 数据来源

本插件使用 [splatoon3.ink](https://splatoon3.ink/) 提供的公开 API，所有数据均来自该服务。

## 开发说明

### 依赖

- `aiohttp` >= 3.8.0 - 异步HTTP请求库

### 配置文件

用户配置存储在 `data/splatoon3_plugin/user_configs.json`，包含：

```json
{
  "平台_用户ID": {
    "language": "zh-CN"
  }
}
```

### API 客户端

`Splatoon3Client` 类封装了所有 API 调用，支持：

- 缓存机制（默认60秒TTL）
- 自动语言翻译
- 异步请求
- 错误处理

## 许可证

本项目基于 [splatoon3api](https://github.com/KartoffelChipss/splatoon3api)，采用 **MIT 许可证** 开源。

```
MIT License

Copyright (c) 2026 AstrBot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 致谢

- [splatoon3.ink](https://splatoon3.ink/) - 提供游戏数据API
- [splatoon3api](https://github.com/KartoffelChipss/splatoon3api) - 参考的npm包实现
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 优秀的机器人框架

## 反馈与支持

如有问题或建议，欢迎反馈！
