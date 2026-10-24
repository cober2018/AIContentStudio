## Why

用户规则（2026-10-24）：平台页面上不写「Claude Code」，外部经 MCP 接入的模型统一叫「第三方模型」。写作开关已按此命名；视频流程页面和两条后端提示还写着 Claude Code。用户确认一并改。

## What Changes

把制作流程中给用户看的文字里的「Claude Code」改成「第三方模型」：
- 视频进度面板（小样 / 成片意见提示、「回到…说一声继续」）
- 分镜表说明、逐镜素材页和背景音乐页的提示
- 视频「待开始」状态说明（后端）、剪辑交接里「哪些镜头用 AE」的提示（后端）

不改：设置页里配置具体客户端的说明（MCP 接入命令的「Claude Code」标题、剪辑助手选择 Claude / Codex），那里是在说具体工具。

## Impact

Web：`VideoChainPanel.tsx`、`StoryboardTable.tsx`、`VideoMaterialSteps.tsx`；API：`services/video_chain.py`、`services/edit_handoff.py`。只改文案。
