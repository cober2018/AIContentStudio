## Why

The 海底光缆 cut looks cheap. The root cause is upstream: the 导演稿 is written by the platform's own model in one batch, materials are filled by platform autofill, and the AE decision is another platform model call. The editing model can only fill in a weak plan.

The user's decision: **articles and images keep the platform's abilities; video is led end to end by the external model the user is working with** (today Claude Code), through the platform MCP. The platform provides tools, keeps records and shows things for review; it does not make the creative decisions for video.

## What Changes

**The video chain, run from Claude Code** (started by the user in the conversation, e.g. 「做海底光缆的视频」, the same way as 「剪这条」):

| Step | Who decides | Stop for the user |
| --- | --- | --- |
| 1. 导演稿 (storyboard 9 columns, narration, 景别 / 运镜, sound, notes) **with a material request per shot** (what the picture must show, shot size, length, real footage or graphic, landscape / portrait) | Claude Code writes both from the project's brief, facts and library; saved through MCP | **Yes**: the user reads the 导演稿 and the material request, says 采用 or gives changes, and puts the footage they have into the library (外部素材库 or the project) |
| 2. Materials per shot | The user supplies what they can. For rows still missing, Claude Code finds or makes them (library, stock search, image generation, AE templates). Claude Code picks the material for every shot. All through platform tools. | No |
| 3. Voiceover | Claude Code calls the platform MiniMax tool with the saved voice settings | No |
| 4. DaVinci vs AE per shot | Claude Code | No |
| 5. **小样** (cut, timing, voice, basic captions) | Claude Code, made in **DaVinci Resolve and After Effects** | **Yes**: the user reviews 小样 on the page (timecoded notes or 通过) |
| 6. **排版** (caption and title layout, packaging graphics, colour and sound polish) then **成片** | Claude Code, made in **DaVinci Resolve and After Effects** | **Yes**: final review |

- **Tools:** 小样, 排版 and 成片 are produced in DaVinci Resolve and After Effects as far as possible (cut, colour, sound in Resolve; titles, captions, packaging, effects in AE). Code-drawn frames or ffmpeg are used only for checks and format conversion, not for the look.
- **Material request:** after the user replies, Claude Code reads what was added (MCP), matches it to rows, and reports which rows it will cover itself and how.

Files go where the standard folders say: 导演稿/, 视频/…, 图片/…, 音频/…, 导出/小样, 导出/成片.

- **Rule: the edit follows the 导演稿.** If picture content has to change while editing, Claude Code saves a new 导演稿 version first, then edits. Details the 导演稿 does not specify (trim points, timing of a move, caption placement) are listed in the edit receipt so the user can see them at review.
- **New MCP tools** so Claude Code can do steps 1–4 without platform models: read project brief / facts / library; save the 导演稿; pick a material for a shot; search materials; generate an image; generate the voiceover; record the DaVinci / AE decision and prepare the edit task (小样, then 成片).
- **Video pages stop calling platform models:** 生成导演稿 / 重新生成 / AI 补齐素材 and the automatic AE decision are removed from video; the page shows the 导演稿, progress, 小样 and 成片, and keeps review and feedback (采用, timecoded notes, 通过). It tells the user to start in Claude Code when nothing is there yet.
- **Rights default to allowed:** every material in the library can be edited by AI and published. Existing materials missing these permissions get them. Web-found materials keep their source credit (e.g. 「Video by xxx from Pixabay」), shown in the edit receipt / credits. Afterwards the 7 duplicate groups left by the last change (only their rights differed) are merged.
- Articles and images: unchanged.
- After this is in place, 海底光缆 is redone with the new chain, starting from a new 导演稿.

## Impact

- API: new MCP tools in `creative_mcp.py` (+ matching services: save master through `content_masters.save_revision`, shot pick through `shot_slots`, image generation and voiceover through existing services, postproduction decision and `web_video_handoff.prepare_edit` for phase `rough_cut` → `final`); `edit_handoff` no longer calls a model for the AE decision; rights defaults in the material create paths plus a one-off update; dedupe re-run.
- Web: video branch of `CreationRecipePanel` / `StageProposalReview` / `ProductionWorkspace` without the platform-model buttons; a status / review view for 导演稿 → 小样 → 成片.
- Skills: `video-production-handoff` and craft skills describe the chain and the 「edit follows the 导演稿」 rule for Claude Code.
