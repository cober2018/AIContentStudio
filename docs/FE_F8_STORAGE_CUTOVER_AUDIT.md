# FE-F8 本机素材存储审计

日期：2026-10-03

正式验收范围：SQLite + `apps/api/app/media` 本地素材库 + loopback-only。MinIO/PostgreSQL 不在本轮切换或验收范围内。

## 结论

- 当前选中的 provider 是 `local`；`storage_diagnostics` 实测检查 6 个 MaterialRevision：`issue_count=0`、`orphan_candidate_count=0`。
- 5 个被当前数据库路径引用的本地字节键完成了独立 copy/hash rehearsal：`copied_and_verified=5`、`failure_count=0`、`ready_for_operator_cutover=true`。
- 本轮没有切换正式存储根目录，也没有修改数据库。目标目录只是 `/private/tmp` 下的新隔离目录。

## 统一入口审计

| 使用面 | 入口 | 本机结论 |
|---|---|---|
| MaterialRevision 写入 | `materials.store_bytes` → `material_storage.provider().put` | 通过 |
| MaterialRevision 读取/权利校验 | `materials.read_bytes_checked` → selected provider + hash | 通过 |
| DraftMedia 历史兼容 | `material_storage.read_legacy_bytes` | 仅保留兼容桥，不作为新素材写入入口 |
| AssetMedia 上传 | `asset_media.save_upload` → selected provider，`legacy/<hash>.<ext>` | 通过 |
| Workflow/Project 输出 | `project_outputs.associate_step_output` → `read_bytes_checked` | 通过 |
| Review/Delivery/Candidate package | `delivery`、`production_packages`、renderers → `read_bytes_checked` | 通过 |
| 本地 ASR/渲染/供应商 CLI 临时文件 | 临时工作目录或 sandbox 输入输出 | 不属于素材库；接受后才进入 MaterialRevision |

`MEDIA_ROOT/working`、ASR/渲染器临时目录和供应商 CLI 的临时文件不是第二套素材库，不参与持久化字节真源。旧的绝对路径只在 development/test 的历史读取兼容桥中允许，production/object-storage 路径不放宽。

## 可重复命令

```bash
cd apps/api
.venv/bin/python scripts/rehearse_storage_cutover.py \
  content_studio.db \
  app/media \
  /private/tmp/aics-f8-storage-cutover-<new-dir>/restored-media
```

命令要求目标目录不存在，源 SQLite 只读打开；任何缺失字节、源 hash 不一致或目标 hash 不一致都返回非零，不得宣称可切换。真实存储切换仍需另行授权、生成数据库键映射并保留回滚副本，本轮不执行。
