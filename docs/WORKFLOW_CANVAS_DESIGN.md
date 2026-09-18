# 工作流画布（Workflow Canvas）设计方案

> 状态：设计稿 V1（待确认后实施）· 2026-09-18
> 定位：仿扣子（Coze）的 Agent 工作流画布——把 Studio 已有能力点串成**可执行、可视化、结果沉淀回既有实体**的编排层。

---

## 0. 设计原则（三条铁律）

1. **节点 = 已有能力的编排壳**：拉取、抽取、荐题、生成、校验、导出全部复用现有 service 函数，画布不重写任何业务逻辑。这样能力点在「页面点」和「画布跑」行为完全一致。
2. **结果只沉淀到既有实体**：节点产物永远是 Source / FactPack / Topic / Draft / Asset，画布只存「哪一步产出了哪个实体 ID」。不在工作流里造第二套存储。
3. **人工节点是一等公民**：确认事实、采纳选题、审核批准这些"人在回路"的环节，画布执行到该类节点时**暂停**（run 状态 waiting_input），节点上直接内联操作，完成后引擎从断点继续。这是内容生产区别于纯 Agent 自动化的关键。

## 1. 总体架构

```text
┌─ 前端 /workflows ─────────────────────────────────────────────┐
│  左：工作流列表（模板实例化 / 我的画布）                        │
│  中：React Flow 画布（节点着色 = 运行状态；点节点 = 配置+结果） │
│  右：检查器面板（节点配置 / 运行结果 / 产物链接）               │
└──────────────────────────────────────────────────────────────┘
            │ POST /workflow-runs/{id} 启动 · 轮询/推进
┌─ 后端引擎 ────────────────────────────────────────────────────┐
│ Workflow（定义）→ WorkflowRun（一次执行）→ WorkflowStep（步）  │
│ 引擎：拓扑遍历 → 节点 handler 分发 → 人工节点挂起 → 断点续跑    │
│ handler 全部薄封装现有 service（见 §3 节点清单）               │
└──────────────────────────────────────────────────────────────┘
```

## 2. 数据模型（三张表，复用 SQLite/PG + Alembic）

```text
workflow            # 画布定义
  id, name, description
  definition_json   # {nodes:[{id,type,label,params}], edges:[{from,to}]}
  template_key      # 内置模板标识（daily_suggest / gen_review_export / null=自定义）
  enabled, created_by, created_at

workflow_run        # 一次执行
  id, workflow_id, status        # running / waiting_input / succeeded / failed / canceled
  context_json      # 跨节点共享状态：{source_ids, fact_ids, pack_id, topic_id,
                    #  job_ids, draft_ids, asset_ids, media_ids, suggestions...}
  params_json       # 启动参数（如指定 pack_id / topic_id / 输入源）
  error, started_at, finished_at

workflow_step       # 每个节点的一次执行记录
  id, run_id, node_id, node_type, label
  status            # pending / running / waiting_input / succeeded / failed / skipped
  input_json, output_json        # 入参与产物摘要（实体 ID 列表 + 关键指标）
  error, started_at, finished_at
```

要点：**run 的 context 就是节点间的数据总线**。每个 handler 从 context 取上游产物 ID，执行后把新产物 ID 写回。不搞隐式传参，检查器面板能看到每步的真实进出。

## 3. 节点清单（V1 全部复用现有能力）

### 自动节点

| 节点类型 | 封装的后端能力 | 关键参数 | 产物（写回 context） |
|---|---|---|---|
| `connector_pull` 数据拉取 | `connector_service.pull_endpoint`（generic_rest / local_git / dtk 归档） | endpoint_id | source_ids |
| `extract_facts` 事实抽取 | `sources/{id}/extract-facts` 同逻辑 | source_ids、自动确认阈值 | fact_ids |
| `factpack_freeze` 打包冻结 | factpack create/add/freeze 同逻辑 | name、fact_ids 或来源 | pack_id |
| `suggest_topics` AI 荐题 | `topic_suggest.suggest_for_pack`（**走 topic_discovery 场景路由**） | pack_id、count | suggestions |
| `generate` 内容生成 | `dispatch_generation`（三渠道独立 job，**走 generate 路由**） | topic_id、channels | job_ids, draft_ids |
| `fact_check` 事实校验 | draft fact-check 同逻辑（**走 fact_check 路由**） | draft_ids | 检查结果摘要 |
| `export` 导出 | exports + ExportRecord | asset_id、formats | 文件列表 |
| `skill` 技能调用 | 设置页已登记的 skills / MCP（wewrite-*、dsh） | skill_name、输入输出映射 | 按 skill 定义 |
| `publish_wechat` 公众号草稿箱 | wewrite publish 封面+草稿（已验证可用） | asset_id、cover_media_id | media_id |

### 人工节点（执行到即暂停）

| 节点类型 | 内联操作 | 完成动作 |
|---|---|---|
| `confirm_facts` 确认事实 | 节点弹层勾选候选事实（确认/拒绝） | 确认结果写回 fact_ids → 继续 |
| `adopt_topic` 采纳选题 | 候选卡片点采纳（预填表单可改） | 创建 Topic → topic_id → 继续 |
| `approve` 审核批准 | 节点显示 FactCheck 摘要 + 跳审核中心；或内联批准 | 走既有 approve（409 闸门不变）→ asset_id → 继续 |

### 条件节点（V2）

`condition`：如「blocker 数 = 0」「新增视频数 > 0」走不同分支。V1 用线性模板 + 失败即停覆盖 80% 场景。

## 4. 执行引擎（后端，无新依赖）

```text
start_run(workflow, params)
  → 建 run + steps(pending)
  → 引擎循环：取入度满足的 step → handler(params, context)
      自动节点：同步执行（复用现有同步模式；TASK_QUEUE_ENABLED 时可派 Celery）
      人工节点：step=waiting_input、run=waiting_input → 返回，等 complete API
      失败：step=failed、run=failed（可从失败节点重试，不回滚上游产物）
complete_node(run_id, node_id, payload)
  → 人工节点结果写 context → 引擎从断点继续
```

API：

```text
POST /api/v1/workflows                 # 从模板或定义创建（admin）
GET  /api/v1/workflows                 # 列表
POST /api/v1/workflow-runs             # 启动（editor），{workflow_id, params}
GET  /api/v1/workflow-runs/{id}        # 运行详情（steps + context + 实体链接）
POST /api/v1/workflow-runs/{id}/nodes/{node_id}/complete   # 人工节点完成（editor）
POST /api/v1/workflow-runs/{id}/retry  # 从失败节点重试
POST /api/v1/workflow-runs/{id}/cancel # 取消
```

权限：跑工作流 = editor；建/改画布定义 = admin；人工节点操作沿用各业务既有角色（approve 仍需 reviewer）。

## 5. 前端（React Flow 12，MIT 协议，`@xyflow/react`）

- **画布态**：节点卡片显示图标+名称+状态色（灰待执行 / 蓝运行 / 绿成功 / 黄等人工 / 红失败），边上显示流转的数据量（如「3 条 Source」「22 条 Fact」）
- **点节点 → 右侧检查器**两栏：
  - 配置页签：该节点的参数表单（endpoint 下拉、渠道勾选、模型路由徽标——直接复用场景路由配置）
  - 结果页签：产物实体链接（Source 3-10 / Pack v3 / Draft 21-23 / Asset 4）+ 关键指标（候选数、blocker 数、耗时）
- **等待人工**：画布顶部横幅「第 4 步等你确认」，节点脉冲高亮，点开即操作
- **模板一键开**：V1 内置两条模板，不用用户从零拖：
  1. **每日舆情 → 荐题**：connector_pull(量化看板+dtk) → extract_facts → factpack_freeze → suggest_topics → 【采纳·人工】
  2. **生成 → 出库**：suggest_topics 或已有 topic → generate → fact_check → 【审核·人工】→ export(html/md/srt) → publish_wechat

## 6. 与既有机制的关系（不重复造轮子）

- **定时触发**：V1 不做工作流级 cron；数据到达型自动化继续走 Connector 的随机间隔监测（已上线）。V2 加 `trigger: schedule/data` 节点。
- **审核流**：approve 的三重校验（无 blocker + frozen + revision 未变）是既有闸门，工作流的人工节点只是「从画布触达它」，不绕过。
- **模型路由**：generate / fact_check / topic_discovery 场景路由直接生效于对应节点，画布节点配置页显示当前路由的模型徽标。
- **素材**：export 节点产物自动带 asset_media 素材位；publish_wechat 节点用上传的真图做封面（无真图回退 SVG 占位）。

## 7. 实施切片（确认后按此顺序交付）

| 切片 | 内容 | 规模 |
|---|---|---|
| **S1 引擎+模板** | 三张表 + 引擎 + 6 类自动节点 handler + 2 条内置模板 + run API + 测试 | 后端为主，~1 天 |
| **S2 画布视图** | React Flow 画布 + 运行态着色 + 检查器（配置/结果）+ 模板实例化页 | 前端为主，~1 天 |
| **S3 人工节点** | confirm_facts / adopt_topic / approve 三类暂停-续跑 + 节点内联操作 | ~半天 |
| **S4 发布节点** | publish_wechat 接入画布；抖音/小红书待 cookie 后接 | ~半天 |
| V2 | 自由拖拽编辑器、条件分支、定时/数据触发、生图节点、失败重试 UI | 后续 |

S1+S2 完成即可在画布上完整跑通「拉取 → 打包 → 荐题 → 采纳 → 生成 → 校验 → 批准 → 导出」并逐步点开看结果——即扣子式体验的最小闭环。

## 8. 风险与对策

- **React Flow 引入**：唯一新前端依赖，MIT 无授权问题；构建体积 +~100KB（gzip ~35KB），可接受。
- **长任务阻塞**：荐题/生成走真实模型需 1-3 分钟，引擎默认同步会占请求 → run 启动即返回，前端轮询 run 详情；TASK_QUEUE_ENABLED=true 时自动走 Celery（接口不变，既有双模式设计复用）。
- **重复执行幂等**：handler 全部落在幂等业务（拉取 sha256 去重、抽取 upsert、冻结不可变、revision 不覆盖），重试安全。
