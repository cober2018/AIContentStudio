# Findings: project-material-folders

- Drive today: `/Volumes/T1000/自媒体素材/` holds `大海/` (the user's 海底光缆 footage), `项目1/` (the standard layout template) and `AIContentStudio/` (platform files by type and hash).
- Confirmed by the user: three libraries (外部 / 通用 / 项目); move happens at 准备剪辑; a file used by a second project stays in the first project's folder and is referenced.
- Storage keys must not change: execution packages and edit manifests hash them. Hence a placement record instead of rewriting keys.
- Defaults chosen by the platform (not asked): 通用素材库 files are never moved; voiceover goes to `音频/` itself because the layout has no voiceover folder; `大海/` and `项目1/` are left alone apart from files 海底光缆 uses.
- 海底光缆's materials were platform copies of the files in `大海/` (same sha256), so archiving moved the user's files and dropped the copies. This rule is general now (see design).
- Project title is long (「海底光缆｜你发的消息怎么跨过大洋｜20261022」); the folder uses the part before the first ｜.
- Staged execution outputs are `<hash>.bin`; the 小样 copy takes its extension from the output's declared type.
- 97 older materials still sit in the platform's local folder and show under 外部 as 平台本地; they move when a project uses them.
- Unused files in `大海/` (4 PNGs) stay there.
