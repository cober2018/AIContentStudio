# MiniMax 厂商设置页可配置

- 阶段：已完成并归档（2026-10-28）
- 结果：「模型与AI → 厂商与模型」的 MiniMax 卡片可配置——API Key（掩码保存/清除）、访问地址（https 或本机/局域网）、区域、启用开关（即时生效）、测试按钮；页面值优先，未保存回退本机 mmx 登录与启动开关。
- 代码：`apps/api/app/services/minimax_cli_provider.py`（存储/覆盖参数/vendor_status/save/test）、`apps/api/app/routers/settings.py`（PUT/POST minimax 端点）、`apps/web/src/product/ModelRegistrationSettings.tsx`（MiniMaxVendorCard）。
- 验证：前端 tsc/tests(37)/build 过；后端相关 75 tests 过；真机 curl 全链路含安全规则验证。详见 progress.md。
