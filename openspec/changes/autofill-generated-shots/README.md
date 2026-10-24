# autofill-generated-shots

**Stage:** applied locally (not committed). API restarted. Verified on a DB copy after the model route recovered.

**What:** two new AE templates, 对比卡 (compare-pair) and 图片推镜 (photo-push). Auto-fill gains a last step: generate a picture for a still-empty row, render it with a template, and tag it 「AI 示意」 (proof rows: 「AI 示意，非实拍」). At most 8 images per run.

**Trigger:** U80 auto-fill left 4 of 6 rows as gaps (deep-sea dive, cable vs hose, fibre vs hair, chat-UI transition).

**Files:** `proposal.md`, `design.md`, `specs/autofill-generated-shots/spec.md`, `tasks.md`, `task_plan.md`, `progress.md`, `findings.md`.

**Next:** user regenerates and accepts U80's 导演稿 (live master is the old 7-shot one), then runs AI 补齐素材 on the platform.
