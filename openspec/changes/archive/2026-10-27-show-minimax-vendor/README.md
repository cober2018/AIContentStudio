# show-minimax-vendor

**阶段：** 已本地实施并验证，2026-10-28 归档；未提交 Git。

**做什么：** 设置「厂商与模型」里只读显示 MiniMax（本机 mmx 命令行）的安装、启用、区域、密钥掩码和用途。

**代码位置：** `apps/api/app/services/minimax_cli_provider.py`（`vendor_status`）、`app/services/model_registration.py`（`configuration_view` 返回 `local_vendors.minimax`）；`apps/web/src/product/ModelRegistrationSettings.tsx`（只读卡片）。

**下一步：** 无。
