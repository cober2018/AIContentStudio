# Creation Recipe 本机正式启用记录

## 需求与范围

2026-10-06 用户明确授权：备份 SQLite＋素材，再启用 `crs000000001`。这台电脑继续是正式生产环境；本轮不提交推送、同步归档或调用真实模型/公众号。

## 当前正式状态

- 工作区：`main@341ead8`＋已有 ACO/F8/Recipe 未提交修改；没有新提交。
- 正式库：`apps/api/content_studio.db`，唯一head、代码approved默认与私有 `REQUIRED_SCHEMA_HEAD` 均为 `crs000000001`。
- `aco → crs` 只新增 `workflow_step_attempt.input_snapshot_json / execution_receipt_json` 两个nullable JSON列，不回填、不删除、不改写业务历史。
- `APP_ENV=development / AUTH_MODE=development_header` 不变；f8a身份列全NULL/inert，不代表JWT启用。
- 素材根仍为 `apps/api/app/media`；私有配置只改schema head一行，凭据及签名key不变，仍0600/Git忽略。
- API `127.0.0.1:8000`、Web `127.0.0.1:5173`；原API/Worker LaunchAgents已恢复，Worker Redis DB2/四队列/concurrency=1/beat拓扑不变。

## 配套备份与验证

私有0700快照：`backups/recipe-local-enable-r2D4Liwl/`。

| 内容 | 用途 |
|---|---|
| `before.db`＋`runtime.env` | 升级前aco在线backup及对应配置 |
| `rehearsal.db` | 从before在线backup，副本显式升级crs |
| `enabled.db`＋`runtime.env.enabled` | 正式升级后在线backup及对应crs配置 |
| `media-full/` | 完整素材：65文件、32,992,851字节 |
| `referenced-media/` | 7条引用、5个去重文件，逐引用hash通过 |
| `generation-receipt-keys.json` | 原签名配置的0600私有备份，不回显/入Git |

停写前Worker active/reserved/scheduled及四队列均0；只停止原两个确切launchd label，确认进程/8000退出后备份。副本保全通过后，正式执行明确目标 `alembic upgrade crs000000001`，不用未来head或downgrade。

- 副本/正式库 integrity=ok；89张表的原列、5,145行完整hash一致（Alembic版本值除外），集合hash `d16b5fdca52bfde87621bec6d25300a043eaec9a4e8ef35d286759dc9440f43a`。
- 既有97条FK异常集合完全不变，是历史债，不是新增异常；没有擅自修复。
- 原正式Attempt为0行，新列nullable JSON，无新Attempt或伪造回执。
- 65个素材文件逐字节hash一致，集合hash `e40520f49cf3b516c9eab69533fdcdb4a63ff848f38940685376fbe4c117b808`，未新增/撤权/替换素材。
- 重启后再次核对原列数据/素材hash不变。API和Web代理readiness均HTTP200/ready=true，required全true；LLM诚实为not_probed。
- Worker恢复后active/reserved/scheduled仍0。MCP正式initialize/initialized/tools-list只读联通HTTP200，15工具，无approval/publication工具，未执行写工具。
- 三个旧Unit的Recipe/options均HTTP200，三个模板可读；没有自动绑定Workflow。
- 实际浏览器Video Unit2显示Creation Recipe/选择窗口/Video模板，Master #5/v3及43条字幕仍在；stale Brief/Evidence、缺成片等保护保留。只打开选择窗口，未确认绑定、生成、保存或发布。

## 使用、恢复与待办

入口 `http://127.0.0.1:5173/production`。旧Unit没有流程时在Creation Recipe明确选择，不能通过自动改绑定制造可执行状态。启动/日志仍用[本机运行手册](runbooks/production-readiness.md)的原方案；Web本轮沿用 `cd apps/web && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`，保持运行，无新依赖/部署体系。

恢复先在新路径验证同一组DB/素材/config、head/历史hash/integrity；before和enabled配置不可混用。正式库不得盲目降级或覆盖；有receipt时crs downgrade拒绝丢失历史，回退需另行明确授权。ACO/f7d记录保留为历史，当前恢复目标为crs。

**141/144**：关闭4.7；19.4永久新增回归和19.6完整backend按用户决定暂缓；19.12仅正式迁移子步骤完成，canonical/archive/commit/push未执行，不提前勾选复合项。

本轮没有运行pytest/全量backend或重跑Web构建。此前构建/三形态隔离写链不冒充本轮结果；新鲜范围Ruff、strict/diff见change进度。只维护现有schema/readiness测试的head期望，没有新增用例。真实模型/专业工具质量与公开发布不由本次回读证明，本地ZIP仍不等于公开发布。

实际skills：using-superpowers、openspec-apply-change、writing-plans、executing-plans、verification-before-completion。
