## 读取

- 版本：`mmx --version`（`minimax_cli_provider` 已有受限执行）。
- 账号：复用 `_read_cli_config()` 的安全读取（不跟随链接、只读本人且权限 600 的文件），只取 `region` 和 `api_key` 的掩码（`system_settings.mask_secret`），明文不出这个函数。
- 启用：现有 `AICS_ENABLE_MINIMAX_CLI` 运行配置。
- 用途：配音固定用 MiniMax；AI 生图读现有生图设置，provider 为 minimax 时列出。

## 显示

列表里与 CPA 并列，标「本机命令行 · 只读」，没有编辑和删除按钮；未安装 / 未登录时写明原因和处理方式。

## 不做

- 不在平台保存或修改 MiniMax 密钥。
- 不把 MiniMax 改成平台 HTTP 厂商。
