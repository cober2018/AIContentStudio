## Why

Finding the right footage for a script is the slowest part of every video. Today the platform searches only Wikimedia, one query at a time; the agent and the user look for material beat by beat by hand. The user saw ScriptMate (github.com/zhangyiling108-code/scriptmate), which turns a script into per-segment material candidates with scores and licenses, and asked for the same ability inside the material library (2026-10-22).

ScriptMate has no license file, so its code is not reused. The platform implements the same method independently on its own contracts: materials, rights, revisions, model routing, outbound policies.

## What Changes

- **按文案找素材** in the 素材库: paste a script, or pick a project's accepted script or Master, choose aspect (9:16, 16:9, 3:4, 1:1, 4:3) and minimum resolution.
- **Plan**: a chat model splits the script into segments. Each segment gets:
  - its visual role: proof of a real thing, explanation, mood B-roll, or data/keyword card;
  - its subject constraints: country, subject, compared objects, time;
  - media type;
  - Chinese and English search queries.
- **Own material first**: each segment is matched against the user's own library, including linked drive folders, using title, tags, notes and attribution text. Only rights that allow model use are matched.
- **Open libraries**: Pixabay (user key), Internet Archive (no key, CC0 / public domain / CC BY items small enough to download), Openverse and NASA Images (no key; unreachable through the current proxy), beside the existing Wikimedia. Pexels is implemented but hidden: the user cannot obtain a key (2026-10-22).
  - A provider without a configured key is shown as off.
  - The default license allowlist is CC0, public domain mark, CC BY and each library's own license.
  - Unknown licenses are never shown.
  - Results are deduplicated by source page.
- **Score with reasons**:
  - A text pre-filter ranks candidates first.
  - A vision-capable model then checks the real thumbnail against the segment and its constraints, and records what it saw.
  - The score breakdown covers meaning, technical fit (aspect, resolution, duration) and own-library match.
  - A candidate whose picture was not actually seen cannot become the main pick.
  - For a video, only the poster frame is checked, so it is marked "看完整片段".
- **Match plan**: a saved, private plan for each run. It holds:
  - segments, each with a main pick and alternates, previews, scores, reasons, license and attribution;
  - gaps where nothing fits.
  Nothing is downloaded while matching.
- **Review and accept** in the 素材库:
  - The user goes through segment by segment and accepts candidates.
  - Accepting downloads through the existing staging and acceptance path. It creates a normal Material revision with the source URL, license, attribution and rights. It can attach to the project with the segment as the reference note.
- **Gaps stay gaps**: a segment with no good candidate is listed as a material request, to shoot, upload, or rewrite the beat. It is never filled automatically with generated or loosely related material.
- **Shot-level search in the 分镜 step** (added 2026-10-22): the AI 创作助手 in the bottom-right corner gets a "找素材" action.
  - With a shot in focus, it searches for that shot. Otherwise it searches every shot that has no material yet.
  - The query is built from the shot's narration, visual, purpose, asset requirements and evidence requirement.
  - It uses the same planner, own-library-first search, licence filter and visual check as a full match run. The results are saved as a match run linked to the project, unit and shot.
  - The assistant shows a few candidates per shot with previews and reasons.
  - The user picks one. It is accepted into the material library, referenced by the project with the shot as note, and set as that shot's source material in the draft. The draft change is saved the normal way, so nothing is bound without the user saving.
  - Shots with nothing suitable show a material request instead.
- **Runs belong to their project and piece** (added 2026-10-22). The user found that searches looked temporary: per-shot and per-card runs are linked to a project and unit in data, but no page showed it.
  - The run page shows its project and piece, with a link back.
  - 素材库 history lists every run (whole script, shots and cards), labelled with project and piece, and can be filtered by project.
  - Each piece's production page (text, graphic and video) gets a 「找素材」 entry listing that piece's runs and opening them. It can start a new run from the piece's content.
- **Manual upload per segment** (added 2026-10-22). Next to 「用这个」 and 「都不合适」, each segment or shot has 「上传自己的」.
  - The upload uses the existing material upload with rights fields (source, licence or own work, model and public use).
  - It is recorded as the segment's choice, attached to the project with the segment as the note, and clears an earlier "都不合适".
  - The agent reads it through `get_material_match` like any other pick.
- **Agents** use the same API, and the `video-material-scout` skill calls it as its first online step.

## Capabilities

### New Capabilities

- `script-material-matching`: script-driven segment planning, own-library and open-library search, scored candidates, and saved match plans reviewed and accepted into the material library.

## Impact

- **API**:
  - New providers in the material search registry.
  - A new `material_match_run` table (migration).
  - A background job with progress and cancel.
  - Endpoints to start, read, cancel, and accept a candidate.
- **Models**: planning uses the chat routing. Visual checks use a registered chat model that accepts images, through the existing `model_vision` outbound policy. Without one, visual checks are skipped and marked.
- **Runtime**: Pexels and Pixabay keys (optional Openverse token) are set in the ignored runtime env. They are never stored in the database or printed.
- **Web**: an "按文案找素材" view in the 素材库; a "找素材" action in the AI 创作助手 on the video 分镜 step (`FormAssistancePanel`, `VideoShotMaterialPanel`).
- **Not included**: Coverr. Its API needs a key and could not be confirmed, so it is left out instead of guessed.
- **Depends on** `add-material-library-workspace` for the 素材库 page.
