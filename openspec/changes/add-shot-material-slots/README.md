# add-shot-material-slots

**Stage:** applied locally and checked in the browser on U80. Not committed or archived.

**What:** in video production, each shot is a slot that takes material from any source. It shows the shot's brief: narration, visual, search words, generation prompt and route. It also shows a status, and picks from the 素材库 match runs. Missing material does not block work. Agents can read the slots through MCP but cannot bind.

**Files:** `proposal.md`, `design.md`, `specs/shot-material-slots/spec.md`, `tasks.md`, `task_plan.md`, `progress.md`, `findings.md`.

**Code (uncommitted, `main` working tree):** API `app/services/shot_slots.py`, `app/routers/material_match.py`, `app/services/material_matching.py` (planner prompt), `app/services/creative_mcp.py` + `mcp_settings.py` (`get_shot_slots`), `app/services/web_video_handoff.py` (missing shots); Web `ShotSlotsBoard.tsx`, `shotSlots.ts`, `ProductionContextHeader.tsx`, `MaterialMatchView.tsx`, `VideoShotMaterialPanel.tsx`.

**Next:** the user fills slots on U80 and accepts the shot plan; archive on request.
