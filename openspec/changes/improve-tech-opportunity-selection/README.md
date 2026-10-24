# 科技选题规则、空结果说明与Radar补充信源

## PRD / 范围
科技内容按最新动态/近期进展/深度常青参评；页面解释实际空态；Radar仅补充科技AIHOT，不影响生活角色。2026-10-19用户已授权复核通过后合并实施三项。

## 当前阶段与代码位置
IMPLEMENTED / RADAR_AUTO_ENABLED / NATURAL_DAILY_PENDING，15/17。三项代码及页面联动已完成，真实Radar首轮15条线索已由既有后台导入，自动日报已启用；自然日批及生命周期收尾仍开放。
项目 `/Users/mshengran/Project/AIContentStudio`，核查基线main@8539806及保留的dirty工作区。代码位置与实施批次见task_plan.md，不以规格完成代替代码完成。

## 目录结构
proposal.md、design.md、tasks.md、specs/四份delta；task_plan.md、progress.md、findings.md、review.md作为本需求唯一交接记录。

## 已完成 / 待完成
已完成科技策略/跨日建议/空结果诊断、Radar本地日报配置与现有补采接入。81项既有检查、隔离边界smoke、Web构建/预算通过。2026-10-19获授权安装Radar 0.4.0，免费GitHub/HF采集后15条线索由自然scanner导入source56，仅科技Persona2订阅；生活source55未变。自动日报已接现有catchup，沿用08:00日批，先生成导入后冻结评估，不将配置启用等同于自然选题/质量通过。详见progress.md和review.md。

## 关键设计决策
科技专属版本化策略；来源年龄不等于推荐有效期；现有来源模型和运行JSON复用；未分析与不合格分开；所有已有角色隔离、证据及预算边界保留。

## 依赖与启动方式
依赖active的add-daily-persona-content-opportunities与add-aihot-persona-source-integration；不代替它们的未完成验收。沿用本机SQLite/API/Web/Worker，无新依赖/迁移。入口 http://127.0.0.1:5173/opportunities 。现有API/Worker使用launchd标签com.aicontent.api/com.aicontent.worker；不重复启动实例。校验：`openspec validate improve-tech-opportunity-selection --strict` 与 `openspec validate --all --strict`。

## 下一步
实际报告 `/Users/mshengran/Project/new-term-radar/report.json`；免费运行说明见该仓库 `AICONTENTSTUDIO-LOCAL.md`。内容机会→科技角色→配置Radar可查看/关闭自动日报。下次自然计划2026-10-19 08:00台北时间；当天失败/unknown不自动重发。自然选题日批单独验收，协调active依赖再归档，不擅自提交推送。

## 最新自然验收（2026-10-19）
Run20/21各1条，Radar生产→导入→科技参评已实证；引文空白误拒及生活转载日期误标使质量验收未通过。5.2/5.4继续开放，证据见review.md末节。

2026-10-20：自然Run24/25各0条；新增确认_date_proof按UTC日期匹配本地日期引文导致跨日误拒。验收未通过，未修复/重跑/归档，证据见review.md末节。
