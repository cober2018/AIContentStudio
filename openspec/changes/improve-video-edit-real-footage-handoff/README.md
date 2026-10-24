# improve-video-edit-real-footage-handoff

## PRD / 需求背景
科技新题成片第二版（P39/U72，执行4，2026-10-21）用作者实拍素材完成，但平台记录时多处只能绕开：编辑清单每镜只能登记一个来源、执行输入整份复制、规划阶段看不到项目素材、作品级方法设置把剪辑方法清空、成片响度达不到短视频常用值且不削波。用户确认：一镜多来源必须支持；素材以链接方式提供而非复制；其余按提出的方向改。

## 当前阶段
用户已确认并 apply 完成（2026-10-21），5项均已实现并实跑验证，strict 校验通过；未提交、未归档（等用户明确授权）。

## 目录结构
- proposal.md：为什么与改什么
- design.md：关键决定（硬链接+复制兜底、清单按Master时间线放置校验、视频规划素材目录、按阶段覆盖、旁白母带派生）
- tasks.md：实施清单
- specs/：web-video-production-handoff、creation-recipe-stage-control-loop、persona-creative-configuration、material-library-v1 增量

## 已完成
- 提案与规范增量；用户选定输入方式为 APFS 写时复制克隆（硬链接/软链接会让剪辑端写穿素材库唯一副本）
- 代码：`web_video_handoff.validate_edit_manifest`（一镜多来源、扩展名路径）、`creative_executions`/`creative_media_stream`（克隆输入、审计、响度测量入输出元数据）、`creation_recipes`（角色视频阶段素材目录）、`creative_packages`（作品配置按阶段合并）、`audio_quality.master_loudness`+`POST /materials/{id}/revisions/{rev}/loudness-master`、`creative_contracts`（元数据允许loudness）、视频交接 Skill 说明
- 实跑证据见 tasks.md「Verification record」

## 待完成 / TODO
- 用户授权后提交与 archive
- 另记问题：作品当前 Master 较大时规划阶段预览超 128KB

## 关键设计决策
见 design.md「Decisions」。证据见 `../improve-persona-content-methods/findings.md` 2026-10-21 条目。

## 依赖与启动方式
同仓库 API（`launchctl kickstart -k gui/$(id -u)/com.aicontent.api` 重启前确认无运行中尝试）；校验：仓库根目录 `openspec validate improve-video-edit-real-footage-handoff --strict`。
