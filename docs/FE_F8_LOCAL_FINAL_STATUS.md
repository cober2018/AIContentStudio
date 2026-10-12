# FE-F8 单机生产环境正式验收状态

日期：2026-10-04

2026-10-05 post-enable校准：当前正式SQLite已另行获准升级至`aco000000001`，经过`f8a000000001`；两列nullable身份字段现存在但7个User全为null/inert，JWT/production身份仍未启用/未验收。代码local approved head/readiness与恢复目标统一为aco，不回滚正式库。原82/82及下文f7d测试、旧User schema、未执行f8a均为当时历史证据，不把旧验收改成aco重跑结果。新正式启用证据见[启用记录](ALIGN_CREATIVE_LOCAL_ENABLEMENT.md)；本次仅窄修当前schema口径和固化回归，未改变认证/配置/Worker。

## 正式验收 profile

最终正式使用和验收基准是这台电脑，不是等待服务器升级的临时环境：

```text
SQLite + 当前本地素材库 + loopback-only API/Web 访问
```

维护目标是容易启动、容易排查、能备份恢复。正式范围82/82已验收；原100项中18项（0.7、1.1–1.10、2.4–2.6、3.3、9.5–9.7）保留为范围外扩展及未验证记录，不是当前生产缺口，也不是计划中的服务器升级。缺少PostgreSQL、MinIO、JWT或独立Secret Provider不阻断当前正式使用。历史83分母误纳MinIO，已纠正为82。

代码中的APP_ENV=production是特定技术分支，与“本机正式使用”不是同一判断。保留现有配置、身份、SQLite和素材路径、凭据及Worker，不为改名切换这个开关；仅本机访问限制入站，不禁止获准模型/公众号出站。现有入口见[单机生产运行手册](runbooks/production-readiness.md)。

## 单机生产结果（既有验收证据保留，规格生命周期另行处理）

下表是此前实际实施/验收记录，不是本轮文档校准重新运行所得。此次不重跑整套生成、模型质量或远端发布实验。

| 层级 | 结果 | 证据 |
|---|---|---|
| 版本化 Golden | 确定性契约 PASS | 新 Identity/Content v1 已实际消费并记录 hash：角色差异、旧 Unit/Run 固定、四组精确事实/Brief、三形态 required-state、真实 H.264 成片及五渠道映射。旧 evaluator 只消费 golden_topics；其 pass_rate=0.2969 不等于质量通过。真实模型质量 `not_exercised`。 |
| SQLite / 本地素材 | PASS | 旧 User schema/f7d 恢复库与复制素材实际启动，五种成品包逐文件 bytes 与原包一致；integrity 失败返回非零，源库只读。 |
| 健康与可观测性 | 本机 PASS | local f7d 默认门禁、production 精确 head 分离；运行状态 7 个浏览器 gate，安全日志、按字段 telemetry、有限 HTTP method、legacy no-probe 等均已修补；整体审查及残余定向复核已闭环。 |
| 出站与凭据隔离 | 本机 PASS | 按能力时间/字节预算、DNS/IP pin、exact-host限制、跨域凭据拒绝与CLI基础环境白名单保留。慢头0.251秒/慢体0.252秒中止，query token零日志；安全复审APPROVE。CLI内部HTTP及供应商grant不由此证明。 |
| 产品链路 | PASS（本地分支） | 同一 Opportunity4→Project4→Text/Graphic/Video→五 Variant/Candidate→Approval→ZIP，13 个新鲜浏览器 gate。Video spoken_script 包不是成片；另有 Golden 成片验证。 |
| 失败/Unknown 边界 | PASS | Unknown、失败、超时、未验证 Publisher 不会变成 published，不自动重发，不进入 Performance/Learning。 |
| 前端 | PASS | 新鲜 TypeScript/Vite/FE-P1：Projects 224.89/72.98 kB，Settings 239.16/78.19 kB；当前产品、运行状态和 legacy Settings 浏览器无页面错误/自动 probe。 |
| 后端 | 新鲜全量 PASS | 2026-10-04最后补丁后，在规定 `apps/api` cwd、已初始化的隔离 f7d worker库上，`1660 passed, 28 skipped, 8 warnings`，84.32秒、exit0；186既有定向通过。根cwd的32路径失败不计PASS。测试内部迁移夹具仍验证code head，不代表正式库执行f8a。 |
| 规格/静态门禁 | PASS | OpenSpec strict `34/34`、本轮 app/scripts Ruff PASS、`git diff --check` PASS。 |

## 范围外扩展与独立功能证据（不是当前生产阻断）

- 服务器issuer/subject、JWT/JWKS及技术production分支启动/schema验收：范围外，原记录未勾选。当前main已有58da22e身份代码，不等于当前库启用或相应场景已验收；本轮不改它、不运行迁移。
- 独立Secret Provider与旧override迁移：2.4–2.6范围外；现有私有凭据配置、脱敏与6.1–6.3隔离保障继续保留，供应商后台grant不能由本机探针推断。
- MinIO/PostgreSQL/多主机：不适用于最终单机方案，非待补齐的正式使用条件。
- 远程 Publisher、真实远程回读和 PublishedContentRecord/Performance/Learning 下游：没有真实 `human_confirmed` receipt 时只记 `not_exercised`。
- push、deploy、production migration、canonical archive：本轮没有执行。

## 独立复核

此前总体复核指出的新浏览器、同项目链路、恢复重导出及Golden缺口均已有证据；最终四项blocker经过RED/GREEN实质修正后，2026-10-04收到两份定向复审：

- Harvey（`01a10298-737c-7562-a81d-23f5d3320ed2`）：安全/运维APPROVE，确认绝对deadline和第三方query日志缺口闭合，既有host/redirect/byte/Unknown边界没有削弱。
- Copernicus（`01a10298-73e9-7c02-a966-bdf2794c0a9f`）：10.9 APPROVE，确认特殊文件名只读SQLite备份及每条引用hash校验缺口闭合，原产品架构批准部分保持。

以上是此前总体审查加修复复审，不是此次重新全审；reviewer没有亲跑其所审查批次的全量/浏览器门禁。门禁由主执行者运行，受限loopback bind尝试未计通过。结论适用于最终单机生产范围，18条范围外扩展仍未验证。

## 状态解释

当前为 **FE-F8 单机生产正式范围82/82完成并已有本地main功能提交**；不是“尚不能正式使用”。主规格同步/归档仍待单独授权，属于文档生命周期，不以服务器化设施尚未建设阻断本机正式使用。此前F8验收库批准head为f7d；当前正式批准head已在另行授权的Creative启用中推进到aco，身份列仅为null/inert祖先，原F8认证扩展仍未验收。

正式范围 **82/82**，10.11提交/状态记录保留；原清单82已验收＋18范围外未验证，并不是当前产品只有82%可用。ade4ce0功能提交当时排除了身份/MinIO片段；当前main@341ead8及后续既有代码/原始包保持原样，不再把历史草案未提交状态当成当前Git状态。此次只校准文档/规格，不push/deploy/迁移/canonical sync/archive。

```text
IMPLEMENTATION_COMMIT = ade4ce04870b854d262cdbc55250233cb293f54e
BRANCH = main (local)
ROADMAP_IMPLEMENTED_LOCAL = true
ROADMAP_IMPLEMENTED_PRODUCTION = true (scope: single-machine SQLite/local-media/loopback)
SERVER_EXTENSIONS_VERIFIED = false (out of current scope)
SPEC_LIFECYCLE = active; canonical sync/archive not authorized
```

这些是文档状态记录，不是新增环境变量或配置体系。PRODUCTION=true只指用户最终确定的单机正式使用范围，不把18扩展项、模型生成质量或公开发布伪报通过；此前false是旧服务器口径，现已纠正。既有功能验收证据不因术语改变重跑。

## 本轮文档校准验证

在main@341ead8只修改13份文档/规格；OpenSpec strict34/34与diff-check通过。原13条要求/46个场景标题和82已验收＋18范围外原ID保留，新增单机最终范围1条要求/3场景。代码、启动脚本和私有runtime.env共12份文件SHA256未变，apps/Makefile/compose/package无diff；现有launchd标签/脚本、命令help、日志与文档链接只读核对。没有改数据库/素材/凭据/身份/Worker，不操作服务，不重跑生成或公开发布，不提交/同步canonical/归档。

## 2026-10-04 获准功能提交的独立快照（历史证据）

用户随后明确授权本地提交并融入main，但没有授权主规格同步/归档。私有索引对应无Git注册快照 `/private/tmp/aics-f8-main-commit.kQBOP1/snapshot/`：排除deps/main/models/f8a/test migration head以及混合文件中的JWT/生产身份/MinIO片段。main本来已为目标分支，不需要切分支或pull。

实际功能提交版本完整后端 **1660 passed / 28 skipped / 8 warnings，85.99秒**；Web/FE-P1、Ruff、OpenSpec strict34/34及暂存diff通过。Projects224.89/72.97kB、Settings238.88/78.06kB；source code head保持f7d。当时临时probe验证无JWT config属性、字面technical production auth/ready=false；只表示那份提交未交付服务器扩展，不否定单机正式使用。首轮3个health导入失败修正后重跑，不计PASS。提交凭据marker扫描0。

当时身份草案保留在工作区，技术production/MinIO不在该功能提交范围；这是ade4ce0时点记录，不表示后续main仍dirty。Hubble限定边界复审APPROVE，3.3计数纠正；功能commit为ade4ce0、原收尾记录为1aa0024。此次文档校准不修改这些历史代码/验收事实，不新增外部调用、依赖、表或永久测试。
