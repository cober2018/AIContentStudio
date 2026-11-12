# craft-publish：把发布包发到平台

用户在自己已登录的浏览器（ego lite，按 ego-browser skill 操作）里，把平台做好的发布包（成片、封面、发布文案）上传到各平台后台。**按用户说的做**：说「发布」就点发表并记回执；说「存草稿」就只存草稿、不发表。默认由 Codex Desktop 执行，Claude Code 备用。

## 流程
1. `list_publish_targets` 看哪些交付目标在等发布；用户点名的作品和平台为准。`links_missing` 是已发表但回执还没有作品链接的目标：顺手按下面「作品链接」取到链接，用 `report_publish_link(target_id, link)` 补上。
2. `get_publish_package(target_id)` 取发布包：`files`（按 role 的本机绝对路径，只读）、`publish_copy`（title、description、hashtags、cover_text、interaction）、`skill_entry`（这个平台的说明文件）。`draft` 有值说明之前传过草稿：发布时先去草稿箱打开那条草稿接着发，不另传一份；只存草稿时先问用户要不要再传，免得平台上出现两份草稿。
3. 读这个平台那一份说明：`get_craft_skill(skill="craft-publish", entry=<skill_entry>)`。没有这份说明的平台，先告诉用户「这个平台还没写说明」，经用户同意再按页面摸索，并把实际步骤记在 note 里。
4. 在 ego lite 里打开平台后台，上传文件（`setInputFiles` 传绝对路径）、填文案，然后点「发表」（只存草稿时点「保存草稿」）。
5. 截图：发表后到平台的作品列表，等这条显示出来（审核中也算）整页截图；只存草稿时到草稿箱截图。存到发布包给的 `screenshot_dir`（项目的 `导出/发布截图/`，不存在就先建），文件名 `<channel>-<target_id>.png`；`screenshot_dir` 为空时存系统临时目录。
6. 取作品链接（见下面「作品链接」），回执要的是作品的公开链接，不是后台管理页的地址。
7. 记录：
   - 发表了：`report_publish_result(target_id, screenshot_path, link, note, model)`。平台按这条记回执，交付目标变成已发布。审核中、定时发布等还拿不到链接时 `link` 先留空，等平台出了链接再用 `report_publish_link` 补；补完交付页显示链接，效果复盘也能对上这条作品。
   - 只存草稿：`report_publish_draft(target_id, screenshot_path, note, model)`，然后**停下**，告诉用户草稿已存好。

## 红线
- 只发 `list_publish_targets` 里有的目标（用户在交付页授权过的）；用户只说存草稿时，不点「发表 / 发布 / 提交审核」。
- 不用「定时发布」；不改账号资料和设置。
- 点发表前核对：账号对（和交付目标的 account 对得上）、视频和封面是这个作品的、文案是 `publish_copy` 的。有一项对不上就停下问用户。
- 遇到登录、扫码、验证码、短信、实名、风控提示：停下，请用户处理后再继续。
- 发布包文件只读：不复制、不另存、不压缩、不改。
- 文案照 `publish_copy` 填；平台字数不够时只截短，不改意思、不加没有的卖点；话题用 `hashtags`，不另编。
- 位置、合集、挂商品、原创声明、可见范围这类选项：保持平台默认，不替用户选；note 里写明哪些留给用户。
- 正常节奏操作，一次只传一个目标，不连发。

## 作品链接
发表后到平台的作品列表找到这条，按平台取链接：
| 平台 | 链接 |
|---|---|
| 抖音 | `https://www.douyin.com/video/<作品编号>`；作品编号在创作者中心作品列表接口的 `id`（见 craft-review 的 douyin.md） |
| 小红书 | `https://www.xiaohongshu.com/explore/<笔记编号>`；笔记编号见 craft-review 的 xiaohongshu.md |
| 公众号 | 发表记录里这篇的 `content_url`（`https://mp.weixin.qq.com/s/...`），见 craft-review 的 wechat.md |
| 百家号 | `https://baijiahao.baidu.com/s?id=<作品编号>`；作品编号在作品管理列表标题链接 `builder/preview/s?id=` 后面（视频打开会跳到好看视频，正常） |
| 视频号 | 网页上没有公开链接，`link` 留空，截图当依据 |
| 其他平台 | 作品页「分享 / 复制链接」给的公开链接；拿不到就留空，在 note 里写明 |

## 封面怎么选
- 竖版作品（9:16）：用 role `cover`（1080×1920）。
- 横版作品（16:9）：发布包里三张封面都有。平台要竖封面用 `cover_vertical`（3:4）；要 4:3 横封面用 `cover_43`；要 16:9 横封面或比例不限用 `cover`。
- 平台不让自定义封面就保留默认，在 note 里说明。

## 平台说明
| 平台 | channel | 说明文件 |
|---|---|---|
| 视频号 | wechat_channels | wechat_channels.md |

说明是按页面写的；页面和说明对不上时以页面为准，把差异写进 note，回头更新说明。
