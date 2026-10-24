# dedupe-material-entries

**Stage:** applied locally and archived 2026-10-24 (not committed). API restarted.

**What:** each file appears once. Entries with the same bytes merge (oldest kept, others archived with `merged_into`); the latest 导演稿 is re-saved to use the kept entry; uploading / dropping / linking bytes already in the library reuses that entry; identical files in one library folder are reduced to one.

**Code:** API `app/services/material_dedupe.py` (new: `existing_revision`, `merge`, `dedupe_folders`), `routers/materials.py` (upload reuse), `routers/project_assets.py` (project upload reuse), `services/material_external.py` (link reuse), `services/edit_handoff.py` (status follows merge-only saves).

**Result:** 3 groups merged (all in 海底光缆); 海底光缆 draft v12 (master 143) uses one entry each for ship and 镜头 3; 7 groups left alone because rights differ (listed in progress.md); no duplicate files on disk.

**Next:** none. Ask the user about the 7 rights-different groups if they want them merged by hand.
