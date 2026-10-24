# auto-edit-handoff

**Stage:** applied locally (not committed). API restarted. User check pending.

**What:** after 采用这版 the platform fills empty rows, puts each row's single pick into the master, decides DaVinci (all rows) and AE (per row, with a reason), saves, and rebuilds and accepts the 导演包. For a work adopted earlier, the 导演稿 header shows 准备剪辑.

**Code:** API `app/services/edit_handoff.py` (new), `routers/material_match.py`. Web `editHandoff.ts` (new), `StageProposalReview.tsx`, `CreationRecipePanel.tsx`, `StoryboardTable.tsx`.

**Next:** user clicks 准备剪辑 on 海底光缆 and checks the table and 导演包.
