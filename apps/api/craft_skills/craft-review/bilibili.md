# B站（channel: bilibili）

后台：B站创作中心 https://member.bilibili.com/platform/home 。

1. 打开创作中心。没登录会出扫码：停下请用户登录。右上角头像 / 空间名核对是哪个账号。
2. 在创作中心页面里 `page.fetch` 两个接口（带登录态，不用签名）：
   - 稿件列表：`https://member.bilibili.com/x/web/archives?status=is_pubing%2Cpubed%2Cnot_pubed&pn=<页>&ps=10&coop=1&interactive=1`，用 `data.arc_audits[]`，`pn` 从 1 开始，`data.page.count` 是总数；
   - 稿件对比（「数据中心 · 稿件分析 · 稿件对比」用的数据）：`https://member.bilibili.com/x/web/data/archive_diagnose/compare?size=50`，用 `data.list[]`，按 `bvid` 和稿件列表对上。
3. 字段：
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `Archive.bvid` |
   | title | `Archive.title` |
   | published_at | `Archive.ptime`（秒级时间戳）换成中国时间 |
   | url | `https://www.bilibili.com/video/<bvid>` |
   | views / likes / comments / favorites / coins / shares / danmaku | 稿件列表 `stat.view` / `stat.like` / `stat.reply` / `stat.favorite` / `stat.coin` / `stat.share` / `stat.danmaku` |
   | avg_play_ratio（平均播放进度） | 对比 `stat.full_play_ratio` ÷ 10000（5787 = 57.9%） |
   | cover_ctr（封标点击率） | 对比 `stat.tm_rate` ÷ 10000 |
   | bounce_rate_3s（3秒跳出率） | 对比 `stat.crash_rate` ÷ 10000 |
   | followers_gained（涨粉） | 对比 `stat.total_new_attention_cnt` |
   | unfollows（取关） | 对比 `stat.unfollow` |
4. 对比接口的 `stat.not_ready_field` 列出还没统计出来的项（刚发的稿件常见），列在里面的不填。`avg_play_time` 2026-11-19 实测全是 0，页面也不显示，不填。
5. 读哪些稿件：`Archive.state` 为 0（`state_desc`「开放浏览」），以及 `Archive.is_only_self` 为 1 的「仅自己可见」稿件（这类稿件的 `state` 不是 0，2026-11-19 实测是 -50，照常读，汇报里标出来）。其他稿件（审核中、退回等）跳过。
6. 2026-11-19 对照「稿件对比」页核对过：`full_play_ratio` 对应的列是「平均播放进度」，不是完播率；`play_viewer_rate` 是「游客播放占比」，不导。
