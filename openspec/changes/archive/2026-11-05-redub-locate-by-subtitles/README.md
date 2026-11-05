# redub-locate-by-subtitles

## 需求背景
作品 95 只重配 line-33 时被 `voiceover_line_split_unclear` 拒绝：没有逐句时间时按字数比例分句分错了。改成先按导演稿字幕定位。详见 proposal.md。

## 当前阶段
2026-11-05 用户确认，已实现、库副本验证和测试通过，已重启生效；2026-11-05 已归档、已提交并推送；作品 95 line-33 已真实重配（配音 580），用户试听确认「去重」读 chóng。

## 代码位置
apps/api/app/services/voiceover.py

## 成果文件
proposal.md、specs/、tasks.md、task_plan.md、progress.md、findings.md

## 下一步
无。
