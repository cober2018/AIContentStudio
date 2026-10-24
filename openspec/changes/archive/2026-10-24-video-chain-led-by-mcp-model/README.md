# video-chain-led-by-mcp-model

**Stage:** applied locally and archived 2026-10-24 (not committed). 海底光缆 成片 (task #10) approved and filed in 海底光缆/导出/成片.

**What:** video is led end to end by the external model over MCP: 导演稿 with a per-shot 素材需求 → (user) → materials, voiceover, DaVinci / AE → 小样 → (user) → 排版 → 成片 → (user). The platform gives tools, records and review; it calls no model for video. Articles and images unchanged. Materials default to allowed (AI editing, publishing), credits kept.

**Code:**
- API `app/services/video_chain.py` (new: state, decisions, brief + rules, save 导演稿, set materials, image, candidate import, voiceover, prepare 小样 / 成片, one-click 通过 accepts outputs).
- `creative_mcp.py` (8 tools, readable `video_chain_*` messages), `mcp_settings.py` (group 做视频), `routers/edit_agent.py` (`GET /video-chain`, `POST /video-chain/decision`).
- `video_documents.py` (`board.material_request`), `edit_handoff.py` (no model call for AE), `project_folders.py` (导演稿 file with 台词 and 素材需求).
- `materials.py` / `routers/materials.py` (rights default allowed), `material_dedupe.py` (merge keeps every credit; unset = not granted).
- Web `VideoChainPanel.tsx` (new), `CreationRecipePanel.tsx` (simple video shows the panel; generate path removed), `VideoStudioShell.tsx`, `StoryboardTable.tsx` (素材需求, AI 补齐素材 removed), `VideoStudioModel.ts`.
- Skill `.codex/skills/video-production-handoff/SKILL.md` (Video chain section); the same rules come back in `get_video_brief.rules` for any external model.

**Next:** none for this change. Optional follow-up (separate proposal): check the library is writable before saving, so a half-dropped USB drive shows 素材库未连接 instead of failing quietly.
