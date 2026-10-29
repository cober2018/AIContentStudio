## Why

设置 →「厂商与模型」只列出平台自己保存密钥的厂商（现在只有 CPA）。MiniMax 实际在用（视频一键配音走本机 MiniMax 命令行 `mmx`，AI 生图也可选 MiniMax），但它的账号存在 `mmx` 自己的配置里，列表里看不到，用户以为没接上。

## What Changes

- 「厂商与模型」列表里加一行 **MiniMax（本机命令行）**，只读显示：
  - 状态：命令行是否已安装（版本号）、平台是否已启用 MiniMax（`AICS_ENABLE_MINIMAX_CLI`）、账号是否已登录。
  - 账号：区域（如 cn）、密钥掩码（与 CPA 相同的「前 3 后 4」格式，不显示明文）。
  - 平台里用到它的地方：一键配音；AI 生图选了 MiniMax 时也写明。
- 不能在这里改 MiniMax 账号：账号由本机 `mmx` 管理，页面写明「在终端用 mmx 登录或换账号」。
- 不改 MiniMax 的调用方式，不改 CPA 的显示和保存。

## Impact

- API：`GET /settings/model-registration` 的返回里加只读 `local_vendors.minimax`（读取复用 `minimax_cli_provider` 的安全读取，只返回区域和掩码）；保存接口不变、忽略这个字段。
- Web：`ModelRegistrationSettings.tsx` 在厂商列表里显示这一行只读卡片。
