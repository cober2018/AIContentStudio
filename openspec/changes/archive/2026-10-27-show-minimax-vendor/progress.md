# 进度

- 2026-10-28 写好方案，等用户确认。
- 2026-10-28 实施：`minimax_cli_provider.vendor_status()` 读 mmx 版本、启用开关、区域和密钥掩码（复用安全读取与 `mask_secret`）；`configuration_view` 附 `local_vendors.minimax`（含用途：一键配音，生图选 MiniMax 时加 AI 生图），读和保存后的返回都带；页面在 CPA 下方显示只读卡片。改动放在 `model_registration.py` 而不是路由里，这样保存后返回的数据也带 MiniMax，卡片不会消失。
- 验证：接口返回 `mmx 1.0.27 · 已启用 · 区域 cn · 密钥 sk-••••kN7w · 用于 一键配音、AI 生图`，响应里不含完整密钥；无界面浏览器打开设置 → 模型与 AI → 厂商与模型，CPA 和 MiniMax 两张卡都在；相关后端测试 402 通过；ruff 无新增问题；`tsc --noEmit` 通过。
