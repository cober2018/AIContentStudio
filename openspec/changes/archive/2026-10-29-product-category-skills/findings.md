# 发现

- clipforge 代码里运镜 22 个、Look 14 个、成片配方 391 个（README 写 18 / 8，已落后）。源码只读副本在 `output/_平台/吸收资料/clipforge`（AGPL-3.0，只吸收方法）。
- 平台品类目前是自由文本 `product_json.category`；「商品表现风格」用 `categories[]` 白名单匹配，没有品类到 skill 的结构。
- 角色结构可直接对照：`ContentPersona` + Revision、`creative_configuration.resolve`、`PersonaCreativeConfig.tsx`、`ProductionStageControls`。
- 发起页已有受众、买家处境、顾虑、卖家优势、价格、时长、渠道；缺参考爆款结构。
- 图生视频只有网页交接 `web_video_handoff.py`；用户定继续这样做。
- 本机 mmx CLI 的 MiniMax-H3 支持 `--image` 首帧、`--last-frame` 尾帧、`--ratio`、`--duration 4–15`；平台 `minimax_cli_provider.submit_task` 目前拒收带图请求，只做文生视频。
- 现有自动补齐 `material_autofill`：用户选的不动 → 有授权的免费素材 → AE 模板 → 缺口。
- 「接上一镜」改用钉帧：上一镜生成时用下一镜关键帧作尾帧（MiniMax H3 `--last-frame`），不用抽帧，自动和手动都适用。
- 视频链路由第三方模型经 MCP 主导，所以品类 / 风格 / 出片方式通过 `get_video_brief.product` 下发，平台不自己跑脚本。
- 多角色配音的性别从角色 id 前缀（female- / male-）判断，音色从已验证的 MiniMax 音色库按顺序固定分配。
- 自动图生视频的模型放在「用途路由 → 图生视频」，不放进「生成能力与插件」：那里的生视频路由（minimax.video，Hailuo-2.3）是旧的通用生成面板用的，商品镜头需要首尾帧和画幅，只有 H3 全支持。
- UUAPI 视频：模型名用 `minimax_h3`（`MiniMax-H3` 在当前分组没开视频接口）；`/v1/videos` 只收 multipart 的 `input_reference` 文件或网址，不收 base64；返回 `id` 与 `status`，`/content` 取 MP4。请求 720x1280 实际返回 768x1344，尺寸由中转方决定，清晰度按 `resolution` 字段尽力传。
- 本机 mmx 命令行没有清晰度参数，选 MiniMax 本机时清晰度设置不生效。
- UUAPI 视频文档（uuapi.io/docs/video）：POST /videos，字段 model、prompt、seconds、size、aspect_ratio、workflow_id、prompt_enhance、images、input_reference 等；文件上传用 image_1 / image_2；首尾帧要 `workflow_id=fl2v` 加两张图；尺寸表 480P / 768P / 1080P（竖屏 480x864 / 768x1376 / 1088x1920）；状态 pending、queued、in_progress、completed、failed、cancelled；/content 取 MP4。实测 480P 竖屏出片 480x864；`last_frame_image` 字段会被静默忽略。
