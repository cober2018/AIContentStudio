## Grouping

Group active materials by the content hash of their latest revision. A group with more than one material is a duplicate group.

## Which entry stays

The oldest material (lowest id) stays. Others get `status = "archived"` with `metadata` note `merged_into = <kept id>`. Bytes and revisions are untouched, so execution packages, previews and old drafts still resolve.

## Rights

Compare `rights_status, public_use_allowed, model_use_allowed, commercial_use_allowed, attribution_text`.
- All equal → merge.
- One entry's permissions are all ≥ the other's (true beats null/false) with the same attribution → keep the oldest entry, give it a new revision-free rights update copied from the more permissive one, merge.
- Otherwise → not merged, reported in the result.

## Current draft

For each video unit whose latest master references a retired revision, replace that revision id with the kept material's revision of the same bytes (shots, timeline items, voice, music, cover) and save through `edit_handoff._save` (same as 准备剪辑). Project references are added for the kept revision.

## Prevent new duplicates

In the shared create path for a new material from bytes or a link: if an active material's revision already has this content hash, return that revision (adding the project reference when a project is given) instead of creating a material. The existing entry keeps its rights; the rights sent with the new upload are not applied, because a Finder drop always claims 自己拍摄或制作 and must not widen the rights of a web or licensed file.

## Same-folder files

Within each project folder, 外部素材库 and 通用素材库, files with identical sha256 in the same directory: keep the one a revision points to (or the oldest), remove the others.

## Edit task after a merge-only save

`edit_handoff.status` follows the parent chain past masters whose edit summary only says `dedupe`, so the existing edit task still counts and the page does not ask for 准备剪辑 again.
