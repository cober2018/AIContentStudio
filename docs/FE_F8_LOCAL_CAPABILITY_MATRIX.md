# FE-F8 单机生产环境能力矩阵

日期：2026-10-04

最终正式基准：本电脑 + SQLite + 本地素材库 + loopback-only API/Web。82/82批准范围已完成；原18项是范围外扩展及未验证记录，不是当前生产缺口。保留当前APP_ENV、凭据和Worker，服务器化不是计划中的升级。

2026-10-05当前schema为另行获准启用的`aco000000001`，代码approved默认/readiness与恢复目标同步到aco；历史f7d验收证据保留。f8a issuer/subject两列仅作为ancestry存在、7个User全null/inert，仍不代表JWT/生产身份启用或验收。现有Header/local media/Worker不变，不回滚正式库；见`ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`。

| 能力 | 实现状态 | 本机验收 | 真实远端状态 |
|---|---|---|---|
| Opportunity / Project / Identity / Brief / Boundary | implemented | verified | 不涉及远端 |
| Text / Graphic / Video Master | implemented | verified | 不涉及远端 |
| ChannelVariant / Candidate v4/v5 | implemented | verified | 不涉及远端 |
| Approval / Authorization / local package | implemented | verified | 不等同公开发布 |
| Unknown/failed delivery 不进入 published | implemented | verified | 仍需真实平台单独验证 |
| SQLite/local storage/recovery | implemented | verified，当前正式生产方案 | MinIO/PG是非当前适用的扩展参考 |
| Request/worker correlation + audit projection | implemented | 正负探针及独立复核通过 | 多主机部署未验收 |
| CPA/Gemini/Grok 外部模型 | configured/optional | 未作为 F8 本机 gate | 本轮不执行真实供应商质量评审 |
| MiniMax/本机 ASR | implemented in F7 scope | 既有证据可读 | 不扩展本轮真实发布 |
| WeChat/其他 remote Publisher | adapter exists | F7 有限草稿证据，不作为 F8 新执行 | 公开发布/远端 read-back 未执行 |
| PublishedContentRecord / Performance / Learning | implemented | 上游 local branch verified；下游 not exercised | 必须有真实 human_confirmed Receipt |
| JWT / independent Secret Provider / multi-host / MinIO | 范围外扩展，代码存在不等于启用/验收 | 不阻断单机正式使用；本轮不改运行配置 | 原验收记录未验证，不计当前完成分母 |
| Uniform outbound policy / credential isolation | implemented | 按能力预算、exact-host、CLI env隔离、真实loopback deadline/query-log探针、既有回归及独立复审通过 | 不证明供应商后台grant；CLI内部HTTP不受host helper控制 |

## 负向边界

- 本机访问限制入站，获准模型/公众号等出站继续按既有授权和凭据隔离执行；不会因部署称呼变化扩大权限。
- 日志/页面不泄密、错误可追踪、真实数据不覆盖、数据库与素材配套备份及恢复hash一致仍是正式保障。运行/停止/日志入口见[单机生产手册](runbooks/production-readiness.md)。
- `unknown`、超时、失败和未验证 Publisher 不会被转换成 `published`；既有 delivery router regression 覆盖 Unknown reconciliation 和 no-auto-retry。
- local ZIP、manual handoff、Candidate 或 DeliveryAttempt 不会单独创建 PublishedContentRecord、PerformanceObservation 或 LearningCandidate。
- 任何真实远端能力只能以 exact account + form + action + version 的独立授权证据关闭，不能从“已配置”推断“已验证”。

## 追溯入口

本机项目读模型、Candidate manifest、DeliveryTarget/Receipt、ProjectEvent 和管理员 audit projection 构成统一查询链；不新增 Dashboard/Golden/Published 第二套状态表。
