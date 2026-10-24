# 停机补偿 Implementation Plan

> 执行阶段使用 `superpowers:executing-plans`，沿用本计划与tasks；用户已确认开发、备份、恢复验收及归档；沿用同一清单。

**Goal:** 恢复后先补采，再生成当天选题，无法补全的来源和区间明确可见。

**Architecture:** 复用来源采集器、Beat和研究日批，以持久化的批次与分源回执作为当天证据冻结的前置条件。

**Tech Stack:** FastAPI / SQLAlchemy / Alembic / Celery / React；本轮只写Markdown规范。

## 规范阶段

- [x] /// 定向核对当前调度、30条上限、日期及幂等路径。
- [x] /// 写proposal/design/specs/tasks并自审一致性。
- [x] /// OpenSpec strict检查通过，方案提交用户确认。
- [x] /// 用户明确确认，已进入apply。

## 实施步骤与责任路径

### A. 持久化（tasks 1）

文件：`apps/api/app/models.py`；在现有`apps/api/alembic/versions/`增加迁移；新增`apps/api/app/services/discovery_catchup.py`仅负责窗口、回执、预算和前置判断。

- [x] /// 备份，恢复副本演练加表，核对旧业务数据保全。
- [x] /// 实现owner/窗口/来源唯一约束及原子进度，重复扫描复用同一任务。

### B. 历史读取（tasks 2）

文件：`services/discovery_ingestion.py`与补采服务；必要时兼容`services/discovery_sources.py`，复用`url_fetch.py`而不重构。

- [x] /// 拆开解析上限与存储分块，实现显式分页、持久游标与请求预算。
- [x] /// 实现覆盖判定和原因；85条可采全，截断/未知必须partial。

### C. 执行先后（tasks 3）

文件：`apps/api/app/tasks/worker_tasks.py`、`services/discovery_runtime.py`、`services/daily_opportunities.py`。

- [x] /// 调度和Worker共用前置条件，未结案时释放执行权。
- [x] /// 角色依赖结案后冻结快照；保全已生成、跨天、已开始模型阶段的历史和调用账本。
- [x] /// 处理共享来源、撤权和别名归并。

### D. 页面与验收（tasks 4–5）

文件：`apps/api/app/routers/discovery.py`、`apps/web/src/product/DiscoveryPanel.tsx`及本目录成果和根README。

- [x] /// API与原页签展示等待、区间和缺口，核对owner隔离及只读无触发。
- [x] /// 运行相关既有后端检查（apply时核对具体用例并记录命令）及`npm --prefix apps/web run build`，预期退出0；不新增测试或示例代码。
- [x] /// 隔离真实服务停启，回读证明补采finished_at不晚于尚未开始日批的证据冻结时间，记录自然恢复来源。
- [x] /// 按明确授权接入正式服务并验收，全部通过后同步主规范并archive。

## 文档检查

`OPENSPEC_TELEMETRY=0 openspec validate add-discovery-offline-catchup --strict`

`OPENSPEC_TELEMETRY=0 openspec status --change add-discovery-offline-catchup`

预期strict通过且四份制品完成，仅表示文档齐备，不代表已批准实施。
