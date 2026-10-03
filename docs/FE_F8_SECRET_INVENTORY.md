# FE-F8 本机配置密钥盘点

日期：2026-10-03

范围：当前本地 SQLite `SystemSetting` 行。此文档只记录键名和分类，不记录任何值、密钥、URL 凭据或 token。

## 盘点结果

- 总行数：6
- 含 secret-bearing 字段的行：3
- 不含 secret-bearing 字段的行：3
- 当前键名：`dsh`、`image`、`llm`、`models`、`plugins`、`wechat.official.account.1`

检测沿用 `runtime_config.contains_plaintext_secret()`，覆盖嵌套字段、带凭据 URL 和签名/令牌参数；仅返回布尔分类，不回显字段名或值。

## 本机正式验收决策

本轮基准是本机 SQLite + 本地素材库，未授权替换个人凭据、迁移外部 Secret Provider 或启用 production auth。因此不删除、不改写这 3 行，不把 masked projection 当成已完成迁移。

生产 profile 的前置条件已经写死：启动/ready 必须拒绝 plaintext override，迁移前由操作者逐项替换为环境变量或 Secret Provider 引用，并重新盘点；盘点未清零时不得宣称 production-ready。当前只关闭“盘点与阻断规则”证据，生产 remediation 仍是后续部署工作。
