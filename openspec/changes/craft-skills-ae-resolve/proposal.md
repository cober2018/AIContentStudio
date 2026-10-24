## Why

The user wants self-made video material to come first from After Effects templates, reused across videos, and the edit to happen in DaVinci Resolve. Both run on the user's Mac (After Effects 2026 with `aerender`, Resolve installed).

Today the AE and Resolve know-how sits inside the `video-production-handoff` skill:

- `references/motion-toolkit.md` and `scripts/ae_build.py` describe AE components;
- `references/edit-combos.md` and `references/finishing.md` cover editing and finishing.

The two are mixed together, there is no index, and the platform MCP cannot reach any of it. Every effect explored for one video is lost for the next.

## What Changes

- Two independent craft skills SHALL exist as entry points: **ae-motion** (After Effects) and **resolve-edit** (DaVinci Resolve). Each has an index that says, for a given job, which template or technique file to read.
- The platform creative MCP SHALL include both skills. An agent reads an index, then reads only the entry it needs. The files live once, in the platform. The local `.codex` and `.claude` skill files only point to the MCP.
- AE templates SHALL be kept as a library:
  - one folder per template version, with a manifest (use, replaceable fields, durations, aspect ratios, fonts), a preview and a poster;
  - large `.aep` files stay outside git, at a path the manifest names;
  - replaceable layers are named `@field`, and all expressions read one embedded data literal that the platform rewrites per render.
- A template SHALL enter the library only after it renders correctly with two different sets of content. A changed template becomes a new version, and old versions stay.
- The platform MCP SHALL render a template locally with `aerender` into a new candidate material, recording the template id, version and filled content. It never binds the material to a shot or accepts it.
- `video-production-handoff` keeps the workflow and platform contracts. Its craft sections point to the two skills.
- First templates come from U80's 后期做 shots: number card, map route, diagram flow and title card. The existing `ae_build.py` components move into ae-motion as they are.

## Impact

- New: craft skill files and AE template manifests in the platform; MCP tools to read the indexes and entries and to list and render templates.
- Changed: `video-production-handoff` craft sections become pointers.
- Not in this change: automatic material fill on the storyboard table (`video-storyboard-table` will use these templates), code-generated animation, and AI video generation.
