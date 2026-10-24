## Roles

- Platform: tools, storage, versions, review pages, the standard folders. No model call in the video chain.
- External model (Claude Code via MCP): every creative decision in the video chain.

## States the page shows

`待开始` → `导演稿待你看`（含素材需求） → `制作中` → `小样待你看` → `排版中` → `成片待你看` → `已完成`. Each "待你看" waits for the user's decision on the page; Claude Code reads it with an MCP call and continues only after 采用 / 通过. Notes are timecoded and become the next version.

## MCP tools (new)

| Tool | Does |
| --- | --- |
| `get_video_brief` | Project brief, facts, voice settings, library and project materials (titles, kind, duration, tags, folder) |
| `save_director_draft` | Validates and saves a `video.master.v2` (shots with board, script blocks) plus a per-shot material request (`board.material_request`: must show, shot size, length, footage / graphic, orientation); returns the review URL; state 导演稿待你看 |
| `get_draft_decision` | The user's decision and notes on the 导演稿 / 小样 / 成片 |
| `set_shot_material` | Put a library material on a shot (adds the project reference) |
| `search_materials` | Existing library + stock search (platform search tools), returns candidates; nothing attached automatically |
| `generate_image` | Existing image generation; result stored in the project folder |
| `generate_voiceover` | Existing `voiceover.generate` with the saved MiniMax settings; returns duration and per-line timing |
| `prepare_edit` | Records the DaVinci / AE decision per shot and creates the edit task: phase `rough_cut` (小样) first, `final` (排版 + 成片) after 小样 is approved |

Existing execution tools (claim, materialize, submit, request review) stay as they are.

## 小样 → 排版 → 成片

- 小样: phase `rough_cut`; outputs as today; copied to 导出/小样.
- 成片: a second task, phase `final`, with `parent_material_revision_id` = the approved 小样; Claude Code does 排版 (caption / title layout, packaging graphics, colour and sound polish) and exports; result moves to 导出/成片 when accepted.

## Removed from video

`CreationRecipePanel` 生成导演稿 / 重新生成, `start_material_autofill` button, `edit_handoff._decide_ae` model call, auto voice button stays only as a page action that runs the same tool (no model).

## Rights

- Create paths (upload, Finder drop, link, generated, web stock): `public_use_allowed = model_use_allowed = True`, `rights_status` kept, attribution kept.
- One-off: set both flags True on all active materials; keep attribution text. Then run `material_dedupe.merge`.
- Edit receipt / credits list the attribution of web materials used.

## Material request

- Shown on the page as a column of the storyboard table and as a list the user can copy.
- When the user approves the 导演稿, Claude Code lists library / project files added since the request (`get_video_brief`), matches them to rows, then covers the rest itself: library → stock search → image generation → AE template. The receipt says which rows came from the user and which were found or made.

## Production tools

小样 and 成片 are built as a DaVinci Resolve project (timeline, colour, sound, export) with After Effects compositions for titles, captions, packaging and effects, as in the existing `resolve-edit` and `ae-motion` craft skills. ffmpeg only for checks and container fixes.
