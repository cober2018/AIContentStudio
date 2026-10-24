## 1. 连接检测

- `library_reachable()`（页面、读文件前调用，5 秒缓存）：只读——`root.is_dir()`、可读可进入、`os.listdir(root)` 成功且包含 `AIContentStudio` 文件夹。上次的半掉线表现为目录列出为空，这一条能识别。
- 新增 `library_writable()`：沿用现在的探测文件写读删，只在写硬盘的操作开始前调用一次：`project_folders.move_into` / `to_common` / `_use_elsewhere` / `export_copy` / `after_execution`、`storage_locations` 的搬迁。失败报「素材库未连接」，不开始写。

## 2. 校验记录

- 记录：`metadata_json["verified"] = {"path", "size", "mtime_ns", "hash"}`，在一次完整读取并且哈希一致后写入（`local_file_checked` 和 `read_bytes_checked` 的本地文件分支）。内存缓存 `_verified` 保留，作为第一层。
- `verify_bytes_checked`（保存主稿、就绪检查、检查项用）：本地文件且记录与当前 `stat` 一致 → 只读开头 64 字节返回（调用方只用它判断文件类型）；不一致或没有记录 → 走完整读取并更新记录。
- `read_bytes_checked` 仍返回整份内容（真需要内容的地方用），完整读后同样更新记录。
- 文件被替换（大小或修改时间变化）就重新整读；内容被改但大小和时间都不变的情况不防，播放和剪辑复制时仍会完整校验。

## 3. 剪辑素材复用

- `creative_executions` 物化输入时（`clone_private` / `copy_private` 前）：在 `MEDIA_ROOT/.creative-executions/<owner>/*/inputs/` 里找同名 `<revision>-<hash>.<ext>` 且大小一致的文件；找到就用它做克隆源（同一个 Mac 磁盘，APFS 克隆，不占空间、不读硬盘），找不到才从硬盘复制。克隆后照旧算哈希核对（读的是 Mac 上的文件）。

## 4. 不变

播放（Range 流式读硬盘）、小样/成片写回时机、剪辑在 Mac 工作区进行，都保持现状。
