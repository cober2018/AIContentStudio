# 公众号（channel: wechat）

后台：https://mp.weixin.qq.com （登录后地址栏里有一个 token 参数，值是一串数字）。

1. 打开公众号后台首页。没登录会出扫码：停下请用户登录。左上角公众号名称核对是哪个账号（`list_accounts` 里有多个公众号）。
2. 在后台页面里请求发表记录接口（`page.fetch`；下面的地址末尾都要再接上当前页面地址里的 token 参数，原样照抄，不写进汇报）：
   `/cgi-bin/appmsgpublish?sub=list&begin=<偏移>&count=10&query=&type=101_1&lang=zh_CN&f=json&ajax=1`
   `begin` 从 0 开始，每页 10 次发表。
3. 解析：返回的 `publish_page` 是 JSON 字符串，解开后 `publish_list[]` 每项的 `publish_info` 还要再解一层。每次发表里的文章在 `appmsg_info[]`（旧的群发也可能在 `appmsgex[]`），一次发表可能有多篇。
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `<appmsgid>_<itemidx>` |
   | title | `title` |
   | published_at | 群发（`type` 9）：`sent_info.time`；新「发表」（`type` 10002）：解开后的 `publish_info` 里还有一层 `publish_info`，取它的 `create_time`（2026-11-19 实测外层没有 create_time）；都是秒级时间戳，换成中国时间 |
   | url | `content_url` |
   | content_form | `item_show_type` 为 5 是视频、8 是贴图，其他按文章 |
   | reads | `read_num` |
   | shares | `share_num` |
   | comments | `comment_num` |
   | reposts | `reprint_num`（有才填） |
   | likes（点赞人数） | `old_like_num` |
   | recommends（推荐人数） | `like_num` |
4. `is_deleted` 为 true 的文章跳过。
5. 2026-11-12 对照「全部发表记录」页核对过：列依次是阅读、点赞人数、分享人数、推荐人数、留言条数、划线人数；`old_like_num` 是点赞、`like_num` 是推荐。页面对不上时以页面为准，两项都标进 `uncertain`。
6. 视频（`item_show_type` 5）发到公众号时，页面上的阅读数旁边会分开显示「公众号播放 / 视频号播放」；`read_num` 只是公众号这边的，视频号那边的数据属于视频号账号。
7. 单篇详情（发表后 30 天内的文章才有，页面写「本页面仅统计发表后30天内的数据」）：对近 30 天内发表的每篇，`page.fetch` 请求
   `/misc/appmsganalysis?action=detailpage&msgid=<appmsgid>_<itemidx>&publish_date=<发表日期 YYYY-MM-DD>&type=int&pageVersion=1&lang=zh_CN`（同样接上 token 参数）
   返回的是网页；在原文里找 `articleData:` 后面那段 JSON（到行尾的 `},` 为止），解出来用 `article_data_new`：
   | 导入字段 | 取值 |
   |---|---|
   | favorites（收藏人数） | `collection_uv` |
   | followers_gained（新增关注） | `follow_after_read_uv` |
   | avg_read_seconds（平均阅读时长） | `avg_article_read_time`（秒；页面上换算成分钟显示） |
   | read_completion_rate（完读率） | `finished_read_pv_ratio`（0–1 小数）；贴图（`item_show_type` 8）页面不显示完读率，不填 |
   一篇一次请求，正常节奏。详情页或「内容分析」返回系统错误（2026-11-19 实测整个下午都报错）时，不重试、不改用别的页面估算：这些文章只导第 3 步的列表数据，详情项不填（平台保留上次的详情值和日期，不会清零），汇报里写明哪些文章的详情没更新。详情里的点赞、推荐、留言、分享和列表重复，以列表为准。超过 30 天的文章只填第 3 步的列表数据。
