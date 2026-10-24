## 1. API

- [x] 1.1 Video definition (persona and product) is 导演稿 only; product default moves when its definition has `shots` or `prepare`.
- [x] 1.2 Persona 2 and 3 video defaults moved live: workflow 63 → 67, 64 → 68 (revision 5, 导演稿 only); old workflows kept. DB backup before the move in the session scratchpad (`before-prepare-removal.db`).
- [x] 1.3 `edit_handoff`: no prepare step; status gains `needs_handoff` (master lacks material/edit settings, or no edit task for the latest master).

## 2. Web

- [x] 2.1 Recipe summary and step list skip `stage.professional.prepare`; 准备剪辑 shows from `needs_handoff`. The full stage panel under 更多 still lists it for old runs.

## 3. Verify

- [x] 3.1 DB copy: new video definition = [master]; 海底光缆 准备剪辑 queues the edit task without touching the old stage. Live page: step list shows 已接受 3/3 and no 专业执行准备; header shows 准备剪辑. Full API suite: 2808 passed, same 7 known failures; one test updated to build the retired node itself. Web build passes.

## 4. Docs

- [x] 4.1 README, task_plan, progress, findings.
