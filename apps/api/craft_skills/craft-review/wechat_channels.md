# 视频号（channel: wechat_channels）

后台：视频号助手 https://channels.weixin.qq.com/platform 。

1. 打开视频号助手。没登录会出扫码：停下请用户登录。左下角显示视频号名称，核对是哪个账号。**2026-11-19 实测：「知数Talk」的视频号在助手里叫「孟不知」**（`list_accounts` 里 id 15 的视频号账号）；名称对不上又没有这条记录时问用户。
2. 作品列表：打开 https://channels.weixin.qq.com/platform/post/list ，用 `page.cdp("Network.enable")` 截获 url 含 `/post/post_list` 的响应原文（`Network.getResponseBody`）；`data.continueFlag` 为真时滚动到底，页面会再请求下一页，同样截获。用 `data.list[]`：
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `objectId`（含 `/`，原样填） |
   | title | `desc.description` 前 100 字（视频号没有单独标题，是描述正文） |
   | published_at | `createTime`（秒级时间戳）换成中国时间 |
   | url | 不填（后台列表里没有作品链接；我们发布的记录里存的是 `https://weixin.qq.com/sph/…` 短链，和 `objectId` 对不上，按正文开头和发布日期认） |
   | plays（播放） | `readCount` |
   | completion_rate（完播率） | `fullPlayRate`（已是 0–1 小数） |
   | avg_play_seconds（平均播放时长） | `avgPlayTimeSec` |
   | likes（点赞，👍） | `favCount` |
   | recommends（推荐，♡） | `likeCount` |
   | comments | `commentCount` |
   | shares（分享） | `forwardCount` |
   | followers_gained（关注） | `followCount` |
3. **点赞和推荐的字段名是反的**：2026-11-19 对照「数据中心 · 视频数据 · 单篇视频」核对过，`likeCount` 是 ♡（推荐），`favCount` 是 👍（点赞）。页面对不上时以页面为准，两项都标进 `uncertain`。
4. `status` 为 1 是正常发表（2026-11-19 实测全部为 1）；其他值（已删除、审核中等）跳过，并写进汇报。很早以前发的私人视频（和账号内容无关的）照常导入为外部作品，不用挑。
5. 同一条视频同时发到公众号时，公众号发表记录里的 `finder_stat_info` 也是这条视频号的数据，以这里为准，不要从公众号那边重复导。
