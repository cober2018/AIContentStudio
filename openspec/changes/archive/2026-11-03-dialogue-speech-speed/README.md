# dialogue-speech-speed

## 需求背景
实拍口播作品要能在「配音与音乐」用滑块统一调口播语速（作品 94 先用约 1.15 倍），配乐不变速。详见 proposal.md、design.md。

## 当前阶段
2026-11-03 用户「确认」，实施并核对通过；已重启；按 review.md 修了 MCP 说明和 tasks.md。2026-11-04 已归档、已提交（未推送）。修正后的 MCP 说明要再重启接口才生效。

## 代码位置
apps/api/app/services/{video_documents,voiceover,video_chain,creative_mcp}.py、apps/api/app/routers/edit_agent.py、apps/api/craft_skills/craft-resolve/techniques/sound.md、apps/web/src/product/{VoiceoverPanel,StoryboardTable}.tsx、VideoStudioModel.ts

## 下一步
无（推送等用户说「推送」；审计的可选建议未做）。
