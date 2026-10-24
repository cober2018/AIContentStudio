## Context

- The creative MCP (`services/creative_mcp.py`) exposes tools and `aics://` resources. Craft know-how is not exposed.
- `video-production-handoff/references/motion-toolkit.md` is a fixed visual system for 1080×1920 explainers. `scripts/ae_build.py` turns a JSON spec into native AE compositions and runs them in AE.
- After Effects 2026, with `aerender`, and DaVinci Resolve are installed on the user's Mac. The platform runs only on that Mac.

## Decisions

1. **Layout in the platform.** One source, read by both the MCP and the local skills:
   ```
   apps/api/craft_skills/
     ae-motion/   SKILL.md (index)  components.md  scripts/ae_build.py  scripts/fill.jsx
                  templates/<template-id>/<version>/manifest.json, preview.mp4, poster.jpg
     resolve-edit/ SKILL.md (index)  edit-combos.md  finishing.md  native-execution.md
   ```
   The AE projects sit in a local template store outside git (`~/AIContentStudio/ae-templates`, setting `ae_template_store`). The manifest holds the file name and the SHA256.
2. **Index format.** Each `SKILL.md` lists entries as job → file, with one line on when to use it. Adding a template adds one line.
3. **Manifest.** Fields: `id`, `version`, `name`, `use` (one sentence; this is what the AI matches against a storyboard row), `fields` (name, kind text|number|image|color, max length), `duration_ms` range, `aspect_ratios`, `fonts`, `aep` {path, sha256}, `comp` (always `MAIN`).
4. **Render.** Templates are saved as XML projects (`template.aepx`). Every expression reads one JSON literal between `/*AICS_DATA*/` and `/*AICS_END*/`, because aerender does not load JSON footage (tested: expressions fell back to the static text). A render copies the XML into a job folder, rewrites that literal and the image paths, swaps supplied images (converted to the PNG the template expects) and runs `aerender` on `MAIN` for the requested frames. The running After Effects is never scripted. The output becomes a candidate video material (`source_kind` chart, origin `ae_template`) with template id, version, project hash, data hash and image revisions recorded; rights follow the image inputs. Before rendering, the project hash, fonts (CoreText PostScript lookup) and `aerender` are checked; a failure is reported as is.
5. **MCP tools:**
   - `get_craft_skill(skill)` returns the index;
   - `get_craft_entry(skill, entry)` returns one file;
   - `list_ae_templates()` returns the manifests;
   - `render_ae_template(project_id, unit_id, template, version, content)` returns the new material revision.

   Only render writes, and only a candidate material.
6. **Acceptance gate for a template.** Two renders with different content, both inspected, recorded in the manifest as `checks`. Without them, `list_ae_templates` marks the template as draft, and the platform does not auto-use it.
7. **Local skills.** `.codex/skills/ae-motion` and `resolve-edit` hold a short SKILL.md that says to read the index through the platform MCP. `video-production-handoff` craft sections point there.

## Risks

- AE must be installed and licensed, and only this Mac renders. If `aerender` is missing, render reports it, and the rest of the platform keeps working.
- Fonts missing at render time would change the look. The pre-check stops the render instead.
