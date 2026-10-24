# Progress: dedupe-material-entries

- 2026-10-24: proposal written. Waiting for 确认.
- 2026-10-24: applied. Sandbox on DB / media / library copies, then real run (DB backup: scratchpad `db-before-dedupe.sqlite`).
- Merged: 133 → 132 (镜头 2 = 镜头 1 video), 136 → 135 (镜头 3), 144 → 142 (ship). 海底光缆 draft re-saved as master 143 (141→140, 149→147). Edit task 7 still shows 粗剪已回传，待你审片; `needs_handoff` false.
- Left alone (rights differ): 11/13 科技日常图卡2, 24/117 Cipher, 66/67 纸笔窗边, 108/113, 109/114, 110/115, 111/116 ESP32 (「·可AI剪辑」 twins allow AI use, the originals do not).
- Folder dedupe: nothing to remove.
- Checked: 项目 → 海底光缆 lists 15 entries / 15 files; kept entry raw read 200; re-uploading 手机掉入大海.mp4 returned material 132 (`reused`), material count unchanged. Tests: 269 passed (incl. all upload / link tests; one test updated behaviour handled by recording the attach event and rolling back on failure).
