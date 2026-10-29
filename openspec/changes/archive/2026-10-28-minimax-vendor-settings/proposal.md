# MiniMax 厂商设置页可配置

## Why

「模型与AI → 厂商与模型」里，MiniMax 是一张只读卡片：API Key 由本机 mmx 命令行登录持有，启用开关写死在启动配置（`AICS_ENABLE_MINIMAX_CLI=1`），页面上既不能换 Key、也不能填访问地址。用户要求它和上面的 CPA 等已注册厂商一样可配置：能填 API Key、访问地址、启用开关，改完即生效，不用去终端操作 mmx。

## What Changes

- 后端新增 MiniMax 厂商配置存储（复用 stock-sources 的 system_settings 模式）：启用开关、API Key、访问地址、区域；Key 只以掩码回显，页面保存优先，未保存时回退本机 mmx 登录与启动配置。
- 平台调用 mmx 命令行时，页面保存的 Key / 地址 / 区域以 mmx 全局参数（`--api-key` / `--base-url` / `--region`）传入覆盖；页面没存则维持现状（用 mmx 自己的登录）。
- 「厂商与模型」页的 MiniMax 卡片从只读改为可编辑：启用开关、API Key 保存/清除（掩码回显 + 来源标识）、访问地址、区域、测试按钮（调 `mmx quota show` 验证）。
- 能力目录 `model-vendors` 的「MiniMax 只读」规格同步修改。

## Impact

- 受影响：`apps/api/app/services/minimax_cli_provider.py`（配置读取、_run 传参、vendor_status）、`model_registration.py`（local_vendors 视图）、`apps/api/app/routers/settings.py`（保存/测试端点）、`apps/web/src/product/ModelRegistrationSettings.tsx`（卡片可编辑）。
- 不变：一键配音、AI 生图、视频生成等功能的调用链路不变，只换凭证来源；mmx 未安装时的行为不变。
- 范围外：Harness（MCP）侧的 MiniMax Key 是另一处配置，本次不改。
