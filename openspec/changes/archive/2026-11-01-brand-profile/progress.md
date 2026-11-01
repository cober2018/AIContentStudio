# 进展

- 2026-11-01：方案已写，等待用户确认。
- 2026-11-01：用户确认，并决定「母婴博主nina」旧字段挪到「懒羊羊小王」。已实施：
  - 数据：懒羊羊小王（角色 5）新建资料 v1（定位母婴博主、受众、内容领域，原样搬过去）；品牌 2 新建空资料 v2，旧字段只留在历史 v1。
  - 后端：`content_identity.BrandProfile`、`brand_terms`；`save_revision` 按类型校验（品牌只收品牌字段，Logo 须本人上传且允许模型使用）；`effective` 不再把品牌字段合并进角色，品牌作为 `brand` 块随身份快照冻结（平台任务包 `identity_content` 自然带上）；`persona_brief` 的 `brand` 改为品牌资料并加规则；文字 / 图文 / 视频原稿检查加品牌禁用词与「不能说的话」硬检查（`brand_forbidden_phrase`）；`routers/content_identities` 修订入参改为按类型校验，新增 `GET /content-brands/{id}/logos`。
  - 前端：新增 `BrandProfile.tsx`（品牌概览、编辑、Logo 上传）；`IdentityWorkspace` 品牌的概览 / 编辑资料改用它；`PersonaPortraits` 导出可复用的缩略图、上传按钮。
  - 测试：旧测试里「品牌填角色字段、角色继承品牌」的预期改为新规则（test_fe_f3b_content_identity、test_persona_creative_identity、test_fe_f5b_learning）。
- 验证：在数据库副本上走通——品牌填角色字段被拒；角色定位不被品牌覆盖；新作品快照、第三方模型简报都带品牌块；品牌禁用词与红线进入检查词表。全量后端 2466 passed，失败的 5 个是已知旧问题；tsc 通过；API 已重启。
- 待办：用户在页面填「知数造物」资料并验收；之后提交、归档。

## 2026-11-01 页面验收反馈修复
- 新上传的 Logo 在保存前只显示「待保存」：改为用本地文件预览。
- 主色原先只收 `#RRGGBB`，用户按「色值 · 名称 + 用途」填写导致整次保存报 `identity_profile_invalid`：主色改为每行最多 200 字的自由文本，最多 20 行。
- 保存校验失败时，页面列出不合格的字段中文名，不再只显示错误码。
- 验证：tsc 通过；身份相关测试 81 通过；API 已重启。
