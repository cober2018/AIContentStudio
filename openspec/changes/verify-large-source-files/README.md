# verify-large-source-files

- 阶段：缺陷修复（执行方反馈），已本地实施，未提交
- 问题：保存导演稿时，超过 30 MB 的源文件（iPhone 口播 MOV、WAV 配乐）报 video_asset_bytes_unverified。
- 原因：materials.verify_bytes_checked 对没校验过的文件走 read_bytes_checked，整份读进内存，存储层 MAX_BYTES=30 MB 直接拒绝。
- 修复：本地文件改走 local_file_checked（1 MB 分块算哈希，记住已校验），只读前 64 字节给类型检查；非本地存储仍走原路径。
- 代码位置：apps/api/app/services/materials.py verify_bytes_checked
- 验证：项目 44 / 作品 85，rev 266（54 MB MOV）、271（61 MB MOV）、218（37 MB WAV）校验通过；用 266 + 218 存导演稿在回滚事务里成功（未落库）；相关测试通过。
- 记录：首次校验 rev 266 用了约 30 分钟，之后同盘大文件冷读都在 0.1 秒内，未能复现，疑似当时硬盘读取卡住；若再出现需看硬盘状态。
