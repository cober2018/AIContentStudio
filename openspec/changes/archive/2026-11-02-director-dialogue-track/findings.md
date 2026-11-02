# findings

- 作品 93 最新导演稿只有 1 条 video 轨（8 段）；shot-5、shot-6 的口播来源只写在 board.sound 文字里；素材 455 时长 10166ms，在外部素材库。
- video_documents：timeline 轨类型 video/audio/subtitle/overlay/music；audio/music 段必须带素材，可带 trim_start/trim_end、volume；_expected_media 已把所有带素材的时间线段登记为 timeline_media → 进入导演稿素材引用 → creative_packages 开剪素材包 → web_video_handoff.validate_edit_manifest 按素材包核对。
- 缺：dialogue 轨类型、script_block_id、同轨不重叠、截取不超素材时长（需查库）、页面显示、剪辑做法说明。

## 实现时的发现（2026-11-03）
- 页面保存路径（content_masters.save_revision）对 timeline_media 按轨类型限定素材种类，未知轨类型是空集合；dialogue 轨必须补成 音频/视频，否则 .mov 口播素材会被拒（已补）。
- 开剪素材包（creative_packages → source_asset_refs）、准备素材（materialize_inputs）、剪辑清单核对（validate_edit_manifest）都按整份素材引用走，不按轨类型过滤，声音轨素材不需要改就能进入并被核对。
- 格式错误的提示：VideoDocumentError 以「代码：说明」写出，MCP 走 video_chain_draft_invalid 原样带给模型；查库的问题在 video_chain._save 先查，用 video_chain_dialogue_material_invalid 带说明（save_revision 自己的 video_ 开头代码在 MCP 只露代码，不露说明）。
- 页面保存同样查库，拒绝代码 video_dialogue_material_invalid + message。
- 素材时长未记录时用 voiceover._clip_ms 读文件；读不到就跳过时长检查（剪辑时以实片为准）。
- 现有 100 份 video.master.v2 重新规范化后与库里一致，旧哈希不变。
- 验证环境：配乐 354 在对象存储，本 shell 没有存储设置，验证脚本只对 354 跳过字节检查；455 等其他素材都真实校验。
