# FE-F8 本机正式验收状态

日期：2026-10-04

## 正式验收 profile

本轮唯一正式验收基准是：

```text
SQLite + 当前本地素材库 + loopback-only API/Web 访问
```

这不是PostgreSQL、MinIO、多主机、JWT生产身份或远程发布验收。已确认的本机profile不含生产身份/Secret Provider/新增远端发布或生产对象存储；原100项中的18项（0.7、1.1–1.10、2.4–2.6、3.3、9.5–9.7）保留延期/未验证。本机分母为82。提交边界复核发现此前将未交付MinIO 3.3误计完成，已纠正，原83分母不是当前计数。

## 本机结果（实施验收与本地main提交完成，规格生命周期待授权）

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

## 明确未纳入本机 PASS 的内容

- 生产 issuer/subject 绑定、JWT/JWKS、生产启动拒绝和身份 schema：F8 的未批准 draft，保持未启用。
- 生产 secret provider 与旧 secret override remediation：2.4–2.6 明确延期；6.1–6.3已完成本机代码控制/凭据隔离与独立复核，不代表供应商后台grant或生产Secret Provider验证。
- 远程 Publisher、真实远程回读和 PublishedContentRecord/Performance/Learning 下游：没有真实 `human_confirmed` receipt 时只记 `not_exercised`。
- push、deploy、production migration、canonical archive：本轮没有执行。

## 独立复核

此前总体复核指出的新浏览器、同项目链路、恢复重导出及Golden缺口均已有证据；最终四项blocker经过RED/GREEN实质修正后，2026-10-04收到两份定向复审：

- Harvey（`01a10298-737c-7562-a81d-23f5d3320ed2`）：安全/运维APPROVE，确认绝对deadline和第三方query日志缺口闭合，既有host/redirect/byte/Unknown边界没有削弱。
- Copernicus（`01a10298-73e9-7c02-a966-bdf2794c0a9f`）：10.9 APPROVE，确认特殊文件名只读SQLite备份及每条引用hash校验缺口闭合，原产品架构批准部分保持。

以上是此前总体审查加最终修复复审，不是本次从零重做所有审查；reviewer没有亲跑本轮全量/浏览器门禁。门禁由主执行者运行，未把reviewer受限的loopback bind尝试计为测试通过。结论仅适用于批准的本机profile，18项延期仍未验证。

## 状态解释

当前为 **FE-F8 本机实施验收与本地main提交完成，主规格同步/归档待单独授权**，还不能宣称规格生命周期已关单或完整生产就绪。身份/远端部署范围仍未批准；正式库仍使用批准f7d，未启用身份draft。

当前本机任务 **82/82**，10.11已由获准本地提交及本节ROADMAP记录完成；主规格同步和归档须单独获准。原清单 **82/100**，另外18条为延期而非本机代码blocker。未执行push/deploy/canonical sync/archive/正式迁移；未批准身份/schema/MinIO draft和原始资料包不在功能提交中，继续保留工作区。

```text
IMPLEMENTATION_COMMIT = ade4ce04870b854d262cdbc55250233cb293f54e
BRANCH = main (local)
ROADMAP_IMPLEMENTED_LOCAL = true
ROADMAP_IMPLEMENTED_PRODUCTION = false
SPEC_LIFECYCLE = active; canonical sync/archive not authorized
```

`ROADMAP_IMPLEMENTED_LOCAL`仅指本轮确认的SQLite、本地素材库和loopback范围，不表示原100项生产/远端路线全部实现。本轮功能提交没有新增迁移或永久测试。

## 2026-10-04 获准本地提交的独立快照

用户随后明确授权本地提交并融入main，但没有授权主规格同步/归档。私有索引对应无Git注册快照 `/private/tmp/aics-f8-main-commit.kQBOP1/snapshot/`：排除deps/main/models/f8a/test migration head以及混合文件中的JWT/生产身份/MinIO片段。main本来已为目标分支，不需要切分支或pull。

实际功能提交版本完整后端 **1660 passed / 28 skipped / 8 warnings，85.99秒**；Web/FE-P1、Ruff、OpenSpec strict34/34及暂存diff通过。Projects224.89/72.97kB、Settings238.88/78.06kB；source code head保持f7d。临时probe证实不存在JWT config属性、production auth/ready=false；不会因为排除draft而虚报生产就绪。首轮投影的3个health导入失败已明确修正后重跑，不计入PASS。提交凭据marker扫描0。

身份草案仍完整保留工作区，生产启动与未来媒体MinIO实现不是该提交能力。Hubble限定提交边界复审APPROVE，MinIO 3.3计数已纠正。功能commit为上述`ade4ce0`；随后的文档提交仅记录最终计数和状态，不改变已验证代码。没有新增外部调用、依赖、表或永久测试。
