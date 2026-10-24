## Why

The floating library shows some files twice under 项目 → 海底光缆 (two ship videos, two phone videos). On disk there is no duplicate: each pair is one file, but the platform holds two material entries for the same bytes. This happened because the same file was added twice (uploaded twice, or picked again for another shot). The user expects each file once, and a project view to show only that project's files, once each.

Found today (same bytes, more than one entry): 10 groups across the library. In 海底光缆: 镜头 3 ×2, 镜头 1 / 镜头 2 (same video), ship ×2. Others: ESP32 实拍 / 演示 (each with a 「·可AI剪辑」 twin), 纸笔窗边, 科技日常图卡2, Cipher ×3.

## What Changes

- **One entry per file.** Entries with the same bytes are merged into one: the oldest entry is kept, the others are retired (hidden, not deleted). Anything that used a retired entry keeps working, because the kept entry holds the same file.
- **The current 导演稿 points to the kept entry.** If the latest draft uses a retired entry (海底光缆: ship in shots 9 and 11, 镜头 3), a new draft version is saved that uses the kept one; nothing else in it changes. Earlier drafts and finished edit tasks are left as they are.
- **Different rights are not merged blindly.** If two entries differ in rights (public use, AI use, commercial use, attribution, e.g. the 「·可AI剪辑」 twins), the kept entry takes the more permissive, explicitly confirmed rights only when one entry is a pure superset; otherwise the group is listed for the user and left alone.
- **No new duplicates.** Uploading, dropping from Finder, or linking a file whose bytes are already in the library reuses the existing entry (and adds it to the project) instead of creating a new one.
- **Duplicate files on disk:** if two files with the same bytes sit in one folder, the extra one is removed. Today there are none in 海底光缆, 外部素材库 or 通用素材库.
- **Views:** 外部 / 通用 / 项目 / 本作品 and the material page then show each file once.

## Impact

- API: a one-off merge step plus a reuse check in the material create path (`materials` upload / link / generated); a draft re-save for the current master when needed (`edit_handoff._save`); listing unchanged apart from hidden retired entries.
- No change to files on disk except removing same-folder duplicates (none today).
