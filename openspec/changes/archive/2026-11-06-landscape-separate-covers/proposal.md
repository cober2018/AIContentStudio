# 横版作品封面单独做：交 16:9 横封面 + 3:4 竖封面，不再从成片开头截

## Why
横版视频发抖音等平台时封面单独上传、只在列表里显示，点进去看的是正文，所以封面不必做进成片。抖音主页把封面裁成 3:4，横版作品要多交一张 3:4 竖封面，否则大标题会被切掉。竖版作品（如商品视频）的封面做法用户认可过，不变。

## 需求原文被截断处，我的理解
| 原文 | 理解 |
|---|---|
| 「竖版作品照旧：封面从成片开  来一样」 | 竖版作品照旧：封面从成片开头截、和成片开头比色，和原来一样 |
| 「改完重启 API；README 和 Ope」 | 照旧：「重启吧」才重启；README 和 OpenSpec 规范同步 |

## 怎么区分新旧任务（不动已开出的任务）
只看任务自己的执行包：新开的横版成片任务（导演稿 aspect_ratio 16:9），交付清单里多一个 role `cover_vertical`。平台的新检查、审片页两张并排，都只对带 `cover_vertical` 的任务生效；作品 95 任务 56（已出结果、执行包里没有这个 role）照旧，不改；不碰作品 93。

## What Changes（只对新开的 16:9 成片任务）
1. **交两张封面**
   - 横封面：role `cover`，1920×1080，jpg / png，sRGB。
   - 竖封面：新增 role `cover_vertical`，1080×1440，jpg / png，sRGB。
   - 都导出到 cover_dir（导出/封面），都在剪辑清单之前交；清单 output_hashes 两张都要列（和现在的 cover 一样，重交后清单里的旧记录不算错）。
   - 两张都能在任务通过前重交，新的显示在审片页，旧的留在历史。
   - 成片通过后两张都成为作品封面：主稿 `cover` 增加可选字段 `vertical_material_revision_id`（竖封面），`material_revision_id` 仍是横封面。
   - 「重做封面」对这类任务要两张都重交才算完成，之前「通过」照旧被拦。
2. **不再和成片开头比**：这类任务不跑 `_cover_check`，不出 `cover_color_mismatch`；改为查两张：缺哪张、尺寸不是 1920×1080 / 1080×1440，审片页提示（只提示，不拦交付）。成片开头直接是正文。
3. **角色封面模板**：角色设了 cover_template 时，两张封面的字都用这个模板渲染（交封面带 `cover_template_render`），叠在单独的封面底图上；`cover_template_missing / mismatch` 两张都查。没设就自己做：底图用文生图或素材，大标题用 AE 字层。
4. **写给第三方模型**：video_chain RULES 的封面段分「竖版（照旧）」「横版（开剪结果写明要交 cover_vertical 时）」两种写法；prepare_edit 的 files 说明对这类任务写明交 cover 1920×1080 和 cover_vertical 1080×1440 两张。
5. **页面**
   - 审片页（VideoChainPanel）这类任务并排显示「横封面 16:9」「竖封面 3:4」，没交的写「还没交」；尺寸提示用大白话，比如「竖封面尺寸不对：现在是 1080×1920，应为 1080×1440」。
   - 交付步骤：商品视频的封面处（ProductPublishCopy）横版作品两张都显示、都能下载。**非商品的横版作品（如作品 95）交付页现在没有显示封面的地方**，我在交付步骤顶部加一小块「作品封面」，横版作品显示这两张并能下载（竖版不加，保持不变）。

## 不在范围
- 竖版作品的封面规则、检查、页面不变。
- 已开出 / 已交审的任务不改（作品 95 任务 56 不动，不碰作品 93）。
- 不做数字人，不在封面上放个人形象。

## Impact
apps/api/app/services（video_chain、web_video_handoff、creative_executions、video_documents、creative_mcp 说明），apps/api/app/routers（edit_agent、product_skus），apps/web/src/product（VideoChainPanel、ProductPublishCopy、ProductionWorkspace），规范 video-chain-led-by-mcp-model。
