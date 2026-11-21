# 小红书（channel: xiaohongshu）

后台：小红书创作服务平台。读两处：「数据看板 · 内容分析」的笔记列表（大部分数据），每条视频笔记的「分析详情」（完播率、5s 完播率、2 秒退出率）。

1. 打开 https://creator.xiaohongshu.com/statistics/data-analysis 。没登录会出扫码：停下请用户登录。左上角账号名核对是哪个账号（同平台有多个账号时问用户对应哪个；`list_accounts` 里的名字和后台不同时，按用户说的对应）。
2. 小红书接口要签名，直接 `page.fetch` 会被拒（406）。一律截获页面自己收到的数据：
   - `page.cdp("Network.enable", {})`，`page.events()` 清掉旧事件，`page.reload()`，等几秒；
   - 在 `page.events()` 里找 `Network.responseReceived` 且 url 含目标路径的那条，用 `page.cdp("Network.getResponseBody", { requestId })` 取原文；
   - 读完 `page.cdp("Network.disable", {})`。
3. 笔记列表：url 含 `/datacenter/note/analyze/list`。页面默认只筛最近一个月发布的笔记，会漏掉更早的：截获前先在列表上方的发布时间筛选里把范围拉到最长（近半年，后台最多只给半年），等列表刷新后再截获。超过 10 条时点页面底部翻页，每页再截获一次。汇报里写明用的时间范围和总条数。用 `data.note_infos[]`：
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `id` |
   | title | `title` |
   | published_at | `post_time`（毫秒时间戳）换成中国时间 |
   | url | `https://www.xiaohongshu.com/explore/<id>` |
   | content_form | `type` 为 2 是视频、1 是图文（2026-11-19 实测） |
   | impressions | `imp_count` |
   | views | `read_count` |
   | cover_ctr | `coverClickRate`（已是 0–1 小数） |
   | avg_play_seconds | `view_time_avg`（秒，视频才有） |
   | likes / comments / favorites / shares | `like_count` / `comment_count` / `fav_count` / `share_count` |
   | followers_gained | `increase_fans_count` |
   | danmaku | `danmaku_count` |
   刚发的笔记很多项还没统计（字段不存在），缺的不填，不要写 0。
4. 视频笔记的详情：逐条打开 `https://creator.xiaohongshu.com/statistics/note-detail?noteId=<id>`（正常节奏，一条一条来），截获 url 含 `/datacenter/note/base?note_id=` 的那条，用 `data`：
   | 导入字段 | 取值 |
   |---|---|
   | completion_rate | `full_view_rate` ÷ 100（接口给的是百分数，1.9 表示 1.9%） |
   | completion_rate_5s | `finish5s_rate` ÷ 100 |
   | bounce_rate_2s | `exit_view2s_rate` ÷ 100 |
   | avg_play_seconds | `view_time_avg_with_double`（带一位小数，比列表的整数准，有就用它） |
   某项为 -1 表示平台还没统计（刚发的笔记），不填。详情数据按天更新（`data_last_update_time`），比列表的次数慢一天，次数类以第 3 步列表为准。图文笔记不读详情。
5. 旧的「笔记管理」页（`/new/note-manager`，接口 `/note/user/posted`）只有观看、点赞、评论、收藏、分享五项，只在内容分析读不到（例如半年前的笔记）时用：`view_count` / `likes` / `comments_count` / `collected_count` / `shared_count`。
