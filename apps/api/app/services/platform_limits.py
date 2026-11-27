"""平台差异只留机械限制：标题字数、话题个数、简介长度、封面尺寸，集中登记在这一张表里。

每个形态作品只有一份发布文案；发往某个平台超限时只提示改哪一项，不另写一版。
数字按各平台发布页的填写限制登记（2026-11 核对时以页面提示为准）；平台改了限制，只改这张表。
"""

from __future__ import annotations

# title / hashtags / description: 最多几个字或几个；cover: 封面尺寸要求。None 表示该平台没有这一项或不限。
LIMITS: dict[str, dict] = {
    "douyin": {"name": "抖音", "title": 30, "hashtags": 5, "description": 1000, "cover": "竖版 1080×1920；横版另交 4:3（1440×1080）"},
    "xiaohongshu": {"name": "小红书", "title": 20, "hashtags": 10, "description": 1000, "cover": "3:4（1080×1440）"},
    "wechat_channels": {"name": "视频号", "title": 16, "hashtags": 10, "description": 1000, "cover": "3:4（1080×1440）",
                        "title_field": "短标题"},
    "bilibili": {"name": "B站", "title": 80, "hashtags": 10, "description": 2000, "cover": "16:9（1920×1080）"},
    "youtube": {"name": "YouTube", "title": 100, "hashtags": 15, "description": 5000, "cover": "16:9（1280×720 起）"},
    "kuaishou": {"name": "快手", "title": 30, "hashtags": 5, "description": 500, "cover": "竖版 1080×1920"},
    "toutiao": {"name": "今日头条", "title": 30, "hashtags": 5, "description": 400, "cover": "16:9 或 3:2"},
    "baijia": {"name": "百家号", "title": 30, "hashtags": 5, "description": 400, "cover": "16:9"},
    "wechat": {"name": "公众号", "title": 64, "hashtags": None, "description": 120, "cover": "2.35:1（900×383）",
               "image_message_title": 32},
}
NAMES = {"title": "标题", "hashtags": "话题", "description": "简介"}


def limit(channel: str, field: str) -> int | None:
    return (LIMITS.get(channel) or {}).get(field)


def check(channel: str, copy: dict | None) -> list[dict]:
    """Which fields of one copy go over this platform's limits; empty when it fits or the platform is not registered."""
    row = LIMITS.get(channel)
    if not row or not copy:
        return []
    found = []
    for field in ("title", "description"):
        cap, value = row.get(field), str(copy.get(field) or "")
        if cap and len(value) > cap:
            name = row.get(f"{field}_field") or NAMES[field]
            found.append({"channel": channel, "platform": row["name"], "field": field, "limit": cap, "actual": len(value),
                          "message": f"{row['name']}{name}最多 {cap} 字，现在 {len(value)} 字：发布时截短，或改这份文案的{NAMES[field]}"})
    tags = copy.get("hashtags") or []
    if row.get("hashtags") and len(tags) > row["hashtags"]:
        found.append({"channel": channel, "platform": row["name"], "field": "hashtags", "limit": row["hashtags"], "actual": len(tags),
                      "message": f"{row['name']}话题最多 {row['hashtags']} 个，现在 {len(tags)} 个：发布时只带前 {row['hashtags']} 个"})
    return found


def check_all(channels: list[str], copy: dict | None) -> list[dict]:
    return [item for channel in channels for item in check(channel, copy)]


def table() -> list[dict]:
    return [{"channel": key, **value} for key, value in LIMITS.items()]
