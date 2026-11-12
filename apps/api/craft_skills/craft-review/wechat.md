# 公众号（channel: wechat）

后台：https://mp.weixin.qq.com （登录后地址栏带 `token=数字`）。

1. 打开公众号后台首页。没登录会出扫码：停下请用户登录。左上角公众号名称核对是哪个账号（`list_accounts` 里有多个公众号）。
2. 在后台页面里请求发表记录接口（`page.fetch`，`<token>` 取当前页面地址里的 token）：
   `/cgi-bin/appmsgpublish?sub=list&begin=<偏移>&count=10&query=&type=101_1&token=<token>&lang=zh_CN&f=json&ajax=1`
   `begin` 从 0 开始，每页 10 次发表。
3. 解析：返回的 `publish_page` 是 JSON 字符串，解开后 `publish_list[]` 每项的 `publish_info` 还要再解一层。每次发表里的文章在 `appmsg_info[]`（旧的群发也可能在 `appmsgex[]`），一次发表可能有多篇。
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `<appmsgid>_<itemidx>` |
   | title | `title` |
   | published_at | 新发表：外层 `publish_info.create_time`；群发：`sent_info.time`（秒级时间戳，换成中国时间） |
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
