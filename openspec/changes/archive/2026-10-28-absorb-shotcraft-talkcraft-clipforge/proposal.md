## Why

用户认为 video-shotcraft（产品宣传片镜头）和 video-talkcraft（口播讲解动效）的特效非常好用，clipforge 是专门做带货短视频的。三者都不用达芬奇 / AE 渲染（前两个用 Remotion），和平台冲突。用户决定：前两个只吸收配方，换成 AE / 达芬奇做法进剪辑武器库；clipforge 按平台 skill 的边界内化成商品 skill。同时明确：角色和商品是两套独立的 skill 体系，只有剪辑、特效工具 skill 共用。

## What Changes

1. **两套 skill 体系分开**
   - 商品体系：商品 skill（商品脚本、商品镜头、实拍任务书、受众需求、购买理由，以及本次从 clipforge 内化的新 skill），只给商品作品用。
   - 角色体系：其余写作类 skill（选题证据、文字、图文、音频、角色视频脚本与镜头），只给角色作品用。
   - 共用：剪辑和特效 skill（craft-resolve、craft-ae），两边都用。
   - 生效位置：第三方模型读需求时的可用 skill 清单、`get_craft_skill` 读取校验、制作阶段方法的可选列表，都按作品是商品还是角色过滤。
2. **shotcraft + talkcraft → 剪辑武器库（共用）**
   - 按 `craft-arsenal` 的「加新招」流程：提炼两个仓库的配方（shotcraft 125 张镜头卡、talkcraft 108 张动效卡，加节拍、音效、审美规则等参考）→ 和现有条目逐张对照，判定 新增 / 合并 / 替换 / 舍弃 → 保留的换算成 AE / 达芬奇做法写进 `craft-ae`、`craft-resolve` 的 `techniques/`，状态「试用」→ 更新 `choose.md` 问题 → 办法表。
   - 梳理表先给用户看，再写条目。
3. **clipforge → 商品 skill（内化）**
   - 吸收带货短视频的方法：卖点提炼、种草脚本结构、商品原图不变形、各平台（抖音 / 快手 / 小红书 / TikTok Shop）差异、脚本评审。
   - 写法：改进现有商品 skill，没有合适归属的新建商品 skill（同样的平台 skill 包格式）。渲染、Remotion、clipforge 自带的生成和配音流程全部不要，执行仍走平台的导演稿、素材、配音和达芬奇 / AE。
   - 映射表先给用户看，再写 skill。

## 版权与来源

- 全部用我们自己的话重写，不拷贝原文、代码、提示词、素材和音乐；每条注明来源仓库和提交号。
- shotcraft：Apache-2.0，可商用。
- talkcraft：PolyForm 非商业许可，商用需作者授权。本次只吸收思路、自己重写，不使用它的工具和原文；若以后要直接用它的工具或原文，需先取得作者授权。
- clipforge：AGPL-3.0。只吸收方法、自己重写，不拷贝代码和原文。

## Impact

- API：`studio_creative_catalog` 给 skill 标体系（商品 / 角色）；`craft_skills.writing_skills`、阶段方法目录按作品体系过滤；新商品 skill 包放 `app/studio_skills/`。
- 武器库：`apps/api/craft_skills/craft-ae|craft-resolve/techniques/`、`choose.md`、两个 `SKILL.md`。
- 维护记录：`.codex/skills/craft-arsenal/log.md`；源码下载到 `output/`（不进 Git）。
