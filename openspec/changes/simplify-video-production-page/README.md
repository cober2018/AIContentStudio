# simplify-video-production-page

**Stage:** applied locally (not committed). Web build passes. User check pending.

**What:** for non-product video works, 内容方案 is one 9-column table with one button (生成导演稿 / 重新生成 → 采用这版 → 去制作内容). 采用这版 saves the master and starts AI 补齐素材. 制作内容 shows the table, 配音, 导演包 and 保存当前主稿; everything else sits behind 更多.

**Code:** `apps/web/src/product/` — `ProductionWorkspace.tsx`, `CreationRecipePanel.tsx` (`simple`), `StageProposalReview.tsx`, `VideoStudioShell.tsx` (`view="simple"`, `more`), `ContentMasterPanel.tsx`.

**Not done:** one-click 生成配音 (task 2.2), see findings.

**Next:** user regenerates/adopts U80 and checks both pages; decide on a small change for one-click voice.
