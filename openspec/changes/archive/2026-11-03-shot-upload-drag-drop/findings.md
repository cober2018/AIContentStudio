# 发现

- 上传入口只有一处：`ShotWork.tsx` 里的 `upload`（隐藏 file input 的 label），补充镜头和九宫格弹框都用它；上传接口 `POST …/shots/{id}/upload` 收 multipart 的 file，拖入可以直接复用。
