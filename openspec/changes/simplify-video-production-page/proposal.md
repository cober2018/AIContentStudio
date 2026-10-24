## Why

The video plan page shows the storyboard twice, plus a full video editor, a recipe panel with stages and sub-steps, and a master panel with hashes, checks and freeze candidates. The user has to tune too many things. The user's rule: the platform decides most things automatically, and the user only reviews (see `product-fixes-outcomes-not-steps`).

## What Changes

- **内容方案 (video):** one 9-column storyboard table and one primary button whose label follows the state: 生成导演稿 → 采用这版. 采用这版 accepts the draft, saves it as the master and starts AI 补齐素材 on its own. While filling runs the button shows progress; when done the page offers 去制作.
- The duplicate table and the video editor are removed from the draft review (`StageProposalReview` no longer renders the video workspace for video drafts).
- **制作内容 (video):** the same table (素材 column editable, other columns read-only), then two steps: ① 生成配音 from the 台词 column with the chosen voice, then listen; ② 准备剪辑包 (existing director package to AE / DaVinci), then the returned cut preview.
- Everything else (stage controls, sub-steps, history versions, checks, hashes, freeze candidate, subtitles, timeline, ASR, per-shot tools) moves into one collapsed 更多 area on each page. No feature is deleted.
- Scope: non-product video works (such as U80). Product video (real shooting routes) and text/graphic works keep their pages for now.
- Not in this change: assembling the cut automatically from the narration audio; the floating material library and storage locations (`material-library-single-home`); edit proxies.

## Impact

- Web only: `ProductionWorkspace.tsx`, `VideoStudioShell.tsx`, `StageProposalReview.tsx`, `StoryboardTable.tsx`, `CreationRecipePanel.tsx` and `ContentMasterPanel.tsx` (wrapped in 更多 for video).
- API: none expected. Accept, save master and AI 补齐素材 use existing endpoints, called in sequence from the page.
