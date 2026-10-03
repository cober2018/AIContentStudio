# F8 本机恢复验收记录

日期：2026-10-03
范围：SQLite＋本地素材库＋仅本机访问
状态：本机恢复批次通过；不代表 PostgreSQL/MinIO、多机或生产身份部署已通过。

## 证据

1. 使用 `apps/api/scripts/rehearse_sqlite_recovery.py` 从当前 SQLite 源库做在线 backup，写入隔离临时副本；源库未被覆盖。
2. 源库与恢复副本 `PRAGMA integrity_check` 均为 `ok`。SQLite/WAL 在线备份可能重排页、改变文件大小，不能把文件大小相等作为恢复完整性的通过条件。
3. 隔离恢复副本读取到批准的 `f7d000000001` migration head；未执行未授权的 `f8a000000001` 身份/schema 草案。
4. 当前本地 storage diagnostics 检查 6 条 `MaterialRevision`：`issue_count=0`、`orphan_candidate_count=0`、`truncated=false`。
5. 当前本地 6 条已引用素材字节重算 hash：`matched=6`、`missing=0`、`mismatch=0`。
6. downgrade preflight 发现 1 条保留 `provider_generation_task` 与 1 条平台身份绑定，返回 `downgrade_allowed=false`；未执行 downgrade、未删除历史。

## 同一产品项目的恢复启动与重新导出

- 新鲜隔离源：`/tmp/aicontent-f6e-acceptance.nbjNXo/studio.db`；恢复库：同目录 `restored.db`；复制素材：`restored-media/`。该库是验收夹具，不是正式库。源与副本完整性均 `ok`，head 均 `f7d000000001`，User 不含待批准 identity 列。
- 复制演练检查 1 个被引用的唯一字节对象，复制 1 个、失败 0；多个精确 MaterialRevision 可以引用相同 hash，不能将其误报为多个不同文件。
- API 在恢复 DB + 恢复 media 下以 loopback 启动，就绪成功，旧 User ORM 读取及新用户插入/refresh 均通过，没有应用身份草案迁移。
- Project 4 的 Candidate 6/7/8/9/10 对应五种渠道包再次导出：WeChat article、X thread、X single、Xiaohongshu image_note、Douyin spoken_script。所有 ZIP entry 名称集合及逐 entry 解压字节与原包一致，包含 frozen manifest、正文/脚本、图片、估计字幕和发布说明。
- 已实际复现并修正 rehearsal 在 integrity 失败时仍 exit0 的问题；现在失败返回 2。backup 与 integrity source 统一使用只读 SQLite URI；不打开源库的可写连接。

## 边界

- 演练只写隔离临时路径，不修改正式数据库、正式素材库、密钥或远端服务。
- 备份成功不等于服务已切换；真实恢复仍需按 runbook 停止 API/worker、替换目标库后再启动。
- PostgreSQL/MinIO、生产 JWT、远端发布和生产迁移保持后续部署范围。

## 2026-10-04 独立复核补验

架构终审发现并实质修正两处恢复可信度缺口：backup/storage source URI 使用 `Path.as_uri()` 编码特殊字符、`mode=ro` 保持只读；存储复制去重前逐条验证 expected hash，而不是只保留同 key 首个值。临时 RED 复现两项失败，GREEN 验证 `records#?.sqlite` 备份读到原 marker、`media#?.sqlite` 读到两条引用、冲突 hash 返回 2/ready=false、相同 hash 两引用验证两条仅复制一份、未创建截断路径源库。无新永久测试或正式数据写入。脚本Ruff/diff PASS；Copernicus（`01a10298-73e9-7c02-a966-bdf2794c0a9f`）最终定向架构复审10.9 APPROVE，两blocker闭合、原架构批准部分不受影响。reviewer未亲跑恢复或浏览器，不以此声称从零重新全审。

修正后实际 f7d 验收源重演：`/private/tmp/aics-f8-final-recovery.JdpsNl/`，源/恢复 integrity 均 ok，head=`f7d000000001`，Project/Unit/Master/Variant/Asset/Review/Target/MaterialRevision 八表计数逐一一致；2 条素材引用逐一验证、1 个字节对象复制、0 失败、ready=true。未重启或切换正式库；原五包重新导出证据仍保留，不声称本轮又重跑浏览器。
