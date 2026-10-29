# 设计

## 存储

- `system_settings` 新增 `SETTINGS_KEY = "minimax_vendor"`，结构：

```json
{"enabled": true, "api_key": "…", "base_url": "https://…", "region": "global|cn"}
```

- 读取优先级：页面保存值 > 现状回退。`enabled` 未保存过时回退 `AICS_ENABLE_MINIMAX_CLI`；`api_key`/`base_url` 未保存时为空，调用时回落到 mmx 自己的登录凭证。
- 复用 open_media 的保存/校验/掩码模式：省略 `api_key` 字段保持现值，空串清除；`runtime_config.validate_persisted_configuration` 校验；读取只回 `mask_secret`。

## 调用链

- `minimax_cli_provider` 增加模块级 `page_config()`，各处 `_run()` 前统一拼全局参数：存了 Key 加 `--api-key`，存了地址加 `--base-url`，存了区域且没存地址加 `--region`（mmx 文档：`--base-url` 覆盖区域）。
- 不通过环境变量传凭证：`_run_bounded` 的环境白名单是刻意收紧的（防止混入无关密钥），保持不动；参数走 argv。
- `bootstrap()` 的安装检查不变，`enabled` 判断改为「页面值优先，env 回退」。

## 视图与端点

- `vendor_status()` / `_minimax_view()` 增加：`key_from`（`page` | `cli`）、`base_url_configured`、`enabled`（页面值优先）；掩码 Key 保留。
- `PUT /api/v1/settings/model-registration/minimax`（admin）：保存/清除，`base_url` 复用 `model_registration.endpoint()` 校验（https、公网、无凭据），`region` 枚举。
- `POST /api/v1/settings/model-registration/minimax/test`（admin，`asyncio.to_thread`）：带覆盖参数跑 `mmx quota show`，返回 `{ok, elapsed_ms, reason}`；失败原因映射：鉴权拒绝→「Key 无效或没有权限」，超时→「连接超时」，其余→原文原因。不回显 Key。

## 前端

- `ModelRegistrationSettings.tsx` 的 MiniMax 卡片改为可编辑，样式对齐上方厂商卡片：启用开关、API Key（掩码回显 + 来源「本页保存」/「本机 mmx 登录」、保存/清除）、访问地址（选填）、区域下拉（global/cn）、测试按钮与结果文案。
- 保存走独立 PUT，不占用厂商与模型整页的 revision；卡片状态徽标沿用「未安装 / 已启用 / 未启用」。
