# 备份与恢复 Runbook（EPIC-17）

适用范围：AI Content Studio 单机正式验收与个人本地运行。当前正式 profile 是 SQLite + 本地素材库 + loopback；PostgreSQL/MinIO 章节只作为未来部署 profile，不是本轮验收前置。

V1 三类存储：

| 存储 | 内容 | 备份工具 |
|---|---|---|
| SQLite / PostgreSQL | 来源原文、事实、FactPack、稿件、审核记录、审计日志 | sqlite3 / pg_dump |
| Redis | Celery 任务队列；业务任务/Attempt/回执仍以数据库为准，副作用不可盲目重放 | 不备份队列；保留数据库任务真源 |
| MinIO（预留） | 对象存储（V1 原文存 DB，暂无数据） | mc mirror |

## 目标（建议值）

- RPO：≤ 24h（每日备份）；接真实模型、稿件资产价值上升后缩短到 ≤ 1h
- RTO：≤ 30min（还原 + 启动 + 抽查验证）

## 1. 快速备份（开发/单机 SQLite）

```bash
make backup          # 备份到 backups/（时间戳文件，保留最近 7 份）
```

等价手工命令：

```bash
cd apps/api
sqlite3 content_studio.db ".backup '../backups/content_studio-$(date +%Y%m%d-%H%M%S).db'"
```

> SQLite 必须用 `.backup`（在线备份 API），禁止直接 cp 正在写入的库文件。

## 2. PostgreSQL 备份（未来部署 profile，当前不执行）

```bash
# 完整逻辑备份（自定义压缩格式，支持单表恢复）
pg_dump -Fc -U studio -h localhost content_studio > backups/content_studio-$(date +%Y%m%d-%H%M%S).dump

# Docker 部署
docker compose exec -T postgres pg_dump -Fc -U studio content_studio > backups/content_studio-$(date +%Y%m%d-%H%M%S).dump
```

建议 crontab（每日 03:00）：

```cron
0 3 * * * cd /path/to/AIContentStudio && make backup >> /var/log/studio-backup.log 2>&1
```

## 3. MinIO 备份（未来对象存储 profile，当前不执行）

```bash
mc mirror --overwrite local/content-studio-assets backups/minio-assets/
```

## 4. 恢复流程

### SQLite

恢复必须选择同一快照的 SQLite 与被引用的不可变素材字节集合，先在隔离目录做完整性/head/hash 和历史包重新导出验收。下方命令只示意数据库步骤；不能据此跳过素材恢复、覆盖当前正式根或把部分恢复宣称成功。正式切换仍需明确目标授权，先保留旧数据库、WAL/SHM 和素材根的可恢复副本，再停止所有 API/worker 写入并切换已验证的库/素材。

```bash
# 1. 停 API 与 worker（避免写入半恢复库）
make stop
# 2. 覆盖库文件（先确认目标文件确实是旧损坏文件再替换）
cp backups/content_studio-<stamp>.db apps/api/content_studio.db
# 3. 重启
make dev
```

### PostgreSQL（未来部署 profile）

```bash
docker compose exec -T postgres psql -U studio -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='content_studio' AND pid<>pg_backend_pid();"
dropdb -U studio -h localhost content_studio
createdb -U studio -h localhost content_studio
pg_restore -U studio -h localhost -d content_studio backups/content_studio-<stamp>.dump
```

## 5. 恢复后验证清单

1. `/api/v1/health/ready` 必须返回 HTTP 200 且所有 required checks 为 true；失败应为 503/固定原因，不能只检查正文或使用旧 `status=ok` 缓存。若启用了必需队列/worker，也必须为 true。
2. `curl -s localhost:8000/api/v1/dashboard -H "X-Studio-User: admin@studio.local"` → stats 数字与备份前一致
3. 抽查 1 条冻结 FactPack：checksum 与生成稿件快照一致（资产溯源不因恢复断裂）
4. 抽查 1 篇 approved 稿件的导出（MD/JSON）可正常生成

## 6. 注意事项

- 备份文件含全部业务数据，属敏感资产：存放目录权限 700，严禁入库/入对象存储本体
- Redis 队列不备份：先从持久任务/Attempt/claim/回执恢复实际状态。已接单或 `unknown` 的供应商生成/发布不得重新触发，必须恢复原 job 或人工对账；只有明确未 dispatch 且现有产品授权/幂等机制允许的任务才可重新排队。旧稿/历史不可覆盖。
- 每季度做一次恢复演练：随机取一份备份走完整 §4 + §5 流程

## 6.1 能力禁用与回退

1. 先停止触发新任务的入口，保留当前 SQLite 与本地素材库，不删除任务、Attempt、Candidate 或 Receipt。
2. 在本机 Settings 中将对应 capability/provider 标记为 disabled，或移除对应运行时覆盖后重启 API/worker；readiness 必须重新回读，不能用旧缓存判断已禁用。
3. 对有副作用的远端 Publisher 保持 `unknown/reconciliation_needed`，不得因为回退而自动重试或切换账号；本机 `copy_package/manual_handoff` 可保留为人工交付。
4. 如需回退代码/数据库，先选取同一备份快照并在隔离副本完成 integrity、migration-head、MaterialRevision bytes 检查，再按第 4 节替换目标库。
5. 若 downgrade preflight 发现保留的 generation task、平台身份或其他不可丢失历史，立即拒绝 downgrade，改用兼容代码读取旧库或恢复完整快照；不得删除历史以制造“成功”。

## 7. 本轮已验证的本机演练

- 可重复脚本（源库只读、目标必须是新临时路径）：

```bash
cd apps/api
python scripts/rehearse_sqlite_recovery.py content_studio.db /private/tmp/aics-restore/recovered.db
```

- 脚本只使用 SQLite 在线 backup API，不覆盖源库；迁移、素材字节抽查和服务启动仍按本 runbook 的后续检查执行。
- 使用 SQLite 在线 `.backup` 从当前库生成私有临时副本，再恢复到另一个临时 SQLite 文件；`PRAGMA integrity_check` 为 `ok`，备份与恢复文件大小一致。
- 恢复副本以当前批准 head `f7d000000001` 执行 Alembic 目标升级，回读 head 仍为 `f7d000000001`，完整性仍为 `ok`。未执行未批准的 F8 身份迁移 `f8a000000001`。
- 当前库 6 个 `MaterialRevision` 的本地字节逐一重算 SHA-256，`matched=6, missing=0, mismatch=0`。该证据不改变任何正式数据。
- storage diagnostics 对当前 6 条 `MaterialRevision` 与未处理 orphan candidates 返回 `issue_count=0`、`orphan_candidate_count=0`、`truncated=false`；该诊断不返回路径或字节内容。
- 当前 downgrade preflight 发现 1 条保留 `provider_generation_task` 与 1 条平台身份绑定，因此 `downgrade_allowed=false`；未执行 downgrade、未删除历史。
- 完整验收记录见 `docs/FE_F8_RECOVERY_ACCEPTANCE.md`。

## 8. 本地素材根切换预演

在未来切换对象存储或新的本地根目录前，先用 `apps/api/scripts/rehearse_storage_cutover.py` 对 SQLite 当前所有被引用字节做隔离复制和 hash 验证。源数据库只读、目标目录必须是新目录；任一缺失或 hash 不一致都返回非零，不能把部分复制视为 ready。本机正式验收只要求完成预演，不执行真实根目录切换。
