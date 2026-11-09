## Why
审阅与交付列表只能按状态筛，角色内容和商品视频混在一起不好找；交付时想看本地成片文件得自己去硬盘翻；视频作品改了很多版，旧的小样、成片和审阅候选一直留着，占空间也容易看错版本。

## What Changes
- 列表筛选：「状态筛选」旁边加「内容分类」下拉（全部 / 角色内容 / 商品视频 / 搜索推广），按作品的 production_domain 筛，写进网址参数 `domain`，可以和状态、搜索一起用。
- 角色筛选：再加「角色」下拉（全部角色 + 列表里出现过的角色），按作品的 persona_id 筛，网址参数 `persona`。
- 成果文件夹：作品详情「交付与回填」步骤里，在「下载成品包 ZIP」和「回填回执」之间加「打开成果文件夹」按钮。视频作品在访达里选中最新成片文件；没有成片文件的作品打开项目的「导出」文件夹。后端新增一个 reveal 接口，只打开平台记录的路径。
- 定稿后删旧版本（只做视频）：成片点通过、送审冻结成功以后，自动删掉这个作品的旧版本，只留通过的那版成片和它对应的小样：
  - 删除旧的剪辑任务（CreativeExecution）和它们交上来的文件记录（CreativeExecutionOutput），以及只被这些旧文件用到的素材记录。
  - 删除硬盘上这些旧任务的 `工作/<作品>/任务N/` 文件夹，以及 `导出/小样`、`导出/成片`、`导出/封面` 里属于旧任务的文件。
  - 删除这个作品更早的审阅候选和它们的审批记录。
  - 每次删除写一条项目日志（删了哪些版本、几个文件、腾出多少空间），在「历史与变更」里显示。
  - 例外：旧候选如果已经有交付记录（授权、推送、回执），保留这个候选，因为它关系到已发出去的内容和后面的效果复盘。
- 已经定稿的旧作品：提供一次性清理脚本，先列出会删什么，你确认后再真删。

## Impact
apps/api/app/services/video_chain.py（定稿后调用清理）、新增 apps/api/app/services/version_prune.py、routers/edit_agent.py 或 content_projects.py（reveal 接口）、services/project_review_projection.py（历史日志）；apps/web/src/product/ProjectReviewCenter.tsx；一次性脚本放 apps/api/scripts/。

## 追加（2026-11-09，用户确认）：审阅与交付列表变慢、重复读硬盘
- 列表每次打开都把 11 个成片整份重算校验码（约 2.5 GB），并且每个文件都调一次 diskutil 查硬盘身份。
- 改法：同一块硬盘 30 秒内只查一次身份；成片文件大小和修改时间都没变时，沿用已有的「已校验」记录，不再重读。文件改动后照样整份重算。
- 改动：apps/api/app/services/material_external.py（volume_uuid 缓存）、materials.py（verify_bytes_checked 复用已校验记录）。
