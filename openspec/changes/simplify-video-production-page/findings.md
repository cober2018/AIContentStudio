# Findings

- The duplicate table comes from `StageProposalReview.tsx` rendering `StoryboardTable` and then the full video `ModalityWorkspace`, which renders `StoryboardTable` again plus the editor.
- U80 live master is still the old 7-shot revision (132); the 15-row draft is not yet adopted.
- Decision (user, 2026-10-23): simplify everything; the platform automates, the user reviews. Table stays 9 columns.
- Decision: product video and text/graphic pages are out of this change.
- Accepting a 导演稿 already creates the master (`accept-master`), so 采用这版 = accept + autofill; no separate save call.
- The 更多 fold hides non-main children with CSS (`[&>*:not([data-main])]:hidden`) instead of moving JSX, so local drafts and panel state survive opening/closing.
- One-click voice is not available: TTS runs only as a workflow audio stage (`stage_audio.py`) or the manual native-generation panel; `/video-tts` returns `capability_unavailable`. Left as task 2.2.
- U80's saved master (revision 1) has no table rows, so the make page shows no table until the 15-row draft is adopted.
- 海底光缆 work: all 15 planned shots already have a pick from 2026-10-21 (11 user uploads, Pixabay ×2, Wikimedia ×1, run 8/9/10). Before adoption the slot view follows the saved 7-shot master, so the draft table's 素材 column is shifted by one row and shows only 7; after adoption it lines up with all 15.
- 采用这版 no longer shows an error when autofill has nothing to fill (`material_autofill_nothing_to_fill`).
- Slot picks still reach the cut only after they are placed into the master and saved (per-shot desk under 更多).
- After the user adopted the 15-row draft: 15/15 rows have picks, 0 placed in the master yet. 专业执行准备 is `stale` (`accepted_stage_input_changed`): its 导演包 was built from the old 7-shot master on 10-23 03:23 and must be regenerated and accepted again.
- The make-page 更多 toggle was an underlined text link the user could not find; now a bordered bar like the plan page.
