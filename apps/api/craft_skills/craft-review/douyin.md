# 抖音（channel: douyin）

后台：抖音创作者中心 https://creator.douyin.com/creator-micro/content/manage （内容管理）。

1. 打开内容管理页。没登录会出扫码：停下请用户登录。右上角头像 / 账号名核对是哪个账号。
2. 在这个页面里请求页面自己用的作品列表接口（ego-browser `page.fetch`，带登录态）：
   `/janus/douyin/creator/pc/work_list?status=0&count=20&max_cursor=<游标>&scene=star_atlas&device_platform=android&aid=1128`
   第一页 `max_cursor=0`；返回 `has_more` 为 true 时用返回的 `max_cursor` 读下一页。
   **作品编号是 19 位长数字，超出 JavaScript 数字精度**：不要在浏览器脚本里 `JSON.parse` 后再取 `id`（末几位会变成 000）。把接口原文存成文件，用 Python 解析；或解析前先把 `"id":数字` 改成字符串。
3. 用返回里的 `items[]`（每条作品一项）：
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `id` |
   | title | `description` 前 100 字（是「标题 + 正文」） |
   | published_at | `create_time`（秒级时间戳）换成中国时间 `YYYY-MM-DD HH:MM:SS` |
   | url | `https://www.douyin.com/video/<id>` |
   | plays | `metrics.view_count` |
   | completion_rate | `metrics.completion_rate` |
   | completion_rate_5s | `metrics.completion_rate_5s` |
   | cover_ctr | `metrics.cover_click_rate`；没有这个字段或 `metrics.cover_show` 为 0 时不填（平台还没统计） |
   | bounce_rate_2s | `metrics.bounce_rate_2s` |
   | avg_play_seconds | `metrics.avg_view_second` |
   | avg_play_ratio | `metrics.avg_view_proportion` |
   | likes / comments / shares / favorites | `like_count` / `comment_count` / `share_count` / `favorite_count` |
   | profile_visits | `metrics.homepage_visit_count` |
   | followers_gained | `metrics.subscribe_count`（页面上的「吸粉量」） |
   接口里数字是字符串，转成数字；比率已经是 0–1 小数，不用再除 100。
4. 视频看 `video_info.duration` 有值（毫秒）；没有的是图文（2026-11-12 实测 `type` 为 1）。图文的完播率、跳出率等字段含义和视频不同（页面显示的是划走率、文案展开率，对不上），**图文只填次数类**：plays、likes、comments、shares、favorites、profile_visits、followers_gained。
5. 字段不一定每条都有，缺的项不填。
