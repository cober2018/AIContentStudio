# Progress

## 2026-10-23
- Proposal written. No code changed.
- Applied (user confirmed):
  - `apps/api/craft_skills/ae-motion` (index, `components.md` from motion-toolkit, `templates.md`, `scripts/ae_build.py`, `scripts/make_templates.py`, four template manifests) and `resolve-edit` (index, edit-combos, finishing, native-execution), moved out of `video-production-handoff`.
  - `.codex/skills/ae-motion` and `resolve-edit` point to the MCP; `video-production-handoff` craft paragraph points to them.
  - `services/craft_skills.py`; settings `ae_template_store`, `aerender_path`; MCP tools `get_craft_skill`, `list_ae_templates`, `render_ae_template` (pinned MCP tool list test updated).
  - Templates v1 in `~/AIContentStudio/ae-templates`: number-card, title-card, diagram-flow, map-route, with preview.mp4 and poster.png.
- Verify: on a DB copy, rendered each template twice with different content for U80 (16 frames inspected); map-route first failed (route off-screen under cover fit), fixed to contain fit and re-checked. Live MCP after restart lists the three tools, returns both indexes and an entry, and lists four ready templates. No live render was made into the real project. API suite: only pre-existing failures remain.
