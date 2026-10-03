# FE-F8 本机能力矩阵

日期：2026-10-04

基准：SQLite + 本地素材库 + loopback-only。

| 能力 | 实现状态 | 本机验收 | 真实远端状态 |
|---|---|---|---|
| Opportunity / Project / Identity / Brief / Boundary | implemented | verified | 不涉及远端 |
| Text / Graphic / Video Master | implemented | verified | 不涉及远端 |
| ChannelVariant / Candidate v4/v5 | implemented | verified | 不涉及远端 |
| Approval / Authorization / local package | implemented | verified | 不等同公开发布 |
| Unknown/failed delivery 不进入 published | implemented | verified | 仍需真实平台单独验证 |
| SQLite/local storage/recovery | implemented | verified | MinIO/PG 是未来 profile |
| Request/worker correlation + audit projection | implemented | 正负探针及独立复核通过 | 多主机部署未验收 |
| CPA/Gemini/Grok 外部模型 | configured/optional | 未作为 F8 本机 gate | 本轮不执行真实供应商质量评审 |
| MiniMax/本机 ASR | implemented in F7 scope | 既有证据可读 | 不扩展本轮真实发布 |
| WeChat/其他 remote Publisher | adapter exists | F7 有限草稿证据，不作为 F8 新执行 | 公开发布/远端 read-back 未执行 |
| PublishedContentRecord / Performance / Learning | implemented | 上游 local branch verified；下游 not exercised | 必须有真实 human_confirmed Receipt |
| Production JWT/multi-host/MinIO deployment | draft/future | 不在本机正式基准 | 未配置、未启用 |
| Uniform outbound policy / credential isolation | implemented | 按能力预算、exact-host、CLI env隔离、真实loopback deadline/query-log探针、既有回归及独立复审通过 | 不证明供应商后台grant；CLI内部HTTP不受host helper控制 |

## 负向边界

- `unknown`、超时、失败和未验证 Publisher 不会被转换成 `published`；既有 delivery router regression 覆盖 Unknown reconciliation 和 no-auto-retry。
- local ZIP、manual handoff、Candidate 或 DeliveryAttempt 不会单独创建 PublishedContentRecord、PerformanceObservation 或 LearningCandidate。
- 任何真实远端能力只能以 exact account + form + action + version 的独立授权证据关闭，不能从“已配置”推断“已验证”。

## 追溯入口

本机项目读模型、Candidate manifest、DeliveryTarget/Receipt、ProjectEvent 和管理员 audit projection 构成统一查询链；不新增 Dashboard/Golden/Published 第二套状态表。
