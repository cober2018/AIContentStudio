# video-variant-skip-film-media

## 需求背景
作品 97 交付页「渠道变体」点「生成确定性预览」报 422 video_source_media_requires_explicit_mapping。详见 proposal.md。

## 当前阶段
2026-11-10 用户确认，已实现、测试、重启；未提交、未归档。

## 代码位置
apps/api/app/services/channel_variants.py `_video_source_refs`

## 下一步
用户在交付页点一次「生成确定性预览」确认；说「提交吧」再归档提交。
