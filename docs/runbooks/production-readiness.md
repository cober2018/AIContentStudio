# 单机生产环境运行手册

本电脑就是最终生产环境：SQLite＋当前配置的本地素材库＋仅本机API/Web。维护目标是容易启动、容易排查、能够备份恢复；不是等待升级到服务器的临时方案。82/82既有正式验收证据保留，不以缺少JWT/PostgreSQL/MinIO/独立Secret Provider阻断使用。

本文入口按现有startup脚本、launchd plist、Web package和Makefile核对，以下命令供日常操作，不构成自动执行授权；已获准的实际操作以对应启用记录为准。不要为“生产”改APP_ENV：字面production技术分支有JWT/schema/MinIO要求，与本机正式使用称呼不同。保留当前runtime.env、SQLite、素材路径、身份行为和Worker，不新增配置体系或组件。

## 1. 当前启动、停止与日志入口

2026-10-06 Recipe启用后，approved schema/readiness默认与私有配置均为`crs000000001`（`f7d→f8a→aco→crs`）。crs仅增加两个nullable Attempt回执列；f8a身份列仍全空/inert，不启用JWT，Header/凭据/Worker不变。当前配套备份见[Recipe启用记录](../CREATION_RECIPE_LOCAL_ENABLEMENT.md)；[10月5日ACO记录](../ALIGN_CREATIVE_LOCAL_ENABLEMENT.md)及f7d验收保留为历史，不重复迁移/回滚正式库。2026-10-12稳定性加固追加`idx000000001`纯增量索引迁移（链变为`crs→idx`，8个热路径读索引，不改列/约束），正式库已upgrade、runtime.env的REQUIRED_SCHEMA_HEAD已同步为`idx000000001`，迁移前快照在[backups/index-migration-20261012](../../backups/index-migration-20261012/)；API/Worker已按上表kickstart重启加载新代码。

从仓库根目录操作；现有本机launchd标签为`com.aicontent.api`、`com.aicontent.worker`。API脚本加载被忽略的`apps/api/scripts/startup/runtime.env`并绑定127.0.0.1:8000；Worker脚本加载同一私有配置，保留既有Redis/default,llm,ingestion,export队列与beat拓扑。没有理由因“本机生产”删除Worker。

| 操作 | 既有入口 |
|---|---|
| 查看常驻状态 | `launchctl list` 中查看上述两个标签；此处不输出私有环境配置 |
| 启动未加载的API | `launchctl bootstrap gui/$(id -u) /Users/mshengran/Library/LaunchAgents/com.aicontent.api.plist`；已加载时不要重复bootstrap |
| 启动未加载的Worker | `launchctl bootstrap gui/$(id -u) /Users/mshengran/Library/LaunchAgents/com.aicontent.worker.plist`；保留现有队列依赖 |
| 有需要时重启现有服务 | `launchctl kickstart -k gui/$(id -u)/com.aicontent.api`；Worker用相同命令的`com.aicontent.worker`标签 |
| 当前Web入口 | `cd apps/web && npm run dev`；现有Vite为localhost:5173，代理到本机API；不要新增`--host 0.0.0.0` |
| 停止常驻写入服务 | 停止新任务入口，确认已发送任务状态后，分别`launchctl bootout gui/$(id -u)/com.aicontent.worker`、`launchctl bootout gui/$(id -u)/com.aicontent.api`；Web前台终端Ctrl+C |
| API/Worker日志 | `logs/api.log`、`logs/worker.log`；按时间/trace/reason定位，不复制密钥或原始私有内容 |
| 前台排查入口 | 未加载常驻服务且端口不冲突时，用既有`zsh apps/api/scripts/startup/start_api.sh`或`start_worker.sh`；停止用所属终端Ctrl+C，不同时启动重复实例 |

`make stop`只杀uvicorn，不停Worker，launchd还可能自动拉起API；它不是完整停止方案。停用服务前处理已dispatch/unknown任务，不能把停止或重启变成自动重新发送。上述操作不是本轮自动执行授权。

## 2. 检查与配套备份恢复

- 已启动必要API/Worker/队列后，管理员显式读取`/api/v1/health/ready`或Settings运行状态；required失败返回503/安全reason，存活不等于依赖全部可用。
- 普通Settings/健康清单不调用模型或Publisher；只有既有明确授权入口允许外部调用。loopback是入站限制，不是出站禁令。
- 私有runtime.env沿用现有权限与gitignore；页面、日志、错误和回执只允许脱敏投影，不迁移或删除个人凭据。
- `make backup`是既有数据库在线备份入口（保留最近7份），不是完整数据库＋素材备份。先按[备份恢复手册](backup-restore.md)建立同一快照的SQLite和被引用不可变素材集合，隔离验证integrity/head/hash和历史成品包；恢复不能直接覆盖当前真实数据。
- 不为日常启动运行`make seed`、`make migrate`、复制扩展production模板或切换素材根。数据库/素材正式替换、迁移和远端发送必须有明确目标与授权。
- 维护结果按本机稳定正式使用、排查和恢复判断；local ZIP不是公开发布，契约测试不是大模型质量验证。

## 3. 非当前适用的服务器扩展参考

以下保留原始JWT/对象存储/服务器部署约束，仅在以后另行改变目标并授权扩展时参考。它们不是当前启动步骤、待升级计划或正式使用前置，也不证明相关配置已启用。范围外原18条仍未验证。

### 3.1 扩展配置模板

`docs/runbooks/production.env.example`只含占位符，不替换当前runtime.env。如果另行授权启用字面APP_ENV=production技术分支，其扩展检查要求同时配置：

- `APP_ENV=production`；
- JWT issuer、audience、签名密钥或批准的 JWKS；
- `REQUIRED_SCHEMA_HEAD` 与代码唯一 Alembic head；
- `MATERIAL_STORAGE_BACKEND=minio` 及 endpoint/bucket/credentials；
- 数据库和队列连接；
- 外部能力的最小权限 credential reference。

扩展迁移/head与启动检查须另行授权；缺项fail closed，不以删除历史、自动迁移或seed制造通过。当前单机生产不执行这些扩展步骤。

### 3.2 服务器扩展 API / Web / Worker

1. 先准备备份、secret reference、数据库和对象存储；完成 migration-head 检查。
2. 只绑定 loopback 或受控私网接口；不把开发 `X-Studio-User` Header auth 暴露到生产。
3. 启动API和配置要求的worker/beat，再检查readiness；不能因只启动API而跳过必需Worker检查。
4. Web 只提供构建产物，`/api` 反代到 API；浏览器不接触 secret。
5. readiness 失败时停止流量切换，查看安全 reason code，不读取或回显原始异常。

### 3.3 扩展 Migration / storage / secret

- 先做 SQLite 在线备份或 PostgreSQL `pg_dump`，并对引用字节做 `rehearse_storage_cutover.py` copy/hash 预演。
- migration 必须是单一 head、可回滚/可恢复；任何 destructive change 先停在规格层。
- MinIO 切换必须完成全量 referenced-byte copy/hash 校验，不允许混合旧根和新桶。
- SystemSetting plaintext secret 必须先逐项替换成环境变量/Secret Provider reference，再启动 production；禁止为通过启动检查直接删除历史行。
- 真实回滚使用同一 DB/字节快照，不在线删除历史 Candidate、Receipt、Attempt 或生成任务。

### 3.4 扩展 Reverse proxy / TLS / auth

- 反向代理负责 TLS、受信 `Host`、请求体/超时上限和安全 header；API 仅接受代理明确传入的可信身份。
- 生产只接受已验证 issuer + audience + signature 的 token，并映射到已存在的 active User/Role；拒绝默认用户、自动建用户和 token 内未受信任的 role。
- `X-Studio-User` 仅 development/test；不得由代理透传成生产身份。
- `/metrics`、ops audit、storage diagnostics 只给管理员；日志和审计只保留 allowlist metadata。
- 外部 Publisher 仍需要 exact account/form/action/version 的单独授权与回执，TLS/代理可用不等于远端能力 verified。

## 4. 当前可选出站 host 限制（保留现有配置）

Backend environment 的 `OUTBOUND_ALLOWED_HOSTS` 默认为空，保留当前各能力的精确目标/SSRF/trusted-LAN 规则；配置后仅允许逗号分隔的精确域名或 IP，不接受 wildcard、URL、空条目或 suffix 匹配。它在 HTTP 的 DNS/发送前执行，不含密钥，不自动修改现有个人配置。所有实际需要的模型、来源、微信等 host 都必须包含，未列出的目标会不可执行。

这不会放宽能力本身的私网/协议限制，也不约束MiniMax CLI内部HTTP。CLI保留固定命令/参数、已有配置和有界隔离进程。预算仍按能力区分（聊天120秒、生图25秒）；供应商grant只按真实证据判断，独立Secret Provider是范围外扩展，不阻断当前单机生产。
