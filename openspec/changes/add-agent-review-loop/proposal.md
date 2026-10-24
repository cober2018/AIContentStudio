## Why

The user drives production with a large model (Claude/Codex) through MCP, and decides on the platform. Today that loop is broken:

- MCP can only work on creative execution packages (video handoff). It cannot run a production stage, read its options or learn what the user decided.
- So the agent fell back to calling the REST API directly and accepted stage results itself (海底光缆 sample, 2026-10-22). Card previews ended up as files in the agent's temp folder, outside the platform.
- Graphic options show only text and layer counts before acceptance; real images exist only after a Master is accepted.

On 2026-10-22 the user stated the intended loop:

1. The model proposes via MCP.
2. The platform shows the options as real images.
3. The user picks or rejects on the platform.
4. The platform signals the decision back.
5. The model continues.

The user also asked that this be built as platform capability, not something the model works around each time.

## What Changes

A shared "model proposes, you decide" loop, wired first to **graphic cards** and **footage choices**:

- **New MCP tools**, so the model never needs the REST API for these steps:
  - `preview_stage` (read) and `run_stage` (mutating): check readiness and run a production stage.
    - Same rules as the web: exact resolution hash, invocation key, tunable `instruction` only.
  - `get_stage_result` (read): the options of the latest attempt, plus a `review_url` to the platform page where the user decides.
  - `get_stage_decision` (read, optional bounded wait ≤ 25 s): the user's decision on an attempt.
    - The decision is one of: waiting for you / accepted / accepted with edits / rejected / rerun requested / commented.
    - It also carries the user's note, the chosen option, the accepted result, and what stage the platform continued to.
  - `start_material_match` (mutating) and `get_material_match` (read).
    - `get_material_match` returns a review URL, each segment's options, the user's picks and per-segment rejections with notes.
  - **No MCP tool can accept, reject, bind or publish.** These stay web-only actions by the user.
- **Images before deciding (graphic):**
  - The stage review renders each card of each option to PNG with the platform's own renderer and shows them as thumbnails, with a larger view on click.
  - Previews are cached by payload hash and canvas.
  - They are marked preview-only: not attested, not saved as material, not a Master.
- **Simple decision on the platform:**
  - Graphic stages keep their existing accept / accept-with-edits / reject-with-reason actions (feedback already exists), now beside the images.
  - Footage segments gain **"都不合适"** with a short note, next to the existing **"用这个"**.
- **Signal back:**
  - Decisions are read from records the platform already keeps: acceptance, feedback events and continuation.
  - The new segment rejection is stored on the match run.
  - No new push channel: the model reads the decision via `get_stage_decision` / `get_material_match`.

Out of scope for this change:
- Text and shot-plan stages. The MCP tools are generic, but only graphic and footage review UIs gain images and decision actions now.
- Global "待你决定" inbox.
- Notifications.
- Making REST unusable by a local agent (REST stays the web's API; the agent rule is to use MCP).

## Impact

- API:
  - `services/creative_mcp.py`: new tools that call existing services (stage preview/run/result, stage feedback history, material matching).
  - New candidate preview route under `creation-recipe/stages/{node}`, using `LocalGraphicRenderer` and the derivative cache.
  - `material_matching`: segment rejection.
- Web:
  - `StageProposalReview` gets graphic thumbnails.
  - `MaterialMatchView` `SegmentResult` gets "都不合适" with a note.
- Skills: `.codex/skills` instructions that drive production are updated to use the MCP loop and wait for decisions.
- No schema migration expected; segment rejections live in the match run's `result_json`.
