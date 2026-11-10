## Why
视频交付页的「渠道变体」（如抖音口播脚本）点「生成确定性预览」报 422 `video_source_media_requires_explicit_mapping`。原因：这条检查是 9 月写的，当时视频主稿只挂镜头画面；后来视频流程把配音、配乐、横竖封面、小样也挂到主稿上，检查看到镜头画面以外的东西就整体拒绝。库里 216 个视频主稿版本都带这些东西，所以做到成片的视频全部卡在这里，不只是作品 97。

## What Changes
- 口播脚本变体只取主稿里的镜头画面（逐镜对应），配音、配乐、封面、小样、成片这些属于成片本身的东西不带进变体，也不再因为它们拒绝。
- 镜头画面和导演稿镜头对不上时，照旧报 `video_source_b_roll_mismatch`。
- 口播脚本生成器（`VideoSpokenScriptAdapter`）同样不再因配音、字幕、叠层、配乐、封面、成片拒绝（原报 `video_media_or_timing_requires_explicit_mapping`），它只读台词和镜头。
- 一句旁白一段：连续共用同一句旁白的镜头合成一段，画面都挂在这段里；没有旁白的镜头（如片尾卡片）接在前一段，不编台词。原来一镜一段，同一句会重复出现。

## 不做
- 不改变体的内容和保存规则；不改交付页界面。

## Impact
- apps/api/app/services/channel_variants.py：`_video_source_refs` 一处
- apps/api/app/services/channel_adapters.py：`VideoSpokenScriptAdapter.adapt`
- apps/api/tests/test_f6e_video_script_adaptation.py：原来断言「有字幕就拒绝」的用例改成断言能出预览
