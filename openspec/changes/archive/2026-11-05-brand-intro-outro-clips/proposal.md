# 品牌进门 / 收尾片段：品牌上设置，成片自动加上

## Why
用户在别的项目里单独做品牌 Logo 动画视频，希望存在「品牌」上，成片时自动加进去；作品没有品牌或品牌没设置就什么都不加。主要用收尾片段（放成片最后）；进门片段也提供设置，但担心完播率，暂时不用。适用所有视频作品。
关系：作品 → 角色（content_persona.brand_id）→ 品牌（content_brand）。例：量化研究专家(6) → 知数Talk(6)；懒羊羊小王(5) → 母婴博主nina(2)。

## 需求原文有几处被截断，我的理解（请确认）
| 原文 | 理解 |
|---|---|
| 「assets 角色写 b」 | 执行包 assets 里这几条的 role 写 `brand_clip`，slot_key 写 `intro` / `outro` |
| 「director 里写明多少」 | 执行包 director 里写 `brand_clips: [{slot, material_revision_id, duration_ms, title}]`，写明每段多长 |
| 「没有品牌、没有设 … 不加」 | 作品没有品牌、品牌没设、或没有这个画幅的片段：都不加，开剪结果写「本作品没有品牌收尾」 |
| 「收尾片段接在最 … 变速」 | 收尾片段原样接在成片最后，不裁、不变速、不缩放变形 |
| 「用片段自带的声 … 完」 | 片段这段用它自带的声音；配音和配乐在片段开始前收完（配乐淡出），不压在片段上 |
| 「进门片段（设置了 … 面改成从进门片段结束后 0.5 秒内截，_cover_che…」 | 设了进门片段时，进门片段放最前面；封面改成从进门片段结束后 0.5 秒内截，`_cover_check` 也改成比这一段 |
| 「抽查成片最后（或 … 一致时在审片页提示」 | 抽查成片最后（有进门片段时也查最前面）那段和品牌片段比画面，不一致时在审片页提示 |
| 「不改导动画」 | 不改导演稿，平台不做 Logo 动画 |

## What Changes
1. **品牌设置**（`content_identity.BrandProfile`，和 logo 放一起）
   - 新增 `outro_clip`、`intro_clip`，各自 `{"16:9": material_revision_id | null, "9:16": material_revision_id | null}`，都可不填。
   - 保存时检查：素材是当前用户的、是视频、可公开使用（public_use_allowed 为是）、允许给模型用（执行包要求）、时长 ≤ 5 秒；不满足就拒绝并说明原因。
   - 品牌设置页加这两项：从素材库选视频（按标题搜、只列视频）、可预览、可清空。
2. **成片自动加上**（只在 `prepare_video_edit(phase=final)`，小样不加）
   - 按作品角色找到品牌，取和作品画幅相同的片段：自动挂到本项目素材，放进执行包 assets（role `brand_clip`）和 `director.brand_clips`；开剪结果写明加了哪几段、各多长，或「本作品没有品牌收尾」。
   - `video_chain` 剪辑说明写清第三方模型在达芬奇里怎么做（见上表）；整片响度照旧（约 −14 LUFS、真峰值 ≤ −1 dBTP）。
   - 剪辑清单（edit-manifest）新增 `brand_clips: [{slot, material_revision_id, start_ms, end_ms}]`；这几段不是导演稿镜头，不进时间线和镜头校验。
3. **平台检查**（只提示，不拦交付，方式同 cover_check / shot_checks；清单格式错误除外）
   - 执行包有品牌片段时，清单必须写 `brand_clips`，素材和时长要对得上（±1 帧），否则清单被拒。
   - 成片时长应等于通过的小样时长 + 片段时长（±1 帧），不符在审片页提示。
   - 抽查成片最后（有进门片段时也查开头）和品牌片段的画面，不一致在审片页提示。
   - 审片页成片区域显示「已加品牌收尾 X 秒（素材名）」（有进门片段时同样显示）。

## 不在本次范围
- 已经交审或完成的作品不改（作品 95 任务 56 不动），不碰作品 93；已开出的剪辑任务不补片段。
- 小样不加；不改导演稿；平台不做 Logo 动画。

## Impact
- 后端：`content_identity.py`、`video_chain.py`、`web_video_handoff.py`、`creative_packages.py`、`creative_executions.py`、`delivery_checks.py`、`routers/edit_agent.py`。
- 前端：品牌设置页（`BrandProfile.tsx`）、`VideoChainPanel.tsx`。
- 生效要重启 API；不改表结构。
