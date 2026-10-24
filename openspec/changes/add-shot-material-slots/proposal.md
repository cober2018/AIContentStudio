## Why

The user wants to look for, generate and upload footage while producing a video, shot by shot, guided by what each shot says and shows (2026-10-22). Today:

- the shot plan has narration, a visual description and asset requirements, but no search words or generation prompt;
- the video draft already gives every shot a material slot (bind a material, or generate it from an image or web-video prompt), but the slot does not show the shot's brief or a clear status;
- picks made in the 素材库's match runs for this piece (e.g. runs 6–10 for U80) never reach the shot slots, so the user ends up collecting everything in the library first.

Agreed principle (2026-10-22): **the platform fixes outcomes, not steps.**
- AI proposes and does the work, the user judges and decides, and the platform records and shows the result.
- The platform guarantees sources, rights, the user's decision and a trail.
- It does not dictate step order, tools or where material comes from.

## What Changes

- **Shot brief:** every shot in the plan and in the video draft carries:
  - narration and on-screen visual (both already present);
  - search words, in Chinese and English;
  - a generation prompt;
  - the suggested route: find, generate, or platform-drawn (maps, numbers, text cards).

  The shot-plan step writes these. Older plans fill them in when the slot is first opened. All of them can be edited.
- **Shot = slot that takes any source.** On the video production page each shot shows its brief and a status: 缺素材 / 有候选 / 已选定. Any source can add to it at any time:
  - a platform search (own library first, then free libraries), which already exists as the AI 创作助手「找素材」;
  - picks and uploads from this piece's match runs in the 素材库, shown as candidates of the shot with the same id;
  - an upload straight onto the shot, with rights fields;
  - the existing generation routes (image API, web video prompt, AE).

  A shot can keep several candidates. Choosing one binds it as the shot's source through the normal draft save.
- **Missing material does not block work:** drafting, narration, subtitles and editing continue with empty slots. Only the steps that truly need every shot keep requiring it (web-video handoff and final render). They say which shots are missing.
- **Agents read and propose, never bind:** one read-only MCP tool, `get_shot_slots`, returns each shot's brief, status, candidates and the user's choice, with a review link. Agents add candidates through the existing `start_material_match`. Binding stays the user's action on the platform.

- **Two prompts per shot** (added 2026-10-22 at the user's request):
  - a first-frame image prompt, for the still that opens the shot;
  - a video prompt that animates that frame: motion, camera movement and pace, without re-describing the picture.

  Together they match the platform's existing image-then-video route. The 「API生成图片」 route shows the frame prompt to copy, because the native image generator is one panel per piece rather than per shot, and 「网页生成视频」 pre-fills the video prompt. Existing briefs get both from the planner-only brief call.

## Capabilities

### New Capabilities

- `shot-material-slots`: per-shot brief (narration, visual, search words, prompt, route), shot slots that collect candidates from every source with a status, and an agent read view.

## Impact

- **API:**
  - shot-plan output and video shot schema gain optional brief fields;
  - a slot read endpoint per unit (draft shots + this unit's match-run picks/uploads by shot id);
  - shot upload reuses the material upload and match attach;
  - MCP gains `get_shot_slots` (read-only).
- **Web:** video production page (`VideoStudioShell`, `VideoShotMaterialPanel`, `ShotMaterialFinder`) gets the per-shot brief, status and candidate list, plus an upload button.
- **Not changed:**
  - material rights and acceptance path;
  - draft save and binding rules;
  - stage acceptance;
  - handoff and render checks, except clearer missing-shot messages.
