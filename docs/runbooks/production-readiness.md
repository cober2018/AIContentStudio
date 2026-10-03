# Production profile runbook（未来部署参考）

本文件不是本机正式启动说明。当前验收基准仍是 SQLite + `apps/api/app/media` + loopback-only；本文件用于未来启用 PostgreSQL/MinIO/JWT/反向代理时的配置和检查顺序。

本次本机提交不包含JWT/User身份字段/生产启动切换或MinIO媒体provider实现，不能仅复制此模板就启动正式生产profile。以下为待单独批准并实现的未来要求，不是当前已交付能力。

## 1. 配置模板

复制 `docs/runbooks/production.env.example` 到受控 secret/environment 管理，不把实际值写入 SQLite、Git 或日志。必须同时配置：

- `APP_ENV=production`；
- JWT issuer、audience、签名密钥或批准的 JWKS；
- `REQUIRED_SCHEMA_HEAD` 与代码唯一 Alembic head；
- `MATERIAL_STORAGE_BACKEND=minio` 及 endpoint/bucket/credentials；
- 数据库和队列连接；
- 外部能力的最小权限 credential reference。

启动前执行 `alembic current`、`alembic heads` 和 `/api/v1/health/ready`；缺项必须 fail closed，不自动建表、迁移或 seed。

## 2. API / Web / Worker 启动

1. 先准备备份、secret reference、数据库和对象存储；完成 migration-head 检查。
2. 只绑定 loopback 或受控私网接口；不把开发 `X-Studio-User` Header auth 暴露到生产。
3. 启动 API，再等待 readiness；之后才启动 worker/beat。
4. Web 只提供构建产物，`/api` 反代到 API；浏览器不接触 secret。
5. readiness 失败时停止流量切换，查看安全 reason code，不读取或回显原始异常。

## 3. Migration / backup / storage / secret

- 先做 SQLite 在线备份或 PostgreSQL `pg_dump`，并对引用字节做 `rehearse_storage_cutover.py` copy/hash 预演。
- migration 必须是单一 head、可回滚/可恢复；任何 destructive change 先停在规格层。
- MinIO 切换必须完成全量 referenced-byte copy/hash 校验，不允许混合旧根和新桶。
- SystemSetting plaintext secret 必须先逐项替换成环境变量/Secret Provider reference，再启动 production；禁止为通过启动检查直接删除历史行。
- 真实回滚使用同一 DB/字节快照，不在线删除历史 Candidate、Receipt、Attempt 或生成任务。

## 4. Reverse proxy / TLS / auth

- 反向代理负责 TLS、受信 `Host`、请求体/超时上限和安全 header；API 仅接受代理明确传入的可信身份。
- 生产只接受已验证 issuer + audience + signature 的 token，并映射到已存在的 active User/Role；拒绝默认用户、自动建用户和 token 内未受信任的 role。
- `X-Studio-User` 仅 development/test；不得由代理透传成生产身份。
- `/metrics`、ops audit、storage diagnostics 只给管理员；日志和审计只保留 allowlist metadata。
- 外部 Publisher 仍需要 exact account/form/action/version 的单独授权与回执，TLS/代理可用不等于远端能力 verified。

## 5. 可选出站 host 限制（本机也适用）

Backend environment 的 `OUTBOUND_ALLOWED_HOSTS` 默认为空，保留当前各能力的精确目标/SSRF/trusted-LAN 规则；配置后仅允许逗号分隔的精确域名或 IP，不接受 wildcard、URL、空条目或 suffix 匹配。它在 HTTP 的 DNS/发送前执行，不含密钥，不自动修改现有个人配置。所有实际需要的模型、来源、微信等 host 都必须包含，未列出的目标会不可执行。

这不会放宽能力本身的私网/协议限制，也不约束 MiniMax CLI 内部 HTTP。CLI 仍只允许固定命令/参数、已有本机配置及有界隔离子进程。统一 HTTP 策略的预算按能力区分，聊天最多 120 秒、生图 25 秒，不使用抓取的 10 秒限制代替生成预算。实际供应商 grant/生产 Secret Provider 需要未来单独验收。
