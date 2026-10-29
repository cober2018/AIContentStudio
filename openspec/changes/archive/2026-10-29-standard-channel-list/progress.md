# 进度

## 2026-10-29 本地实施
- 后端：`channel_registry.PLANNED_CHANNELS`（8 个渠道键、11 个待接入形态，带显示名）、`list_channel_catalog`、`ensure_work_channel`；`GET /channels?catalog=true`；`content_projects` 新建 / 修改作品改用 `ensure_work_channel`。
- 前端 `PersistentProjectPage.tsx`：渠道下拉（按形态过滤、待接入灰显、可不选；编辑时渠道没改就不提交，旧值照常保留）；删「新增身份」弹窗，角色下拉下方加「去新建角色」链接；本页与 project/ 下各页签「内容单元 / 内容身份」改「作品 / 角色」。
- 测试：`test_creation_recipe_domain_adoptions._flow` 先登记渠道再建作品（原来先建作品，靠的是渠道不校验）。
- 验证：后端 `5 failed, 2449 passed, 28 skipped`（5 个已知失败）；tsc、node --test 37/37、build 通过；接口实测 `abc` 和待接入的 `kuaishou` 都被 422 拒绝；页面实测文字 13 个、图文 2 个可选 + 3 个待接入、视频 1 个可选 + 7 个待接入。
- 待做：用户页面验收、归档。
