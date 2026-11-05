# 付费生成前先查素材库盘

## Why
2026-11-05 作品 95（项目 50）调用 `generate_video_voiceover` 时，素材库盘没接上。平台先调了 MiniMax 配音（已计费，`logs/api.log` 2026-11-05 02:05:02 `POST https://api.minimaxi.com/v1/t2a_v2` 200），到存文件时才报 `material_library_unavailable`，配音结果丢了。

另外，MCP 只给第三方模型回了 `creative_domain_conflict`，看不出原因是素材库盘没接。生图、九宫格、图生视频也是先调供应商再存文件，有同样的问题。

## What Changes
- **调用供应商前先查盘：** project_folders 里加一个检查，复用 `storage_locations.library_writable`。素材库不可写时，直接返回 409 `material_library_unavailable`，提示「素材库盘没连接」，不调用供应商。
- **用到这个检查的付费生成入口（在调用供应商之前）：**

  | 生成内容 | 入口 | 覆盖的调用方 |
  |---|---|---|
  | 配音 | `voiceover.generate` | MCP、剪辑助手接口 |
  | 生图 | `material_autofill._Images.make` | `generate_video_image`、素材自动补齐 |
  | 镜头图 | `product_video.generate_shot_image` | MCP、网页 |
  | 图生视频 | `product_video.start_shot_video` | MCP、网页、素材自动补齐 |
  | 九宫格 | `shot_image.grid` | MCP |

- **MCP 透出原因：** 把 `material_library_unavailable` 加进可以透出给模型的错误码，提示原样给到模型。

## 不在本次范围
- 不补回已经丢失的配音，也不重新调用。
- 其他不花钱的写盘操作不变。

## Impact
- 代码：`apps/api/app/services/{project_folders,voiceover,material_autofill,product_video,shot_image,creative_mcp}.py`
- 生效要重启 API。
