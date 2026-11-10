# craft-publish：把发布包上传成平台草稿

用户在自己已登录的浏览器（ego lite，按 ego-browser skill 操作）里，把平台做好的发布包（成片、封面、发布文案）上传到各平台后台，**只存成草稿 / 待发布**。发表和回填链接都由用户来。默认由 Codex Desktop 执行，Claude Code 备用。

## 流程
1. `list_publish_targets` 看哪些交付目标在等发布；用户点名的作品和平台为准。
2. `get_publish_package(target_id)` 取发布包：`files`（按 role 的本机绝对路径，只读）、`publish_copy`（title、description、hashtags、cover_text、interaction）、`skill_entry`（这个平台的说明文件）。`draft` 有值说明之前传过草稿：先问用户要不要再传，免得平台上出现两份草稿。
3. 读这个平台那一份说明：`get_craft_skill(skill="craft-publish", entry=<skill_entry>)`。没有这份说明的平台，先告诉用户「这个平台还没写说明」，经用户同意再按页面摸索，并把实际步骤记在 note 里。
4. 在 ego lite 里打开平台后台，上传文件（`setInputFiles` 传绝对路径）、填文案、存草稿。
5. 草稿存好后整页截图，存到发布包给的 `screenshot_dir`（项目的 `导出/发布截图/`，不存在就先建），文件名 `<channel>-<target_id>.png`；`screenshot_dir` 为空时存系统临时目录。
6. `report_publish_draft(target_id, screenshot_path, note, model)` 记一笔，然后**停下**，告诉用户：去平台后台检查草稿、自己点发表，发表后在交付页回填链接。

## 红线
- 不点「发表 / 发布 / 提交审核 / 定时发布」以及任何会让内容对外可见的按钮；不改账号资料和设置。
- 遇到登录、扫码、验证码、短信、实名、风控提示：停下，请用户处理后再继续。
- 发布包文件只读：不复制、不另存、不压缩、不改。
- 文案照 `publish_copy` 填；平台字数不够时只截短，不改意思、不加没有的卖点；话题用 `hashtags`，不另编。
- 位置、合集、挂商品、原创声明、可见范围这类选项：保持平台默认，不替用户选；note 里写明哪些留给用户。
- 正常节奏操作，一次只传一个目标，不连发。

## 封面怎么选
- 竖版作品（9:16）：用 role `cover`（1080×1920）。
- 横版作品（16:9）：平台要竖封面用 `cover_vertical`（3:4）；要横封面用 `cover`（16:9）；只收 4:3 的用 `cover_43`。
- 平台不让自定义封面就保留默认，在 note 里说明。

## 平台说明
| 平台 | channel | 说明文件 |
|---|---|---|
| 视频号 | wechat_channels | wechat_channels.md |

说明是按页面写的；页面和说明对不上时以页面为准，把差异写进 note，回头更新说明。
