# findings

- 账号模型 `ContentAccount`：persona_id、platform_channel、platform_account_id，(平台, 标识) 全局唯一；没有「同角色同平台唯一」约束。
- 账号资料走 `content_identity.REVISION_MODELS["account"]`，`effective()` 把账号层叠在角色上；delivery.py、channel_variants.py 读最新账号修订。
- 正式库：账号 2 个；`content_account_revision`、`account_workflow_default`、`content_series`、`series_account_target`、账号快照、内容记忆均 0 条。
- 账号页现有标签：概览、编辑资料、修订历史、关联与管理、内容记忆、平台连接；平台连接只有公众号（AppID，凭据走部署环境）。
- 用户确认：同一角色同一平台只能一个账号；一个角色可以有多个平台的账号。
- 决定：不存密码、不代登录；跳转依赖用户浏览器已有登录。内容记忆/学习里的账号范围本次不动，后续单独清理。
- 实施决定：账号仍留在身份层级里（作品可指定目标账号、栏目投放绑定账号），只拿掉它的资料修订；`ENTITY_MODELS` 管实体，`REVISION_MODELS` 只含品牌/角色/栏目。内容学习的账号范围改用 `ENTITY_MODELS`，行为不变。
- 冻结的目标账号上下文只留 content_account_id、platform_channel、platform_account_id（和栏目绑定），去掉 account_revision_id、account_profile_checksum、profile；正式库渠道版本 0 条，无历史冻结数据受影响。
- 「绑定真实账号」（platform-binding）一并删除：账号登记时必带平台和标识，绑定步骤已无用；公众号接口连接表单保留。
- 栏目只认角色栏目：层级校验与列表不再处理 account_legacy；`content_series` 表的 scope/account_id 列和约束本次未动（0 行），后续可清。
- 独立自有账号（不挂角色，商品视频用）保留，不受「同角色同平台唯一」影响。
- 迁移 `acctrec0001`：空表才删 `content_account_revision`、`account_workflow_default` 和 `identity_snapshot.account_revision_id`，加 `content_account.home_url`；本地批准头和 runtime.env 的 REQUIRED_SCHEMA_HEAD 改为 acctrec0001。
- 平台入口地址 20 个用 curl 都返回 200（未登录状态）；登录后是否直达对应页面要用户点开确认。
- 账号目录的新建表单原来固定 personaId=null，只能建独立账号；这是导致「关联不了角色」的原因。
- 换归属角色只允许未被使用的账号：作品、快照、投放、栏目绑定、内容记忆都按旧角色冻结过这个账号，改了会让历史对不上。
