# 发现

- MiniMax 现走本机 `mmx` CLI（`minimax_cli_provider.py`）：凭证在 `~/.mmx/config.json`，平台只读它做凭证指纹；`model_registration.py:193` 注释明确「shown here but never saved here」。
- mmx 支持全局覆盖参数 `--api-key` / `--base-url`（覆盖区域）/ `--region`（global/cn），`mmx --help` 已确认。
- `_run_bounded` 的子进程环境白名单是刻意的安全约束（不继承无关密钥），凭证走 argv 不动环境。
- 启用开关现写在 `apps/api/scripts/startup/runtime.env` 的 `AICS_ENABLE_MINIMAX_CLI=1`。
- 「CPA」是已注册 OpenAI-compatible 厂商卡片的代称（`cpa_image_provider.py`、路由设置里的「HTTPS 或本机 CPA 地址」）。
- 用户遇到的 understand_image「invalid api key」来自 Harness MCP 的 MiniMax Key，与平台存储分离，本次不改（proposal 已注明范围外）。

- 2026-10-28 实现发现：
  - mmx 在 API 报错时 rc 可能仍为 0，错误藏在 JSON `error.message`；rc!=0 时也可能打 JSON——测试逻辑两条路都剥壳再映射（invalid api key/login fail/api secret/authorization→Key 无效；timeout→连接超时；could not determine region→提示选区域）。
  - 只给 Key 不给区域时 mmx 报「Could not determine the API key region」，页面有区域下拉兜底。
  - `model_registration.endpoint()` 只验 URL 形状，http+私有地址的拦截要另用 `trusted_literal_address`（真机验证抓出 metadata 地址被放过，已修）。
  - 凭证走 argv 不动 `_run_bounded` 的环境白名单；启动顺序 `load_from_db` 先于 `bootstrap_media_providers`，页面配置对 bootstrap 可见，PUT 后再跑一次 bootstrap 即可热生效。
  - 本机 mmx 登录的 Key 已失效（quota show 报 invalid api key），页面现在可以直接换新 Key，不用去终端。
