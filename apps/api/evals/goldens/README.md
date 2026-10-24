# AIContentStudio Golden 夹具

这组夹具是 F8 本机正式验收的版本化质量基线，服务于：

- Identity：品牌、角色边界、角色差异、历史快照固定与长期观点连续性；
- Content：事实保真、Creative Brief 约束、Text/Graphic/Video 方向和首批渠道适配；
- Review：区分确定性检查与模型生成质量的人工作证据。

## 文件

- `manifest.v1.json`：夹具版本、覆盖范围、审查记录和本机执行入口；
- `identity.v1.json`：可复用的 Brand/Persona/Account/Series 方向样本和历史快照断言；
- `content.v1.json`：三种 Master 形态、首批 ChannelVariant 目标及保持/禁止规则；
- `../golden_cases.json`：30 个受控事实场景，Content 夹具从中取用例，不复制事实正文。

## 2026-10-03 新夹具实际执行

采用临时 stdin 诊断和现有 API/纯服务，不新增永久测试文件或业务表。实际 JSON 文件已读取并记录 SHA-256：

- Identity v1：`fc8875772c9c73a45c4204f8d014c0f1b05bdd8241a468823b401b05e466505a`。
- Content v1：`ec733c02261dc9db951505688db94c796fb2ec54c432ca6542e0e7f5a2a3ce6e`。

| 夹具断言 | 新鲜结果 |
|---|---|
| Brand / 两 Persona 边界、长期观点、账号归属 | 实际存入隔离项目，两个完整 profile 独立；修改一方不覆盖另一方。 |
| Unit / Run 历史身份固定 | 旧 Unit 9 → Run 1 始终 snapshot 9/checksum `c41db95e…b29ee6`；Persona 后续修改，新 Unit 使用 snapshot 12，旧 Run/read-back 不变。 |
| G001 / G003 / G006 / G009 | 分别 3/4/3/3 个 confirmed Fact，经真实 `freeze_pack` 固定 checksum/as_of，精确 citation/evidence locator 随 v4 冻结；Brief 目标/受众/主张/免责声明保持。新增无依据数字后 check blocker、freeze 409。 |
| 三种 Master 必需状态 | 读取 fixture 的 `required_state` 验证 Text Master 6、Graphic Master 8、Video Master 19 的 identity/Brief/Boundary/check/render/slot 血缘，不凭 schema 名称推定通过。 |
| 首批五渠道 | 实际 frozen Candidate 与 fixture 的 source schema、target form、Variant schema、artifact kind 五组逐项一致。 |
| 成片 Video v2 | 本地 ffmpeg 合成的 4 秒 320×568 H.264 MP4 经 ffprobe 验证；精确 shot/ref + 手工 attestation → Master 19 → Candidate 15 → Approval → Target 13 → ZIP。`render-1.mp4` 字节/hash 完全一致，无 Draft/Topic/Mother。 |

事实/视频诊断副本：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aics-f8-golden-snprd9ru/`；恢复链路与渠道/身份副本：`/tmp/aicontent-f6e-acceptance.nbjNXo/restored.db`。Video final 使用明确的测试 Registry `f8_golden_video_final/final`；不宣称 Douyin spoke-script 包是已渲染成片，合成黑画面不是真实截图/新闻事实。

这批PASS仅表示确定性结构、事实映射和冻结/权利边界正确。Text fact/identity的semantic coverage仍 `unavailable`，check为warning，审批保存精确warning disposition；不填成语义审核成功。真实模型质量继续 `not_exercised`；2026-10-04本机安全/架构独立复核已通过，不代表真实模型质量获批。

真实模型的风格/质量判断必须在 `manifest.v1.json` 的 `quality_review` 中记录 provider、model、version、输入输出标识、审查人和决定；没有真实模型或人工判断时保持 `not_exercised`，不得填成 pass。

## 变更规则

夹具只允许追加版本，不覆盖历史版本。修改事实、边界、渠道矩阵或通过条件时，必须同时更新 manifest 的变更说明和对应评测报告。fixture 文件不承载生产账号、密钥、真实素材字节或远端发布回执。
