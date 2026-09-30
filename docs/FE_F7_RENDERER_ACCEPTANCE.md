# FE-F7 Renderer 持久验证批验收

## 范围与长期需求

从 main@fad17d5 接续已批准 F7。仅完成 tasks 7.1–7.4，F7 84/105；不代表完整 F7/F8 或 PRD 已完成。新增 renderer_output exact scope 复用 CapabilityRegistration/CapabilityVerification，没有新业务表；迁移 f7b000000001 仅拓宽 CHECK，保留历史并拒绝丢失 Renderer 证据的降级。

Text v1/v2 使用真实现有 Production adapter 确定性渲染，显式管理员 probe 校验所属项目、当前 Master/context、精确 refs 和 live rights，只保存输入/输出摘要，不修改 Master 或 Candidate。Graphic/Video 人工成片如实保留 manual，不冒充自动 renderer。库存读取无渲染、字节读取、网络或子进程副作用。

## 关键实现与独立复核

- 注册实现指纹与每事件 scope/Profile 指纹分开，多个渠道验证可以同时有效。
- 指纹绑定实际解析的 renderer/adapter callable、defaults/closure；不支持的身份保持不可执行。marshal v2 排除引用跟踪/字符串驻留造成的假漂移。
- Material/Revision 与 FactPack/items 锁定、刷新并在 render 后重验，直到提交；撤权、detach、坏 hash、旧 Master/context、跨项目/viewer/伪造证据均拒绝。
- 初次独立实施复核发现三项阻断，失败测试复现后修复；三项 closure APPROVE。最终含 UI、新增权利/迁移测试与六门禁报告的窄复核 APPROVE，不把本批复核当整个 F7 通过。

## 本轮实测门禁

| 门禁 | 结果 |
| --- | --- |
| 定向 renderer / migration / capabilities / migrations | 55 passed，5 existing warnings |
| 全量后端 | 1318 passed，2 skipped，8 existing warnings，52.35s |
| TypeScript / Vite / FE-P1 | PASS |
| /projects initial | 224.84 kB raw / 72.94 kB gzip |
| /assets initial | 258.81 / 82.80 kB |
| /settings initial | 230.21 / 75.11 kB |
| common Production initial | 280.03 / 89.09 kB，无 TipTap / XYFlow |
| Text-only RendererVerificationPanel chunk | 2.59 / 1.58 kB |
| Text Studio lazy closure | 606.78 / 189.30 kB，Graphic/Video 排除 TipTap |
| OpenSpec strict | 30/30 |
| 范围 Ruff / diff-check | PASS |
| SQLite | 新隔离库 upgrade head、往返、旧行/索引/FK 保留、有 Renderer 证据拒降级 |
| PostgreSQL | 仅兼容 DDL 编译；非真实 migration 或并发验收 |

SQLite CHECK 修改遵循 Alembic batch move-copy 机制，保留已有命名约束：[Alembic 官方说明](https://alembic.sqlalchemy.org/en/latest/batch.html)。生产库未执行任何迁移。

## 隔离浏览器

脚本：apps/web/scripts/fe-f7-renderer-browser-acceptance.mjs。
隔离库：/tmp/aicontent-f7-media.7sbrOk/studio.db；媒体同目录 media。
报告：/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-renderer-browser-l6nJQP/report.json。

6 gates，0 page errors：真实 v1 渲染无内容写入、刷新持久回读、追加撤销不改稿、真实 v2 渲染独立验证、历史按钮禁用、Settings 四个 Graphic/Video manual descriptor 不标自动可执行。测试服务器含现有隔离 Provider fixtures，但本脚本未调用它们；Text 渲染确为真实本地 adapter，不是 fixture 输出。

第一次运行因测试库 admin 邮箱自动创建为 editor 无管理员按钮而失败；仅修改明确隔离库该行角色后，整套重跑通过。没有修改真实身份或降低角色门槛。

## 未完成与边界

7.5–7.7 的真实媒体 Renderer 接受/MaterialRevision/精确 render-input 绑定仍待后续；本批已有 Text 过期/版本/上下文/权利负例，不据此提前核销整个媒体 stale 门禁。外部 Provider、账号绑定无改稿 Publisher、F7 最终全阶段验收及 F8 均未完成。

未 push、deploy、生产迁移、canonical sync 或 archive；原始规格包未暂存或覆盖。仅本地 main 的 scoped batch commit。
