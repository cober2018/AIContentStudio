# fix-redub-voice-over-30mb

## 需求背景
单句重配（`generate_video_voiceover` 带 `lines`）把整条配音存成 WAV，片长超过约 4 分钟就超过素材 30 MB 上限，在 MiniMax 已经计费之后报 413 存不进去。详见 proposal.md，证据见 findings.md。

## 当前阶段
2026-11-08 已完成并归档（本地，未提交、后端未重启）。单句重配结果改存立体声 FLAC；超限在调 MiniMax 前报 `voiceover_redub_too_large`。验证见 progress.md。

## 代码位置
- 本次改动（未提交）：voiceover.py（`_flac`、`_too_large`、`_redub`）、materials.py（`_SIGNATURES` 加 fLaC）、creative_executions.py（`_INPUT_EXTENSIONS` 加 flac）、creative_mcp.py（工具说明）
- apps/api/app/services/voiceover.py：`_redub`（约 950–1065 行，`voice.wav` 写出和 `create_revision`）
- apps/api/app/services/materials.py：`validate_upload`（30 MB 上限）、`sniff_mime`（已识别 audio/flac）
- apps/api/app/services/creative_mcp.py：`generate_video_voiceover` 工具说明、413 → `creative_domain_bounds` 的映射
- openspec/specs/video-chain-led-by-mcp-model/spec.md：单句重配那条规格（约 148 行）

## 成果文件
proposal.md、specs/video-chain-led-by-mcp-model/spec.md、tasks.md、findings.md；开发方新建 task_plan.md、progress.md。

## 下一步
重启后端生效；制作方重配作品99 `line-26`；第一次真实剪辑时确认达芬奇导入 FLAC 配音正常。

## 依赖 & 启动
本地 API：apps/api（.venv，`scripts/startup/runtime.env`），日志在 logs/api.log。MiniMax 调用计费，验收用测试配音，不在作品上反复重配。
