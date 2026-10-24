# Progress

## 2026-10-23
- Proposal written. No code changed.
- Applied (user confirmed):
  - `article.plan.v1` schema (title, angle, reader_stake, known, unknowns, sections) with the same fact rules as the research brief.
  - `stage.creative.method.v3` plugin (schema list + article.plan.v1); acceptance and upstream handoff accept v3 attempts.
  - Built-in methods `studio.text.article-plan@1` and `studio.text.article-write@1` (merged rules from evidence-brief/angle-lab/outline and longform/humanize/title-hook).
  - Text answer schema: optional `alt_titles` (≤2), kept on the candidate.
  - Text definition: 写作方案 (3 candidates) → 成稿 → 质量检查; method-trial bump only touches v1 creative nodes.
  - Continuation auto-accepts a check result when every check passes.
  - Web: labels for the plan fields.
- Verify on a DB copy with the real model, project 41 (海底光缆): 写作方案 returned three distinct plans (physical fragility / history and capital / operations and repair), each with 5 facts and 4 sections; accepting one started 成稿 automatically; it returned a full article with two alternative titles; accepting it started the check automatically, which reported blockers (text_fact one claim, text_identity, text_platform missing cover) and a discoverability warning, so the step failed as 需要处理. API suite: only the 7 pre-existing failures. Web build passes. API restarted while idle.
- User: move persona text defaults and delete old versions (test data). Persona 2 and 3 text defaults saved through the platform route: revision 3 → 4 (workflows 65, 66), plan → write → quality, fact mode kept (grounded / current).
- Deleted old persona workflow versions that nothing references: 12, 16, 20 (persona 3 video v1–v3). DB backup first: `~/AIContentStudio/db-backups/content_studio-before-workflow-cleanup-20261023.db`.
- Kept because existing works are pinned to them or ran on them: 7, 13, 17 (persona 2 text), 9, 14, 18 (persona 2 video), 10, 15, 19 (persona 3 text; 10 and 15 are parents of 19). Deleting them needs deleting those works; waiting for the user.
- User: delete the old test works and their versions; keep 海底光缆. The platform's own unit delete only archives works with history, so a cascading delete script was prepared (scratchpad `cleanup_old_works.py`): units 1, 3, 4, 6, 7, 41, 42, 75, 76, 77 and their dependent rows (runs 11, steps 74, attempts 66, masters 18, check runs 137, outputs 22 and a few assets, reviews, delivery targets, packages and one generation task), then workflow versions 7, 9, 10, 13, 14, 15, 19; versions 17 and 18 stay for 海底光缆 with their parent link cleared. Rehearsed on a copy: 0 foreign-key violations. The user ran it on the live DB: same counts, 0 foreign-key violations; 海底光缆 units 78–80 intact and readable.
