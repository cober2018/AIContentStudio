# Findings

## 2026-10-23
- AE and Resolve know-how already exist inside `video-production-handoff` (motion-toolkit + ae_build.py, edit-combos, finishing, native-execution), mixed and without an index; the platform MCP cannot reach them.
- After Effects 2026 (with aerender) and DaVinci Resolve are installed on the user's Mac.
- User decisions: AE first for self-made material; effects become reusable templates ("武器库"); two independent skills as entry points with an index; the platform MCP includes both.
- aerender does not evaluate expressions that read JSON footage (`footage().sourceData`): the render kept the static layer text even after relinking and saving. Embedding the data in the expressions of an XML project (`.aepx`) and rewriting it per job works headless.
- aerender 26.5 writes H.264 MP4 directly with the default output module; a 4 s template renders in about 15 s including launch.
- The running AE GUI is never touched by a render. Authoring templates (`make_templates.py`) does open new projects in the GUI, so check it has no unsaved project first.
- Font check: Spotlight does not index system PingFang; CoreText PostScript lookup is reliable.
- map-route needs a real map image per use; the stored one is a placeholder grid.
