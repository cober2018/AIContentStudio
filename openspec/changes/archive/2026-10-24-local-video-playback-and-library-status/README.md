# local-video-playback-and-library-status

**Stage:** applied locally and archived 2026-10-24 (not committed). API restarted, verified in browser.

**What:** 硬盘半断开时显示「素材库未连接」；素材读取去掉 30MB 上限、边读边播；播放器右上角加「在访达中显示」「复制路径」。

**Docs:** proposal.md, design.md, specs/, tasks.md.

**Next:** none.

**Code:** API `services/storage_locations.py`, `services/materials.py`, `routers/materials.py`, `services/project_folders.py`, `services/video_chain.py`, `routers/edit_agent.py`; Web `product/FileLocationActions.tsx` (new), `product/VideoChainPanel.tsx`, `product/MaterialDetailDrawer.tsx`.
