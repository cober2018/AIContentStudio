## Why

The cover and title decide whether people click. Today only the WeChat article form has an optional cover slot; Xiaohongshu, Douyin, Bilibili and WeChat Channels versions have no cover at all, there are no candidates to compare, and titles are just one field. The user confirmed cover & title as its own step in the workflow (2026-10-21).

## What Changes

- A **cover & title step** for every platform version, after production and before review.
- **Platform cover specs** in the channel registry: Xiaohongshu 3:4 (1080×1440), Douyin 9:16 (1080×1920) with a 3:4 feed crop, Bilibili 16:9 (1920×1080), WeChat Channels 3:4, WeChat article 2.35:1 (900×383) plus 1:1 share image. Each spec lists safe areas where platform UI overlays text.
- **Cover candidates** from four sources, each a normal MaterialRevision with rights: a frame picked from the video at a chosen time; a project image; platform image generation (existing providers); a layout composed from an image plus cover text (existing graphic composition).
- **Cover text and title candidates** generated with a built-in method (`studio.cover.title-hook@1`), several options per platform, following persona expression and fact boundary.
- **Human choice**: the user picks one cover and one title per platform version; the choice is frozen into the candidate hash, so approval covers exactly what will be shown.
- Review shows each platform version's cover at real size with the safe-area overlay.

## Capabilities

### New Capabilities

- `cover-title-design`: per-platform cover specs, candidates, choice and freezing.

## Impact

- `channel_registry.py` (cover specs), channel variant media roles, candidate manifest; new built-in skill package; production workbench step UI and review preview.
- Frame grabs use ffmpeg on the rendered output, read through the existing media stream.
