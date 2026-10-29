# 设计

## 1. 品类像角色

| 项 | 做法 |
|---|---|
| 存哪 | 新表 `ProductCategory` + `ProductCategoryRevision`（`profile_json` 带版本），对照 `ContentPersona` / `ContentPersonaRevision` |
| 内置 | 美妆护肤、食品零食、家居日用、服饰鞋包、数码 3C；首次启动写入，用户可改、可新增、可停用 |
| profile 字段 | `directive`（看什么、卖点怎么写、违禁词、常见人群、语气）、`styles`（可用风格 skill 列表 + 默认）、`hooks`（推荐开头）、`look`（默认 Look）、`camera_plan`（镜头类型 → 运镜）、`production_stages`（各阶段 skill 组合，结构同角色） |
| 解析 | `creative_configuration.resolve` 增加品类层：全局商品默认 → 品类 → SKU 方案 → 本次发起；后者覆盖前者，冻结进作品快照 |
| SKU | `product_json.category_id` 选品类；原 `category` 文字保留为「细分」；老数据按名称匹配内置品类，匹配不上的归「其他」并提示补选 |
| 商品表现风格 | 保留，作为品类之上的附加风格，不再用 `categories[]` 白名单拦截 |
| 页面 | 设置 → 商品品类：列表 + 编辑（复用角色创作配置的阶段 skill 组件）；商品资料页选品类 |

## 2. 风格 skill

- 10 个包：`studio.product.style.{drama,reversal,interview,story,unboxing,product-pov,comparison,talking-head,pain-point,scene}` v1，每个写：结构与情绪节奏、适合 / 不适合的品类、镜头类型序列、边界（演绎不冒充真实用户，不编造销量、测评数据、亲测经历）。
- `studio.video.product-script` v3：输入多了品类 directive、所选风格、固定开头 / 开头版本数；输出多 `style`、`hooks[]`（版本）、剧情类的 `characters[]`。没选风格时在品类可用风格里挑并写理由。
- 品类脚本套路和镜头结构写进各品类 directive 和 `product-shots` v3 参考，替换 v2 的 `categories.md`。

## 3. 开头与发布文案

- 发起页加「开头」：自动 / 指定一种（16 种名称，来自 `hooks.md`）/ 版本数 1–3。
- `studio.product.publish-copy` v1：按渠道出标题（≤15 字）、话题 3–5 个、封面字（≤8 字）、互动引导、简介（≤50 字）；挂在合规检查之前，结果随作品保存，可编辑。
- 「参考爆款结构」：发起页可贴一段结构描述，脚本按结构写，不抄原文。

## 4. 运镜、Look、强度

- 平台目录 `product_motion_catalog`（代码内数据）：运镜 22 个（推拉、环绕、平移跟随、升降俯仰、手持实感、特殊技法六类，名称用通用电影术语），每个有中英运动描述和适合的镜头类型；叠加规则：最多两个、同一个不叠、「定住」类和移动类不叠。Look 14 个（8 个光线色调 + 6 个机位质感）。强度：轻 / 中 / 强。
- 导演稿每镜加 `camera_presets[]`、`look`、`intensity`、`chain_from_previous`；默认来自品类 `camera_plan`、`look`。
- 视频阶段页每镜可改这些项，改完存导演稿。
- 网页交接（`web_video_handoff`）组提示词时拼入：运镜描述、Look 光线锚点、强度、商品保真与稳定性、连续单镜头、无人声；`chain_from_previous` 时，上一镜生成时用本镜关键帧作尾帧（钉帧），剪接点不跳；网页不支持尾帧时只传首帧。
- 逐镜「重写运动」：保留关键帧，只重新生成该镜交接提示词。
- 导演稿检查加「AI 拍不出的动作」规则（列在 `product-shots` v3），命中时提示改写。

## 5. 出片方式与素材融合

- 作品快照加 `material_mode`：`photo_only`（一张图出整片）/ `user_footage`（给素材剪）/ `mixed`（混合补齐，默认）。
- 复用现有自动补齐 `material_autofill`，在「免费素材」和「AE 模板」之间加一档「图生视频」：缺镜头按导演稿的运镜、Look、强度组提示词，用商品图或该镜关键帧作首帧。`photo_only` 时所有非亮相 / 非行动引导镜头都走图生视频；亮相和行动引导用商品原图（可配 AE 模板）。`user_footage` 时不自动补，只列缺口。
- 每个镜头记录素材来源（用户 / 免费素材 + 版权 / 图生视频 自动或手动 / AE 模板）。

## 6. 图生视频开关

- 设置 → 模型与能力加「图生视频方式」：手动（网页交接，默认）/ 自动（MiniMax H3）。作品可覆盖，镜头可再覆盖。
- 自动：`minimax_cli_provider` 的视频提交支持 `--image`（首帧）、`--last-frame`（链式尾帧）、`--ratio`（9:16 / 16:9）、`--duration`（4–15 秒）；目前代码拒收带图请求，这次放开。结果作为候选素材，仍要用户在镜头里接受。
- 提交前列出将自动生成的镜头数；失败或用户不满意时一键转网页交接，交接提示词与自动一致。
- 手动：沿用 `web_video_handoff`。

## 7. 真实感与多角色配音

- 有人出镜的镜头：生图提示词和交接提示词自动追加真实素人约束（自然皮肤、不磨皮、不网红脸、不丑化、手机自然光）。
- 剧情类 `characters[]` 每人分配一个不同的 MiniMax 音色（按性别从音色表轮流取，结果固定）；旁白用作品默认音色。

## 边界

- 只吸收方法，用平台自己的话重写（clipforge 为 AGPL-3.0）。
- 价格、评价、销量、证书只用真实资料；商品亮相和行动引导镜头用商品原图或实拍。

## 8. 镜头生图（带参考图）

- `uses.shot_image`：生图模型 profile id，选项来自绑了 `image_generation` 的已登记模型；默认 CPA grok。
- 通用接口两种协议，按绑定选：OpenAI 兼容「改图」`POST /images/edits`（multipart：`model`、`prompt`、`image` 参考图、`aspect_ratio`、`n=1`）；Gemini 原生（CPA 图片协议 v2）`POST /v1beta/models/{model}:generateContent`（`inline_data` 参考图 + `imageConfig.aspectRatio`）。都没有参考图时退回纯文字生图。
- 新 MCP 工具 `generate_shot_image(shot_id, prompt, extra_reference?, as_first_frame?)`：返回素材编号；`as_first_frame` 为真时直接调用 `set_shot_first_frame`。页面「商品镜头」每镜显示当前首帧，可清除。
- 生成图：`source_kind=ai_generated`，标题「AI 示意 · 镜头 x」，带模型与参考图编号；亮相 / 下单引导镜头拒绝设生成图作首帧。
- 一致性检查：用「用途路由」里能看图的聊天模型（图片作为输入）对照商品主图逐项判：外形、颜色、材质、logo / 字样、配件、比例，输出 `{pass, problems[]}`；不过关把 problems 写进下一次提示词重画，最多 3 次。结论存进图片素材的 metadata，面板显示「一致性：通过 / 不通过（原因）」。
- 手动上传：面板每镜加「下载首帧」和「上传视频」；上传的视频进项目「视频/Broll」，记来源「手动图生视频」，并直接用到这一镜（用户自己传的就是用户的选择）。
- 自动：`generate_shot_image(as_first_frame)` → 一致性检查通过 → `generate_shot_video` → 完成后放进这一镜；任何一步不过关都停在那一步并说明。

