---
name: craft-ae
description: Use for After Effects work in AIContentStudio videos: picking and rendering AE templates (number card, title card, flow diagram, map route), building compositions, keyframes, compositing, tracking and title techniques, and turning a new effect into a reusable template.
---

# craft-ae

The content lives in the platform, not here. Through the local AIContentStudio creative MCP:

1. `get_craft_skill` with `skill: "craft-ae"` returns the index. Read it first.
2. Read only the entry you need with `entry` (for example `components.md` or `templates.md`).
3. `list_ae_templates` shows templates; only `ready` ones may be chosen automatically.
4. `render_ae_template` renders into a candidate project material. It never binds a shot; the user decides.

Technique sections (`techniques/<category>.md`) are chosen through craft-resolve `choose.md`.

Do not copy the platform files into this folder.
