# findings

- `library_reachable()` 只看 `is_dir()` + `os.access`，硬盘半断开时仍返回 True，所以「素材库未连接」提示从未触发（提示和浮窗提醒本身已存在）。
- raw 接口经 `read_bytes_checked` → `provider().read()`，整文件读入内存，上限 `MAX_BYTES` 30MB；超出抛 ValueError，被映射成「素材存储不可用」。
- 视频进度面板的播放走 preview-session（已支持分段），素材详情抽屉走 raw。
- 素材详情抽屉原本就走 stream-session（无上限、可分段）；30MB 上限只影响用 raw 接口的地方（视频工作台素材预览、配音试听等），这次统一去掉。
- 视频进度在「已完成」状态不显示播放按钮——成片通过后反而看不到成片，这次一并补上。
- 「在访达中显示」由后端执行 `open -R`，API 跑在 launchd 的用户会话里，可以直接唤起访达；非 Mac 时返回「只能在 Mac 本机上打开访达」。
