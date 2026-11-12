# 小红书（channel: xiaohongshu）

后台：小红书创作服务平台 https://creator.xiaohongshu.com/new/note-manager （笔记管理）。

1. 打开笔记管理页。没登录会出扫码：停下请用户登录。左上角账号名核对是哪个账号（同平台有多个账号时问用户对应哪个）。
2. 笔记列表接口 `/api/galaxy/v2/creator/note/user/posted?tab=0&page=<页>` 要签名，直接 `page.fetch` 会被拒（406）。改为截获页面自己收到的数据：
   - `page.cdp("Network.enable", {})`，`page.events()` 清掉旧事件，`page.reload()`，等几秒；
   - 在 `page.events()` 里找 `Network.responseReceived` 且 url 含 `/note/user/posted` 的那条，用 `page.cdp("Network.getResponseBody", { requestId })` 取原文；
   - 要下一页：滚动笔记列表到底，页面会再请求一页，同样截获；
   - 读完 `page.cdp("Network.disable", {})`。
3. 用返回里的 `data.notes[]`：
   | 导入字段 | 取值 |
   |---|---|
   | platform_item_id | `id` |
   | title | `display_title` |
   | published_at | `time`（已是中国时间 `YYYY-MM-DD HH:MM`） |
   | url | `https://www.xiaohongshu.com/explore/<id>` |
   | content_form | `type`（video / normal） |
   | views | `view_count` |
   | likes | `likes` |
   | comments | `comments_count` |
   | favorites | `collected_count` |
   | shares | `shared_count` |
