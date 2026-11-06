# 进门 / 收尾片段从「品牌」搬到「角色」上

## Why
上一版（9533684，archive/2026-11-05-brand-intro-outro-clips）把片段放在品牌上，成片时按 作品 → 角色 → 品牌 找。用户确认片段要按角色配：同一品牌下不同角色可以用不同片段。品牌上的这块直接删，不留「角色没设就用品牌」的兜底。

## 需求原文被截断处，我的理解
| 原文 | 理解 |
|---|---|
| 「已交审或已完成的作品不改：  品 93」 | 已交审 / 已完成的作品不改（含作品 93、94）；已开出的剪辑任务不补片段 |
| 「角色编辑页能选、预览、清空  看到」 | 角色编辑页能选、预览、清空，只读页能看到 |
| 「量化研究专家的作品开成片任  尾 4.2秒…」 | 量化研究专家（16:9）的作品开成片任务，结果写「已加角色收尾 4.2 秒（知数Talk收尾_深墨_横版，素材 618）」 |
| 「改完重启 API；README 和 Ope」 | 按老规矩：「重启吧」才重启；README 和 OpenSpec 规范同步更新 |

## 现状（已查）
- 执行包里带 `brand_clips` 的剪辑任务：0 个；已存的成片检查结果里带 `brand_*` 提示：0 条。所以直接改名，不留旧名字。
- 知数Talk（品牌 6）第 2、3 版资料里有 `outro_clip`（横竖都是 617）。
- 素材版本 618（1920×1080）、619（1080×1920）：视频、4.2 秒、admin 自己的、可公开、可给模型用，能通过检查。
- 量化研究专家（角色 6）当前资料没有封面模板，也没有片段。

## What Changes
1. **角色资料**（`content_identity.IdentityProfile`）加 `intro_clip`、`outro_clip`，格式同原品牌：`{"16:9": revision_id, "9:16": revision_id}`，都可不填。保存检查照搬原 `_brand_clip`，改名 `_persona_clip`，提示里「品牌」改「角色」。
2. **品牌资料**（`BrandProfile`）删掉这两项。读旧版本资料时把这两个旧字段丢掉，不报错；保存时不再接受。
3. **接口**：新增 `GET /content-personas/{id}/clips`，删除 `/content-brands/{id}/clips`。
4. **页面**
   - `BrandClips.tsx` 改名 `PersonaClips.tsx`，只留一份；角色「编辑资料」页在「封面样式」旁边加「收尾片段」「进门片段」，照 `PersonaCoverTemplate` 的做法，存成角色资料新版本。
   - `IdentityProfileView` 显示这两项（片段名 + 时长），`KNOWN` 加上这两个字段。
   - 品牌设置页删掉片段这块，保存不再带片段。
5. **成片自动加片段**（只在 final，小样不加）：从作品的角色（`unit.persona_id`）当前资料按画幅取片段；没角色或没设就不加。挂项目素材、放进执行包的做法不变。
6. **改名**（规则不变，只改名字和文字）：
   | 原来 | 改成 |
   |---|---|
   | `director.brand_clips`、剪辑清单 `brand_clips`、开剪结果 `brand_clips` | `persona_clips` |
   | 素材 role `brand_clip` | `persona_clip` |
   | `brand_note`、「本作品没有品牌收尾」 | `persona_note`、「本作品没有角色收尾」 |
   | 提示码 `brand_duration_mismatch`、`brand_clip_mismatch`，清单错误码 `video_edit_manifest_brand_clips_mismatch` | `persona_duration_mismatch`、`persona_clip_mismatch`、`video_edit_manifest_persona_clips_mismatch` |
   | 审片页「已加品牌收尾 / 进门」、挂素材备注「品牌收尾片段」、RULES 里「品牌片段」 | 「角色」 |
   涉及 video_chain、web_video_handoff、creative_packages、creative_executions、delivery_checks、routers/edit_agent、routers/content_identities、VideoChainPanel，及规范 video-chain-led-by-mcp-model。

## 上线时改的数据（等「上线」，先备份）
- 知数Talk 存一个新版本资料，不带 `intro_clip` / `outro_clip`。
- 量化研究专家存一个新版本资料：`outro_clip` = {"16:9": 618, "9:16": 619}，不设进门。
- 素材 576 / 617 留着不删。

## 不在范围
- 已交审 / 已完成的作品不改；已开出的剪辑任务不补片段。
- 小样不加；不改导演稿；片段接法、声音、时长与画面抽查、封面后移的规则不变。
