# 私有原始来源摘录

此文件是已批准设计/原始创作简报，不是模型输出；未授权来源全文公开。

| 对象 | 唯一职责 | 不能承担 |
|---|---|---|
| Owner/User | 权限、Provider/Model、本机配置、通用技术能力 | 任意 Persona 的默认创作风格 |
| Persona | 创作身份、Creative Profile 根、创作记忆隔离 | 具体平台登录凭据 |
| Brand | 品牌/合规/事实约束 | 默认 Creative Skill/Style/Recipe |
| **Editorial Series**（新） | 属于 Persona 的唯一跨平台栏目：选题定位、栏目创作方法、通用更新规划 | 锁定唯一交付账号 |
| ContentAccount | Persona 下一个明确的真实平台账号、公开身份、平台能力和可选授权引用 | Master 的唯一合法交付终点 |
| SeriesAccountTarget | 一档栏目将某种内容形态投到某个具体账号的显式绑定 | 独立稿件、发布审批或登录真源 |
| ContentUnit/Master | 某角色、某栏目下的内容创作及接受真源 | 把 `unit.account_id` 等同于所有未来目标账号 |
| ChannelVariant/Candidate | 某平台/账号语境下的具体表现与候选 | 自动认为已审核或已发布 |
| Delivery Authorization/Attempt/Receipt | 针对**精确目标账号**的一次合法交付与证据 | 反向篡改源内容身份 |

**术语约束**：`platform_channel` 表示平台类型（如 `xiaohongshu`），不是具体 Account；同一平台可以有多个 ContentAccount，不能通过频道字符串猜测账号身份。

- 不选 Account 即可创建新栏目和 Master；源创作身份来自 Persona/Series，不能因为“默认平台”偷偷引入某个 Account 的创作偏好。
- 若为单账号内容显式选取 origin Account，应在 Preview 显示来源，冻结到源身份快照。它是创作来源/偏好，并不自动禁止现代 v5 后续其他账号分发；目标端仍需重适配与独立审核。
- Legacy Account Series + legacy Candidate 的固定账号约束仍保持。切换到 persona_editorial 模式须显式迁移/新 revision，不可后台偷偷改变历史含义。
- Target-specific Account Creative Profile、Series 覆盖、平台限制、账号限制，**只作用于对应 Variant/Delivery**；不得回写或重算已接受 Master。
- 若同平台两个账号存在不同 Account/Profile/rights/广告声明等要求，必须分别生成或确认兼容的 Variant，且每个目标有独立 Candidate/Review/Authorization；**禁止通过换一个 `account_id` 复用不兼容的冻结 Candidate**。
- 每次执行冻结来源 Persona/Series revision、origin context（若有）、target Account revision/渠道/form、effective profile hashes、Content/Variant/Candidate refs、审核和 rights/capability evidence；拒绝 stale/串 Persona/权限不明。


原始已授权创作简报（设计观点，不作事实验证）：
以工程师视角写一篇约500汉字的完整短文章，解释为什么内容创作要把人设与平台账号分开。仅谈设计取舍，不能声称任何软件当前实现或添加新闻、版本、数据。