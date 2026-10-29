# 进展

- 2026-10-28 实现完成并验证：
  - `minimax_cli_provider.py`：`SETTINGS_KEY="minimax_vendor"` 页面配置（enabled/api_key/base_url/region，页面优先、env 回退）；`_run()` 认证类调用统一拼 `--api-key/--base-url/--region` 覆盖参数，`--version/--help/dry-run` 不带；`vendor_status()` 增 `key_from`/`base_url_configured`，掩码回显；`save_settings()`/`test_vendor()`。
  - `routers/settings.py`：`PUT /settings/model-registration/minimax`（保存后重跑 bootstrap，启停即时生效）、`POST .../test`（to_thread）。
  - 前端 `ModelRegistrationSettings.tsx`：MiniMax 卡片改为可编辑（启用、Key 保存/清除、地址+区域、测试），`MiniMaxVendorCard` 子组件。
- 验证：前端 tsc/37 tests/build 全过；后端相关 75 tests 过；真机 curl 全链路：假 Key→「Key 无效或没有权限」；坏区域 422；`http://169.254.169.254` 422（补了与注册厂商一致的 http 仅限本机/局域网规则，最初漏掉、真机验证抓出）；`http://127.0.0.1` 放行；启停开关即时生效；清除后回退本机 mmx 登录（其 Key 当前已失效，测试如实报 Key 无效）。
