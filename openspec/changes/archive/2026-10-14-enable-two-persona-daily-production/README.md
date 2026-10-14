# 两角色日常生产：可直接使用

## PRD / 需求背景
用户授权补齐科技、生活两个角色的日常配置，并从正常页面完整跑通文字、图文和音频。当前六链已真实生成、明确接受、刷新回读；按委托AI质量评审收口。只在本机工作室使用，未push或公开发布。

## 当前入口与成果

| 角色 | 正常项目 | 文字 | 图文 | 音频 |
| --- | --- | --- | --- | --- |
| 科技 | [项目3](http://127.0.0.1:5173/projects/3) | Unit7 / Master24，九阶段Run8完成 | [Unit9](http://127.0.0.1:5173/projects/3/units/9/production)，Master28；3张1080×1440 PNG，素材10/13/12 | [Unit7音频](http://127.0.0.1:5173/projects/3/units/7/production?stage=audio_quality)，素材14；159.679秒，lengdan_xiongzhang |
| 生活 | [项目4](http://127.0.0.1:5173/projects/4) | Unit8 / Master22，九阶段Run10完成 | [Unit10](http://127.0.0.1:5173/projects/4/units/10/production)，Master33；3张1080×1440 PNG，素材15/16/17 | [Unit8音频](http://127.0.0.1:5173/projects/4/units/8/production?stage=audio_quality)，素材18；129.226秒，chunzhen_xuedi |

打开项目即可继续编辑文字、查看图卡和音频；音频原件在项目共享素材中。Text Unit当前显式选择Audio-only Recipe，完整文字Master和此前九阶段历史仍保留；新建同角色Text Unit继承各自Text默认17/19，Graphic继承8/11。制作下一篇时先填写它自己的任务书、来源和事实边界；本次生活内容明确是假想场景，不能把其事实包用于其他事实。

## 目录结构
proposal/design/specs为确认范围；tasks/task_plan是同一持续计划；progress/findings/review记录实情；receipts/current-artifacts.json给精确Master、素材、SHA和正常URL；receipts/configuration-readback.json及preservation-readback.json给正式配置和保全实读；六类子目录保存当前成品/阶段/质量证据。私有数据库和素材备份在被忽略的backups/daily-production-20261014.6kc8s1o0/，不入Git。

## 已完成
- 两Persona修订4/5保存真实音色，Audio明确绑定speech-2.8-hd/rate1；正常Text/Graphic defaults及项目Audio覆盖实际回读。
- 两篇文章各9/9、两组图文各4/4、两条音频各4/4明确接受；6张真实PNG、2份完整WAV和9个精确素材引用的实际字节SHA通过。
- 当前最终QC62/60/72/78/75/79均零阻断。文字SEOpartial、图文视觉语义unavailable原提醒逐项处理，保留warning；Audio当前QC pass。
- 两音频独立全文件离线ASR/声学通过，clipping均0；对稿98.806%/96.940%，识别差异如实保留。没有直接试听，human_review_required保留。
- 仅四个现有源码文件最小修复独立通过：FactPack模型使用许可控件及Text明确设封面。10既有后端/9既有前端检查、Web构建/FE-P1/Ruff通过；本轮未新增测试。
- 482旧行、53旧素材、三归档263文件、65相邻文件和运行配置逐项保全。新增487行；实际26注册模型+2image+2TTS，另22语义QC保守预留，总52≤80，Unknown0。科技一次生图质量不合格未采用，原任务保留；一个准备任务未发送。

## 待完成 / TODO
本需求生产配置及六链验收已完成；独立六项质量复核已接受，18/18任务关闭；规范已同步并归档，strict43/43，白名单本地提交记录见review/progress及Git最后一条提交。人类试听、商业授权、远端账号验证与公开发布不在本次已完成声明中。

## 关键设计决策
科技是有条件、有成本边界的架构观点，不伪造实测；生活明确假想，不伪装亲历或宣称健康疗效。素材public/model=true、commercial=false。Audio不是新ContentUnit形态，沿用已接受Text Unit中的项目Recipe；不回填旧Run、不重发Unknown、不放宽平台封面/结构/权限门禁。源码只涉及fact_packs.py、FactPacks.tsx、TextStudioModel.ts、TextStudioShell.tsx。

## 依赖与启动方式
沿用现有API8000/Web5173、CPA Gemini、MiniMax、Chromium renderer及已缓存离线MLX ASR；无新依赖、迁移或部署体系。API ready=true、Web200，常规启动见[本机手册](/Users/mshengran/Project/AIContentStudio/docs/runbooks/production-readiness.md)。

## 版本与下一步
基线main@6ff0d7ac02045c752436d8c2261e6862a3f2a19f。根保留全部相邻未提交修改；本change已归档，采用提交标题“Complete two-persona daily production through normal UI”选择性本地提交，不push。以后可从上述两个项目进入日常创作，保留真实证据/权限和明确采用步骤。
