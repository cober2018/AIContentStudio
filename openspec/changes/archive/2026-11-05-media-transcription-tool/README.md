# media-transcription-tool

## 需求背景
用户常需要把音视频转成文字、字幕、md 笔记（文字配截图）。平台已有本机转写但只在参考视频拆解里用；用户决定做成独立小工具，通过 MCP 执行，导航加「小工具」页。详见 proposal.md。

## 当前阶段
2026-11-05 用户确认，代码已改、真实文件副本验证和测试通过；已重启生效、页面截图正常；待第三方模型实调。2026-11-05 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services/{media_transcription,creative_mcp,mcp_settings}.py、新路由；apps/web/src/App.tsx、新页面

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
第三方模型重连后实调一次；推送等用户说「推送」。
