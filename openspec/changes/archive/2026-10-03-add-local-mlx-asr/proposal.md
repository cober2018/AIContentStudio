## Why

用户已确认内容中心仅在本人电脑使用，字幕识别优先本机运行。FinanceOpinionRadar 已有 MLX Whisper 子进程桥接；复用它可以避免云端视频上传和 ASR 付费调用，同时补齐 Studio 现有字幕建议到 Video Master 的真实产品验收。

## What Changes

- 注册本机 `local.mlx_whisper@1` ASRProvider，移植 Radar 的最小识别桥接逻辑，复用 voice-pro 既有环境/缓存模型，不复制采集、观点、业务表或整套运行系统。
- Production 字幕面板优先选择本机识别，明确本地/云端及可用原因；MiniMax 保留为显式可选引擎，本地失败绝不自动发送到云端。
- 仅处理正式素材库中已保存 Master 精确引用的音频/视频。本机视频先提取音轨；返回带毫秒时间码的段级字幕，校对/接受仅改本地草稿，显式 Save 才持久化。
- 为本机 ASR 设置服务端受限的等待/进程截止时间，保留其他 Provider 的 30 秒等待及既有输入、权利、权限、receipt/CAS 与 Unknown 边界。
- 按两批完成后端/接入和真实页面/回归验收，不增加业务表、migration 或 Studio 模型依赖。

## Capabilities

### New Capabilities

- `local-asr-subtitles`: 本机 MLX 识别、离线执行、安全有界进程、精确来源、人工字幕保存和本地优先/显式云端选择。

### Modified Capabilities

无已有 canonical requirement 删除或替换。新契约在现有 Registry、ASR 建议和 Master 不变量之上加法扩展；F7 路由/消费者仍沿用各自未完成验收，不因此宣告全关。

## Impact

- API：复用 `/asr-provider-options` 与 unit/master-scoped `/asr-suggestions`，加安全标签/本地模式/可用原因，不接受客户端 executable、路径、命令或超时配置。
- 代码：新增最小 `apps/api/app/services/local_mlx_asr_provider.py`；限定修改 Registry 初始化、`asr_suggestions.py`、`provider_calls.py`、相关安全配置/模型能力 descriptor 和 `AsrSuggestionPanel.tsx`。
- 运行：沿用现有 API/Worker、ffmpeg/ffprobe 与 voice-pro 的 ARM Python/MLX worker/模型缓存；apply 后显式本地 opt-in，不自动安装或下载。
- 数据：复用 MaterialRevision / Project refs / ASR receipt / append-only Master；零新增表、零 migration，公开/模型/商业许可不自动授权。
- 本轮仅提案与规格/计划复核，不修改业务代码、不调用模型、不写正式配置、不迁移/提交/推送/部署。完整 OpenSpec 产出后需用户单独确认 apply；新付费素材生成接受不是本 change 的义务。
