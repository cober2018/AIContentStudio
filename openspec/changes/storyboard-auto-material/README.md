# storyboard-auto-material

**Stage:** applied locally (not committed). API restarted.

**What:** one **AI 补齐素材** action on the 分镜表. For each empty row, it searches the own library and licensed stock (with vision scoring) and picks an eligible candidate; otherwise it fills and renders a ready AE template; otherwise it marks a 缺口 with a reason. Every auto pick shows its source. The user's picks are never replaced, and the master is saved only by the user.

**Files:** `proposal.md`, `design.md`, `specs/storyboard-auto-material/spec.md`, `tasks.md`, `task_plan.md`, `progress.md`, `findings.md`.

**Builds on:** `video-storyboard-table`, `craft-skills-ae-resolve`.

**Next:** regenerate and accept U80's 导演稿 (live master is the old 7-shot one), then try AI 补齐素材 on the platform.
