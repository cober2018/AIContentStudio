# video-storyboard-table

**Stage:** applied locally (not committed). API restarted. Waiting for the user's platform check.

**What:** a video's 导演稿 is one storyboard table, made in one go. One row per shot: 镜头, 时长, 信息点, 画面, 运镜, 台词, 声音, 备注, 素材. New video workflows drop the separate 视频脚本 and 镜头计划 stages. Material picked in a shot slot is used without picking again.

**Trigger:** U80 shot plan (15) and director draft (7) did not match, and material had to be picked twice. The user wants one table, like a professional storyboard sheet (`openspec/视频分镜脚本表.xlsx`).

**Files:** `proposal.md`, `design.md`, `specs/video-storyboard-table/spec.md`, `tasks.md`, `task_plan.md`, `progress.md`, `findings.md`.

**Related:** `master-follows-shot-plan` (applied locally) keeps old runs such as U80 aligned to their shot plan.

**Next:** user regenerates the U80 导演稿 and checks the table; persona 2 and 3 video defaults already moved (revision 4).
