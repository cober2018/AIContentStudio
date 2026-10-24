## 1. MCP tools

- [x] 1.1 `get_video_brief`, `save_director_draft` (with per-shot material request), `get_draft_decision`; material request column on the page.
- [x] 1.2 `set_shot_material`, `search_materials`, `generate_image`, `generate_voiceover`.
- [x] 1.3 `prepare_edit` with per-shot DaVinci / AE decision; phase `rough_cut`, then `final` after 小样 approval.

## 2. Platform stops deciding for video

- [x] 2.1 Remove the AE model call from `edit_handoff`; remove 生成导演稿 / 重新生成 / AI 补齐素材 from video pages.
- [x] 2.2 Page states 待开始 → 导演稿待你看 → 制作中 → 小样待你看 → 排版中 → 成片待你看 → 已完成, with review actions.

## 3. Rights

- [x] 3.1 Defaults on create paths; one-off update; merge the remaining duplicate groups.

## 4. Skills

- [x] 4.1 `video-production-handoff` and craft skills: the chain, stops, material request, user material first then find / make, Resolve + AE for 小样 / 排版 / 成片, 「edit follows the 导演稿」, receipt lists unspecified details, material origin and credits.

## 5. Redo 海底光缆

- [x] 5.1 海底光缆 redone: 导演稿 v13 → v17 → 小样 #8, #9 → 成片 #10 approved by the user.
- [x] 5.2 Tests for the changed paths; docs.
