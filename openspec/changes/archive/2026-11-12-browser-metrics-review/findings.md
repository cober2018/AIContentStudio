## 2026-11-12 浏览器试跑（ego lite，只读）
- 抖音：`/janus/douyin/creator/pc/work_list?status=0&count=20&max_cursor=0&scene=star_atlas&device_platform=android&aid=1128`，用 page.fetch 在创作者中心页里请求。`items[].metrics` 有 view_count、completion_rate、completion_rate_5s、cover_click_rate、bounce_rate_2s、avg_view_second、avg_view_proportion、like/comment/share/favorite_count、homepage_visit_count、subscribe_count（=页面「吸粉量」）；`items[].id` 是作品编号，`create_time` 是秒级时间戳；`description` 是「标题 + 正文」，不是我们的标题。
- 小红书：`/api/galaxy/v2/creator/note/user/posted?tab=0&page=0` 要签名，page.fetch 返回 406；开 Network、重载笔记管理页、用 getResponseBody 取页面自己的响应可行。字段：id、display_title、time（本地时间字符串）、view_count、likes、comments_count、collected_count、shared_count。登录的是「coober」。
- 公众号：`/cgi-bin/appmsgpublish?sub=list&begin=0&count=10&type=101_1&token=<页面URL里的token>&f=json&ajax=1`，publish_page 是 JSON 字符串，publish_list[].publish_info 再解一层，appmsgex[] 有 title、read_num、like_num、old_like_num、share_num、comment_num、reprint_num。like_num / old_like_num 哪个是「点赞」哪个是「在看」要对照页面再确认。
- 视频号助手：未登录，需微信扫码，没试。
- 作品 97 的发布记录（公众号 #8、百家号 #9、抖音 #10、小红书 #11）都没有发布时间和链接，小红书 #11 没挂账号；按现在「账号+标题+时间」认作品会建重复记录。

## 2026-11-12 实跑
- 来源类型 `platform_page` 被数据库检查拦下（500），加迁移 acctdata0002 放开；schema head 改为 acctdata0002。
- 抖音作品编号 19 位，在浏览器脚本里 JSON.parse 后末几位变 000：接口原文要原样存下，用 Python 解析。已写进 craft-review。
- 抖音图文（无 `video_info.duration`，type 1）的完播率等字段和页面「划走率」对不上，只导次数类。
- 抖音 `cover_click_rate` 不是每条都有，`cover_show` 为 0 时也不导。
- 公众号列名核对：阅读、点赞人数、分享人数、推荐人数、留言条数、划线人数；`old_like_num` 是点赞，`like_num` 是推荐。视频发到公众号时阅读数旁分开显示公众号播放 / 视频号播放，`read_num` 只算公众号。
- 公众号上「K线差2%」标题去了标点，靠回执里的链接对上；所以 `list_published_works` 的 url 也取回执上的链接。
- 百家号公开链接 `https://baijiahao.baidu.com/s?id=<作品编号>`（视频会跳好看视频）；作品编号在作品管理标题链接里。
- 小红书 coober = 账号 14（量化研究专家），用户确认。
- 撤销批次只删数据和新建的外部作品；对上的自有发布记录补上的发布时间、链接、作品编号不会撤回。
