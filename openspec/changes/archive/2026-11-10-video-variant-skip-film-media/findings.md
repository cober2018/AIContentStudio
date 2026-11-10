## 2026-11-10 422 原因
- 作品 97 主稿 #284（v7, video.master.v2）挂了 44 个 shot_source，加 voice_audio、music_audio、cover_image ×2、postproduction_parent。
- `_video_source_refs` 遇到任何非 shot_source 就报 `video_source_media_requires_explicit_mapping`（2026-09-29 提交 6a978d8 引入，当时主稿只有镜头画面）。
- 库里 216 个视频主稿版本带非镜头用料，都会触发。
- 修完第一处后，用户界面上又报 `video_media_or_timing_requires_explicit_mapping`：`channel_adapters.py` 的口播脚本生成器有同样假设（有配音、字幕、配乐、封面就拒绝）。
- 接着是 `script_scene_mapping_incomplete`：97 的片尾 shot-43 没有旁白；另外 97 有 44 镜、32 句旁白，一镜一段会让同一句重复。改为按旁白分段。
- 本地排查时一度看到「156 个 AE 渲染片段文件都不存在」，是脚本没加载素材库位置设置（runtime_config.load_from_db）造成的误判，文件都在。
