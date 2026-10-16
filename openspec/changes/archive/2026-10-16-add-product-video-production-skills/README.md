# 商品视频Skills与AE/Resolve适配

## PRD / 需求背景

将用户提供的六组商品视频Skills按本平台流程拆解，形成自己的分阶段方法，保留角色独特风格并适配本机达芬奇和AE。

## 当前阶段、代码与版本

v2 ARCHIVED_CONFIRMED_LOCAL_COMMITTED，2026-10-16；隔离工作树codex/product-video-production-skills基于main@4a1f212并保留相邻基线。20/20已完成；正式登记、回收与最终复核通过，规范已归档，并已选择性提交本机main（最终版本以Git HEAD为准）。

## 目录结构

proposal.md目标范围；design.md分工/流程图；specs/行为标准；tasks.md二十项实施任务；task_plan.md唯一持续计划；research.md/source_inventory.json来源与快照；progress.md/findings.md/review.md实际进展、决策与审查。

## 已完成

六仓库README与重点子Skill核查、固定commit/hash来源清单；六项商品方法映射、十阶段复用及原生AE/Resolve适配设计。补充实际源码适配复核：首轮前冻结方法、确定性节点适用性、参考图路由退路、结构化促销/静态截止时间、完整方法卡与原生接口边界。方案strict和审查结果见progress。

## 待完成 / TODO

本需求20项均已完成；主规范同步/归档和选择性本地提交已完成，无push。样片不代表商品事实/肖像公开授权、直接试听或默认风格采纳。

## 关键设计决策

商品是任务类型，不增设商品Persona。六项专用方法叠加角色风格，现有后期复用；阶段独立开关，默认不覆盖科技/生活普通创作配置。图片确认后才写据图视频提示词；用户人工网页生成，Codex平台CLI/MCP、Resolve主剪和终混、AE按需包装。

## 依赖与启动方式

沿用根README中的本机API/Web和现有AE/Resolve MCP，不新增服务/渲染引擎。方案检查：openspec validate add-product-video-production-skills --strict。当前无需启动或重启服务。

## 下一步

可直接通过正常商品入口创建下一作品；本次样片用于本地流程验收。每日选题自然验收change继续独立保留，不随本次归档。

## 懒人沙发实际样片

用户原图，生活Persona3；16秒、1080×1920、30fps。真实正常商品入口创建Project8/Unit14/Run18；首轮真实模型稿、角色音色配音、三段AE可编辑合成、Resolve主剪/分轨配乐终混与8项合同产物已完成并回传。正式导入恰好也是Project8/Unit14：既有作品同字节导入，未再调用模型或重渲染；正式Master41/执行2已接受8/8产物并仅本地绑定。

成片：`/Users/mshengran/DaVinci Resolve Media/AICS-Product-Skills-20261016/sofa-delivery.mp4`；AEP/DRP与原图/旁白/音乐依赖同目录保存；实际重开均缺失媒体0。私有正常API回执：根目录backups/product-video-sample-20261016/state.json；不提交业务数据库或媒体。

独立AI质量接受本次单图二维本地测试：无形变、黑帧或未经证实性能/价格。完整ASR匹配旁白；字幕细分估算，未直接试听，当前−22.2 LUFS偏轻。公开使用仍受门禁保护。

## 正常页面使用步骤

| 步骤 | 页面与操作 |
|---|---|
| 商品输入 | 内容项目 `/projects` → **从商品创作**；选择角色、视频形态，填写商品说明，上传/选择原图。未知参数留空；促销资料按需开启。 |
| 选择方法 | 展开 **本次商品创作的阶段方法**；research选“商品事实底稿”、script选“带货叙事”、storyboard选“一致性/镜头路由”、packaging按需选“演示/促销动效”。每阶段可多选/排序/关闭；在“开始创作”前决定。 |
| 脚本和来源 | 点 **开始创作** 后进入共同Recipe生产页；审阅脚本与镜头计划，在“来源与证据”确认实际事实，在“商品素材”检查图片。商品说明不会自动成为已核实事实。 |
| 画面素材 | 原图裁切/标注可直接给AE；需要图生视频时先确认精确图片，再据图写动作提示词，由用户网页生成并回传原MP4。复杂功能优先实拍。 |
| 配音与后期 | 视频单元Director/创作交接设置旁白、字幕、配乐或无音乐，再准备后期任务。Codex只用CLI/MCP领取冻结方法；Resolve声音→节奏→字幕/校色，AE按需包装，回Resolve终混导出。 |
| 成片回收 | 同一“创作交接”查看/预览产物，质量通过后接受，再绑定本地主稿；公开使用另过Candidate/发布门禁。角色默认不会被当前任务覆盖。 |

现有样片入口：[懒人沙发项目](http://127.0.0.1:5173/projects/8?tab=overview) → 内容矩阵 → 视频单元；[生产页](http://127.0.0.1:5173/projects/8/units/14/production)。成片已绑定Master41，8项接受产物可在创作交接查看。正式导入项目保存已有作品，不冒称又运行了一次首稿模型。

## 正式保全与提交边界

备份：根目录`backups/product-video-formal-enable-20261016/`，SQLite完整性ok/catchup000001；42旧素材引用→36文件全部复制验hash，153旧媒体文件未改。2786旧行无删除；仅既有后台日批更新2个运行时钟设置，其余旧行原样，Persona2/3全部修订回读一致。正式新增六项方法、一个商品作品及8项接受产物；无新迁移执行、无新模型调用或重渲染。

纯候选从4a1f212独立构建：24个必要代码/原迁移路径，564项既有检查通过/1跳过、Web/API导入/迁移链与独立审查APPROVE；排除日批hook/runtime/worker/相邻渠道与栏目。当前运行工作树仍包含这些相邻工作，不能以其dirty状态替代提交树验收。

归档后纯候选OpenSpec strict：47 passed / 0 failed。最终提交50路径；完整文档与方法来自本需求，代码24路径按最小闭包独立复核。公开Candidate仍不可冻结（事实/权限与人工音频检查未满足），这与已接受的本地样片范围一致。

实际使用Skills：using-superpowers、openspec-apply-change、executing-plans、subagent-driven-development、using-git-worktrees、writing-skills、video-production-handoff、openspec-archive-change、finishing-a-development-branch。
