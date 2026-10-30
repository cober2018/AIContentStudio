# 进度

## 2026-10-29 本地实施（未提交）

已完成：
- 角色资料 `IdentityProfile.portrait_material_revision_ids`（≤3，去重）；`save_revision` 校验：只能角色用（品牌 / 账号 / 栏目 422 `portrait_persona_only`），每张须是本人上传、允许模型使用、未撤回的图片（422 `portrait_invalid`）。旧修订没有这个字段照常读。
- 新接口 `GET /content-personas/{id}/portraits`（当前修订的形象照 + 素材号 + 是否还能用，给页面显示缩略图）。
- 前端新文件 `PersonaPortraits.tsx`：`uploadPortrait`（`/materials/upload` → `/materials/{id}/to-common`，标签「形象照」）、`PortraitPicker`（新建表单，照片先传再建角色）、`PersonaPortraitEditor`（编辑资料，增删即存新修订）。`NewPersonaForm`、`IdentityWorkspace`（抽出 `sideRevisionSaved`，参考风格和形象照共用）。
- `product_video.references()`：作品「共同视觉参考」手动选的优先；否则商品取 SKU 主图、人物取角色当前修订里仍可用的形象照；`person_notices()`、`person_rule()`。
- 首帧 `generate_shot_image`：参考 = 商品 + 形象照 + 场景 + 额外参考；提示词加人物规则；没形象照的人物镜头返回 `notice`。
- `shot_prompt`（get_shot_video_prompt / 图生视频）：首帧兜底用 `references()` 的商品图；没形象照时去掉 attitude、视频提示词（中英）和首帧提示词加「不出现人物，只露手」，返回 `references`、`notice`。
- 九宫格 `shot_image.grid`：自动带商品主图 / 形象照 / 场景；`grid_prompt` 按有无形象照写人物；每格 `check(..., absent_ok=True)`，不过关用该格分镜图作参考单独重画，总共最多 3 次；结果多 `references`、`person_notices`、`hints`（商品纯特写建议单独生成）、`consistency_failed`。去掉 `shot_grid_product_shot`，亮相 / 下单引导 / AE 模板 / 素材库镜头仍拒绝（新码 `shot_grid_original_only`）；默认选镜头不含商品纯特写。`redraw_cell` 同样带参考并检查。
- `GET /product-video` 多 `references`、`person_notices`；九宫格候选带 `consistency`。`direction.rules` 加一条人物规则；`persona_brief` 加 `portrait` 和对应规则。MCP 工具说明更新（generate_shot_image、generate_storyboard_grid）。`studio.video.prompt-direction@1` 文案同步。
- 页面 `StoryboardGridPanel`：显示参考来源、没形象照的人物镜头提示、每张候选的商品对照结果。

验证：
- 后端 `pytest -q`：5 failed（已知基线 5 个）、2466 passed、28 skipped。
- 前端 `tsc --noEmit` 通过；`node --test` 37/37；`npm run build` 通过。
- 重启 API 实测：角色 5（懒羊羊小王）effective 正常（旧修订无新字段），`/portraits` 为空；项目 42 作品 83 `GET product-video`：`references` 商品 / 人物都为空，`person_notices` 标出 shot-1、shot-5；shot-1 提示词带 notice 和「不出现人物」；`persona_brief.portrait=False`。
- 未调用任何付费生成；没给任何角色上传真照片。

未做：页面点击实测、真实生图验收（付费）、归档。

## 2026-10-29 复核修正
- `product_video._people` 不再把「手」算人物（没形象照也允许拿商品的手部特写），加上 博主 / 妈妈 / 爸爸 / 孩子 / 宝宝 / 小朋友 / 女孩 / 男孩。后端 `5 failed, 2466 passed`（5 个已知失败）。

## 2026-10-29 用户试用后修正
- 商品主图入口：商品工作台 → 商品 →「商品资料」里原叫「商品原始图片」，改名「商品主图」并加说明；上传时默认允许给模型和公开使用（自家商品原图），不再默认禁用。
- `references()`：作品发起时那版商品资料没有主图时，取这个商品最新一版有主图的资料，后补的主图也能用上。
- 作品 84 配音报 `master_context_conflict`：删「按阶段制作音频」前保存的导演稿，作品环境指纹包含已删的音频配置；已把 84 的导演稿按当前环境原样重存一版（v10 → v11，内容不变），小样状态不变。删之前保存的导演稿只有 84 这一条受影响。
- 验证：后端 `5 failed, 2466 passed`；tsc、build 通过。

## 2026-10-29 九宫格试用后修正
- 用户点「九宫格分镜」后页面停在「生成中…」、没有新图：请求同步跑了约 2 分钟（22:25–22:27），生图返回后裁切时报 `shot_grid_layout`（比例不对或找不到格线），整张图还没保存就失败了。
- 改为后台生成：`shot_image.start_grid` 记 `grid_run`（running / done / failed、整张图文件名、没进九宫格的镜头、失败原因），页面每 4 秒刷新；同一作品正在生成时再点会被拒（15 分钟后视为中断）。MCP 的 `generate_storyboard_grid` 仍同步。
- 整张分镜图先保存再裁切，失败也保留；新接口 `GET …/product-video/storyboard-grid/sheets/{name}`，页面显示最近一次的整张图，可点开看大图。
- 裁切：提示词改为格间细白线；找不到格线或比例不对时按三等分裁，再按镜头比例居中裁切放大，不再整张拒绝（每格仍对照商品主图检查）。
- 生成结束时重新读取作品记录再写入候选，避免覆盖生成期间用户的选择。
- 页面写明没进九宫格的镜头及原因；候选按时间最新在前。
- 测试：`test_storyboard_grid_refuses_a_sheet_that_is_not_a_grid` 改为验证三等分兜底。后端 `5 failed, 2466 passed`；tsc、node --test 37/37、build 通过。

## 2026-10-29 九宫格第二次失败：生图服务超时
- 现象：后台运行约 3 分钟后失败，报 Cloudflare 524。请求从平台发到本机生图中转（8317），中转的上游在 Cloudflare 后面，等模型出图超过网关时限就断开。平台这边的后台运行、轮询和报错显示都正常。
- 改动：`shot_image.generate` 遇到超时或 502/503/504/52x 时，报「生图服务超时，这次没出图，可以过几分钟再点一次」，不再显示 Cloudflare 原始 JSON。
- 没有自动重试：524 时上游可能已经出图、已经计费，重试可能重复扣费。
