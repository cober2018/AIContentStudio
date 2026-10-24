# 科技机会规则与Radar补充 Implementation Plan

> **For agentic workers:** 实施获授权后使用 executing-plans；按以下批次推进，复用本计划，不逐轮重建文件。

**Goal:** 科技长期价值可参评、空结果可解释、Radar与AIHOT共同提供可验证线索。

**Architecture:** 复用现有Discovery/ResearchRun/Opportunity及API/Web；科技显式策略和源集合，不复制选题系统。生活隔离和既有预算不变。

**Tech Stack:** Python API、SQLite、Celery、React、OpenSpec。

## 本轮规格工作
- [x] 读取既有active规格、canonical机会规格及相关实现。
- [x] 写proposal/design、4份delta、实施任务及依赖协调约定。
- [x] 完成strict与diff-check并回写真实结果：单change通过，全量55/55通过。
- [x] 用户授权复核通过后apply；已核对规格、真实实现和dirty范围，无设计阻断。

## 实施批次

最新状态：自动生产6.1–6.3完成，15/17；正式开关已启用，08:00自然日批和生命周期收尾仍开放。下方12/14为前一批历史状态。

/// 自动日报（本轮用户授权）：先将免费本机生成、当日回执和既有前置顺序写入规范；新增services/radar_producer.py处理固定CLI及文件锁/300秒边界；radar_discovery配置与读模型支持auto_daily，catchup在现有来源lease下先生成后导入。日报失败保留类型化缺口，不增加模型调用。复用已有检查和隔离smoke，不新增测试文件；确认Worker空闲再加载，备份后启用科技来源56，记录下一自然日批。

/// 补充执行（2026-10-19用户明确授权）：安装已审阅的Radar 0.4.0，运行免费GitHub/Hugging Face日报；备份SQLite后配置科技Persona2补充来源，由既有scanner导入。关闭所有付费模块，不改生活、日批时间或预算。真实导入与自然选题分开验收；日报生产尚未自动化时必须明确记录，不能把周期性读同一文件称为每日新采集。

执行状态（2026-10-19）：第一至第三批代码完成；第四批81既有回归、隔离smoke、本机只读页面、Web/预算及独立代码复核完成。真实Radar文件与自然日批、依赖协调归档仍待，不以合同检查代替。具体结果见progress.md，任务12/14。

/// 第一批：策略与运行诊断。
范围：apps/api/app/services/daily_opportunities.py，现有研究Run序列化所在discovery路由。显式科技策略、证据类型判断、推荐deadline、分阶段统计。核对10天有正文材料可参评、180天常青需持久价值证明、未知日期不冒充新事件；两次证据分门槛和生活策略保持原样。

/// 第二批：Radar适配与科技多源。
范围：apps/api/app/services/discovery_aggregation.py、discovery_runtime.py及既有来源适配入口。先确认真实上游schema，后做映射；新增文件必须有明确适配职责。验证同一报告重读不增条、两个来源同一原文不多计主体、Radar不可用保留AIHOT与partial；调用次数不因源数增加而突破原预算。无上游输出不得勾选真实接入完成。

/// 第三批：API与页面。
范围：apps/api/app/routers/opportunities.py、services/home_projection.py、apps/web/src/product/OpportunityPages.tsx与DiscoveryPanel.tsx。检查分页/日期/状态组合：昨天有效建议默认可见，过期与无deadline转历史；尚未调度不显示昨天的零结果为今天结论。刷新操作无新任务/模型请求。

/// 第四批：统一验证和交接。
优先运行仓库已有相关检查，不新增测试代码。按上述例子执行隔离或只读冒烟，正式写入/真实Provider调用须沿用明确授权。使用apps/web/package.json声明的build及预算命令，不猜脚本。运行 `openspec validate --all --strict`、`git diff --check`，未跟踪规格另做空白检查。合同检查、真实Radar样本、自然Beat→Worker批次分开记录。复核通过后再申请归档/提交授权。

- [x] /// 2026-10-19只读核实真实自然批、Radar回执/hash/导入/冻结及API/页面，记录失败证据。
- [ ] /// 引文空白误拒与转载日期问题修复后重新自然验收；本次不改代码/数据，不归档。

2026-10-20：自然Run24/25各0条；新增确认_date_proof按UTC日期匹配本地日期引文导致跨日误拒。验收未通过，未修复/重跑/归档，证据见review.md末节。
