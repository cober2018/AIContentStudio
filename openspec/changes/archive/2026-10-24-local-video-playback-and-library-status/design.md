## 素材库是否连接

- `library_reachable()` 在原有检查后，再在 `<素材库>/AIContentStudio/` 里写一个 `.probe-*` 小文件并删除；任何报错都算未连接。结果缓存 5 秒，避免每次请求都写盘。
- 读取：要读的文件在素材库里（不在平台本地工作目录）且试写失败 → 抛 `material_library_unavailable`，接口返回 409「素材库未连接」。

## 读取与播放

- raw 接口：本地存储时用文件流返回（Starlette `FileResponse`，自带 Range 分段），不经过 `read(MAX_BYTES)`。
- 校验：按 (路径, 大小, 修改时间) 缓存 sha256 结果；第一次分块计算，之后直接用；不一致仍返回 409「素材字节校验失败」。
- 前端原来用 fetch→blob 的地方不用改，接口返回内容不变，只是不再有大小上限。

## 文件位置

- 素材版本：`GET /materials/{id}/revisions/{rev}/location` → `{path}`；`POST .../reveal` → 后端执行 `open -R <path>`。路径来自该版本的存放记录（`LocalMaterialStorage._path`）。
- 视频进度：`GET/POST .../video-chain/location|reveal`，对应当前展示的小样或成片（已通过的取素材版本位置；待审的小样取 `导出/小样` 里的副本，没有副本则取执行任务里的文件）。
- 文件不存在或素材库未连接时，返回对应提示，按钮旁显示。
- 「复制路径」用浏览器剪贴板，本机 localhost 页面可用。
