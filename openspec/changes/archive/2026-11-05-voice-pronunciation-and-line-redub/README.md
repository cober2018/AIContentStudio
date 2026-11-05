# voice-pronunciation-and-line-redub

## 需求背景
作品 95 的「去重」被读错，平台没法指定读音；整条重配又让每句长短变了、和画面对不上。要支持指定多音字读音，以及只重配几句原位换进去。详见 proposal.md。

## 当前阶段
2026-11-05 用户确认（只换声音不用再通过）；代码已改、免费部分验证和测试通过；付费实配一次（ch 送气已见，声调待用户试听）；已重启生效。2026-11-05 已归档、已提交（未推送）。

## 代码位置
apps/api/app/services/{video_documents,voiceover,minimax_cli_provider,model_capability_routing,video_chain,creative_mcp}.py

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
用户试听 output/_平台/配音试听/去重-chong2-读音试配.mp3 确认声调；推送等用户说「推送」。
