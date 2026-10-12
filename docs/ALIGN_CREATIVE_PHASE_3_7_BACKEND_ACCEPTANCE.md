# Creative Orchestration：第二批后端验收

日期：2026-10-04。范围：`align-creative-orchestration-product` 阶段 3–7 的后端，不是全 change 或页面最终验收。

本批新增完成 42 项，累计 64/147，83 项未勾选。状态：BACKEND_BATCH_EXECUTED / REVIEW_PASSED；不等同整个 change 完成。

## 基线与正式环境

`main@341ead8` 加第一、第二批未提交工作。新增迁移 `aco000000001`，前置 `f8a000000001`。正式 SQLite 只读核验仍为 `f7d000000001`，没有新执行表；未执行正式迁移、未重启正式 API、未写正式素材或凭据。

新增 ORM 字段需要后续明确授权的迁移才能在正式运行库使用，本批 API 闭环仅在隔离库成立。启动 `create_all` 不创建这六个 migration-only 表，也不会替正式库添加新 intent 列。不改变现有 approved schema head 或部署配置。

F8 13 个 owned 文件 SHA256 保持不变。根 README 和根三份执行记录未被覆盖；本 change 使用自己的 README/task_plan/progress/findings。没有提交、推送、部署、canonical sync/archive 或真实 Provider/公众号调用。

## 已实现的后端

| 范围 | 实现 | 保持的边界 |
| --- | --- | --- |
| 持久化 | Package、Execution、Output、CapabilityArtifact/Revision/Use 六表，Master/Variant nullable intent/hash | Capability 服务尚未实施；模型存在不等于可使用 |
| Creative Intent | `creative.intent.v1`，服务器 canonical hash，Master/Variant 原 CAS/幂等保存，独立 history/diff | 不新增事实/身份真源；旧 null 行不回填 |
| 执行包 | `creative.execution.v1`、`director.video.v1`，exact source/context/intent/profile/assets/evidence/output contract | 过期包只能读取；创建包不执行、不批准 |
| 执行 | prepare/claim/start/report/checkpoint、unknown/reconcile、确认未 dispatch 的新记录重试 | 换 key、重复包或换执行者不能绕过同包 unknown 核对 |
| 暂存 | 私有工作目录、精确素材 materialize、MIME/hash/大小和 role/index/attempt 校验 | 不允许任意路径、符号链接、设备或超合同输出 |
| 人工接受 | exact MaterialRevision、可选原子项目引用、派生权利不升级、归因/许可继承 | 不自动改 Master/Variant/Candidate/Review/Delivery/Published |

```text
current Master / Variant + exact context / refs / intent
                      ↓
        immutable CreativeExecutionPackage
                      ↓
     prepare → claim → start → private outputs
                       │             ↓
                  unknown       immutable staging
                       ↓             ↓
                显式 observation 逐个人工接受 / 拒绝后替换
                                     ↓
                       MaterialRevision + 可选项目引用
                                     ↓
                       另行显式绑定并保存 Master / Variant
```

`result_ready` 按必需 role 的 staged distinct index `min_count` 判定；任何必需槽位最新 attempt 被拒，均要求同槽位替换。`accepted` 按必需 role 的 accepted `min_count` 判定；optional 不阻塞。终态不能提交新输出，已经 accepted 的执行不能因拒绝额外必需输出而重新打开。旧被拒输出保留，不覆盖。

## 隔离实际断言

运行真实本地 FastAPI/domain/storage，fixture 使用受控 PNG/字幕/Video v2 文档，不调用模型或专业工具。没有新增永久测试文件或测试用例；既有迁移测试仅将当前 head 断言更新为 `aco000000001`。

| 检查组 | 结果 |
| --- | --- |
| Text 包与多输出接受 | canonical 包 hash 一致；prepare 幂等；min_count 未齐不能完成；接受只创建素材/明确项目引用；Master 不变、无 Candidate；foreign owner 404 |
| Variant 包 | exact Variant/Master/profile/intent 冻结；仅意图修改产生新 Variant、Master 不变；旧包可读但不能准备执行 |
| replacement / unknown / retry | required 拒绝后 blocked；更高 attempt 保留旧行；unknown 不自动 start；人工核对；确认未 dispatch 后新 execution 链接原记录 |
| 派生权利 | 实际 materialize restricted 输入；公开权利升级 403 且无部分素材写入；受限接受保留输入归因/许可；旧包 source drift 后只读 |
| Director / 路径 / 脱敏 | 无最终 MP4 的 current Video v2 可创建 Director 包；script/shots/timeline 等原样；illegal kind 422 且无部分包；5 类路径/文件拒绝；secret 不回显；归档可读不可新建 |
| 并发与历史 | 双线程 claim 200/409、submit 201/409、accept 200/409；同字节不同输出使用不同素材 provenance；重新打开引擎可读原 hash |
| 新进程回读 | 第二个独立 Python 进程读取已 accepted execution 和两个成果，字节 SHA256 一致 |
| SPEC 修正负向 | 普通上传拒绝保留来源；unknown 换 key/同 hash 新包/换版本/换执行者全部拒绝；required surplus 拒绝仍 blocked，替换后历史不变 |
| 数据安全修正负向 | 任一输出已接受后追加输入 409、原输入可重读；prepare 和合并后的 checkpoint 缺少 observation hash 时 422；剩余总量预算在读取前生效，失败不写文件或改变 CAS |

临时 API 断言目录为 `/tmp/aics-align-core.Cthtw9`，迁移副本目录为 `/tmp/aco-stage3-HRe8tT`。目录是本次证据，不是正式数据位置或新的部署要求。

## 迁移验证

当前正式库通过只读 backup 创建独立副本，up/down/up 最终为 `aco000000001`。比较六张历史表原始列 SHA256，每一步一致；副本已有 v4/v5 各一条，没有 v3，v3 兼容由现有 regression suite 验证，不虚构现有 v3 数据。原有 97 条 foreign-key-check 异常没有增加，本批不修复或删除这些历史数据。

10 组 retained-row/intent 降级保护均在删除结构前拒绝。SQLite integrity 为 `ok`；PostgreSQL DDL 编译通过，但未连接 PostgreSQL 服务，也不是当前生产要求。

首轮全量测试与并行 migration/model 修改交叠，4 个迁移测试出现 CHECK mismatch。文件稳定后严格 CHECK 比对保持，定向迁移 5/5 和全量复跑通过；没有放宽约束来使测试通过。

## 门禁与复核

| 门禁 | 最新已执行结果 |
| --- | --- |
| 全量后端 | 三处数据安全补丁后最终复跑：1660 passed / 28 skipped / 8 warnings，85.03 秒 |
| TypeScript / Vite / FE-P1 | PASS；`/projects` 225.02 kB raw / 72.99 kB gzip |
| OpenSpec strict | 35/35 PASS |
| Ruff / diff-check | PASS |
| F8 SHA256 | 13/13 一致 |
| 独立 SPEC 复核 | APPROVE，限定已实施后端范围；只读复审，没有冒充重跑命令 |
| 独立 Python 代码复核 | APPROVE；定向 Ruff/diff-check，未冒充全量测试或数据库验证 |
| 独立数据安全代码复核 | APPROVE；三处补丁均闭合，并以独立内存诊断验证；正式库、网络和仓库文件未写入 |

首轮 SPEC review 找到普通上传来源伪造、换 key 绕过 unknown、必需输出拒绝后的数量旁路，已修正并用真实 API 负向验证。后续还补了 accepted-output 回读 provenance 和终态不能重新打开的保护。独立复核不冒充重新执行上述命令。

数据安全复核追加的输入权利边界漂移、metadata 合并后的假 verified checkpoint、素材总量检查晚于读取均已修正：接受任一输出后冻结实际输入集合；对最终合并 checkpoint 校验证据；按剩余总量限制每次读取。真实 API/存储负向和独立定向复核均通过。最后全量后端结果是在这些补丁之后执行，不沿用补丁前结果。

全量命令在 `apps/api` 执行，使用已初始化的隔离库：

```bash
APP_ENV=test DATABASE_URL=sqlite:////tmp/aco-stage3-HRe8tT/full-suite.db AI_STUDIO_MEDIA_ROOT=/tmp/aics-align-core.Cthtw9/final-media .venv/bin/python -m pytest -q
```

本批实际使用：using-superpowers、openspec-apply-change、writing-plans、executing-plans、subagent-driven-development、test-driven-development、systematic-debugging、requesting-code-review、receiving-code-review、verification-before-completion。依用户限制，不新增永久测试代码；红/绿验证采用临时内联断言和既有 suite。

## 后续未完成范围

Intent 编辑 UI、Package 预览、逐输出 review/rights UI、绑定接受结果的浏览器闭环、显式 discard/cleanup、本机 MCP、Capability Memory 服务/页面、Director-first Video 产品界面、完整 Legacy retirement、全 change 最终验收均未在本批完成。

不将 API 测试冒充浏览器验收，不将受控执行文件冒充 Premiere/AE/Resolve/Photoshop 自动化或真实生成质量。正式 SQLite 迁移、canonical sync/archive、本地提交和远端动作继续保持未执行。
