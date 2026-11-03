# 审计：导演稿声音轨

审计时间：2026-11-03；代码版本 0d03d1e。

## 结论：通过

| 需求 | 实现 |
|---|---|
| 导演稿可加一条 dialogue 声音轨，段可跨镜头 | `video_documents._dialogue_item`，段不挂 `shot_id`，最多一条轨 |
| 保存时检查：素材存在可用、不超出素材长度、在成片时长内、不重叠 | `dialogue_material_problems`、`_dialogue_item`、`_dialogue_overlaps`，报错写明是哪一段 |
| 声音轨素材进开剪任务 | 声音段生成 `timeline_media` 引用，随导演稿进任务包；剪辑清单按包内素材核对 |
| 页面显示每句台词的声音来源 | `StoryboardTable` 的 `SoundSource` / `UnlinkedSegments` |
| craft-resolve 补衔接做法 | sound.md「声音轨口播衔接」 |

## 可选建议（不阻塞）

- sound.md 写「每个接缝两边各加 2–4 帧淡入淡出」。作品 93 小样实测：一段从 7.733 秒起、字头在 7.76 秒，2 帧淡入吃掉了「每」字。建议改成：淡变只落在停顿里，切点离字头不到 3 帧时用 1 帧。这一条最初是审计方自己写进需求的，实际剪下来要收紧。
