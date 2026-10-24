## 1. API

- [x] 1.1 `services/edit_handoff.py`: place single picks (image/video with model or public use), one model call for AE rows (rows already rendered from an AE template are skipped, max 15), postproduction (粗剪, 30 fps, 1080×1920 or 1920×1080), save the master with `edit_summary.auto_handoff`.
- [x] 1.2 Re-run 专业执行准备 (preview → run → accept `professional`) when it is stale or not accepted.
- [x] 1.3 `POST/GET /content-projects/{p}/units/{u}/edit-handoff`; failures say which step and why; retry continues (placed rows and existing settings are kept).

## 2. Web

- [x] 2.1 素材 column: 后期：达芬奇 / 达芬奇 + AE（原因）; 待你选 for several picks.
- [x] 2.2 采用这版 → 补齐 → wait → 准备剪辑, progress in the review; header shows 准备剪辑 / 继续准备剪辑 when the 导演包 is out of date.

## 3. Verify

- [x] 3.1 DB copy, 海底光缆 work: 15/15 rows placed, AE for 10 rows with reasons, master saved, 专业执行准备 accepted; all four stages accepted. Related API tests 275 passed; web build passes; live page shows 准备剪辑 (not clicked).

## 4. Docs

- [x] 4.1 README, task_plan, progress, findings.
