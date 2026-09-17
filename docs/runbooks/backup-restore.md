# 备份与恢复 Runbook（EPIC-17）

适用范围：AI Content Studio 全部持久化数据。V1 三类存储：

| 存储 | 内容 | 备份工具 |
|---|---|---|
| SQLite / PostgreSQL | 来源原文、事实、FactPack、稿件、审核记录、审计日志 | sqlite3 / pg_dump |
| Redis | Celery 任务队列（可丢，任务可重放） | 不备份 |
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

## 2. PostgreSQL 备份（生产）

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

## 3. MinIO 备份（启用对象存储后）

```bash
mc mirror --overwrite local/content-studio-assets backups/minio-assets/
```

## 4. 恢复流程

### SQLite

```bash
# 1. 停 API 与 worker（避免写入半恢复库）
make stop
# 2. 覆盖库文件（先确认目标文件确实是旧损坏文件再替换）
cp backups/content_studio-<stamp>.db apps/api/content_studio.db
# 3. 重启
make dev
```

### PostgreSQL

```bash
docker compose exec -T postgres psql -U studio -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='content_studio' AND pid<>pg_backend_pid();"
dropdb -U studio -h localhost content_studio
createdb -U studio -h localhost content_studio
pg_restore -U studio -h localhost -d content_studio backups/content_studio-<stamp>.dump
```

## 5. 恢复后验证清单

1. `curl -s localhost:8000/api/v1/health` → `{"status":"ok","db":true}`
2. `curl -s localhost:8000/api/v1/dashboard -H "X-Studio-User: admin@studio.local"` → stats 数字与备份前一致
3. 抽查 1 条冻结 FactPack：checksum 与生成稿件快照一致（资产溯源不因恢复断裂）
4. 抽查 1 篇 approved 稿件的导出（MD/JSON）可正常生成

## 6. 注意事项

- 备份文件含全部业务数据，属敏感资产：存放目录权限 700，严禁入库/入对象存储本体
- Redis 队列不备份：worker 未消费的任务丢失后，重新触发生成即可（生成幂等，旧稿不覆盖）
- 每季度做一次恢复演练：随机取一份备份走完整 §4 + §5 流程
