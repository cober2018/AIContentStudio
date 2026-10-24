# Findings: dedupe-material-entries

- The duplicates in the floating window are DB entries, not files: no two files with the same sha256 exist in 海底光缆, 外部素材库 or 通用素材库.
- 10 duplicate groups library-wide. 海底光缆: materials 135/136 (镜头 3), 132/133 (镜头 1 and 镜头 2, same video), 142/144 (ship; the current draft uses both, shots 9 and 11).
- Some twins carry different rights on purpose (「·可AI剪辑」 copies of ESP32 footage, Cipher with CC BY attribution), so rights decide whether a group can merge.
- Applying the upload's rights on reuse would let a Finder drop (always 自己拍摄或制作, public + AI allowed) widen the rights of a web or licensed file, so reuse keeps the existing rights.
- A merge-only re-save made the page think the draft needed a new edit task; status now looks past such saves.
