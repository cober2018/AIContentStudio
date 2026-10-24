# Findings

- The edit task (`web_video_handoff.prepare_edit`) builds its own `director.video.v1` package from the saved master; it does not read the 专业执行准备 package.
- The video definition is in `starter_personas._definition` (nodes `master` → `prepare`); the product default reuses it and adds prepare constraints in `workflow_templates`.
- Decision (user, 2026-10-24): remove 专业执行准备.
- `tests/test_persona_creative_studio.py` took the last video node as the prepare stage; it now builds that node itself, since old runs still use the plugin.
