## Why

软件运行在用户自己的电脑上，关机、休眠、断网或后台停止会错过来源采集和08:00日批。当前恢复后日批与采集分别排队，可能先使用旧资料生成选题；每源前30条的读取方式也无法判断停机期间是否漏采。

## What Changes

- 恢复运行时，按每个来源上次成功检查的边界补采，保存可续跑的进度与来源覆盖回执。
- 将补采结案设为当天选题的前置条件：先补采，再冻结证据并选题；部分来源补不到时显示缺口，使用其余可用资料继续。
- 对来源公开提供的分页、历史Feed或既有日期游标进行有界回溯；没有历史入口、访问失败、时间未知或达到预算时，明确报告无法确认的区间，不承诺全网无遗漏。
- 对重新启动、任务重投、补采途中再次中断、跨天恢复和当天已经生成等情况保持幂等；不反复生成当天选题、不补造历史日期选题。
- 在现有「运行状态」「信息源储备」「研究记录」中展示补采区间、状态、条目数、缺口及当天选题采用的覆盖快照。

## Capabilities

### New Capabilities
- `discovery-offline-catchup`: 来源补采、持久进度、覆盖证据、每日生成前置顺序、恢复幂等及缺口展示。

### Modified Capabilities
- 无已归档主规范需要替换。此能力在未归档 `add-daily-persona-content-opportunities` 的恢复调度约束上增加前置条件，沿用 `manual-discovery-source-management` 的角色关联和权限。本 change 单独确认、验收、归档，不能作为原日批自然验收的完成证明。

## Impact

- 后端：现有 `discovery_runtime.py`、`discovery_ingestion.py`、`daily_opportunities.py`、`worker_tasks.py` 与 `routers/discovery.py`；新增窄职责补采协调服务及加法迁移。
- 数据：新增补采批次与按来源回执，沿用 DiscoveryItem 去重、Source 租约和 PersonaResearchRun 日批唯一键；保留历史数据与人工选择。
- 前端：扩展现有 `DiscoveryPanel.tsx`，无需新独立页面。
- 沿用本机 API、Celery/Beat、Redis、现有安全抓取与模型接口；不新增常驻云服务或付费搜索供应商。电脑及服务恢复运行后才可执行。
- 本轮仅产出规范与计划，状态为 `SPEC_DRAFT_FOR_REVIEW`；用户确认后才允许 apply。商品直接创作路径不依赖此补采门槛。
