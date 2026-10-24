# gentle-external-drive-access

**Stage:** applied and archived 2026-10-24 (not committed). API restarted.

**What:** 平台少碰移动硬盘：只读检测连接（写之前才写探测）；每个素材只完整校验一次（记录路径/大小/修改时间）；剪辑素材只从硬盘复制一次；写硬盘时机不变。

**Code:** API `services/storage_locations.py`, `services/project_folders.py`, `services/materials.py`, `services/creative_executions.py`, `services/creative_media_stream.py`. Branch `video-chain-and-material-library`.

**Next:** none.
