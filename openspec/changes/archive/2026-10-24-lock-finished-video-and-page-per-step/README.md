# lock-finished-video-and-page-per-step

**Stage:** applied and archived 2026-10-24 (not committed). API restarted.

**What:** 成片通过后锁定（可重新打开）；内容没变的保存不打断视频进度；角色视频按「选题与资料 / 导演稿 / 小样 / 成片 / 交付」一步一页。

**Code:** API `services/video_chain.py`, `services/content_masters.py`, `routers/edit_agent.py`；Web `product/ProductionWorkspace.tsx`, `VideoChainPanel.tsx`, `StoryboardTable.tsx`, `ContentMasterPanel.tsx`, `VideoStudioShell.tsx`, `CreationRecipePanel.tsx`。Branch `video-chain-and-material-library`.

**Next:** none.
