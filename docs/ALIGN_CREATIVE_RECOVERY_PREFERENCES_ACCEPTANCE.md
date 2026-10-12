# Creative Execution：本地客户端、恢复、偏好候选与配套备份

## 范围与状态

第六批沿用已批准的 `align-creative-orchestration-product`，基线为本地 `main@341ead8` 加本 change 未提交实施。任务 8.11、9.1、9.7、9.8、11.5、14.2–14.4、14.10 已按下述证据完成；新增 9 项，累计 **131/147，剩余 16 项**。本批 EXECUTED / REVIEW_PASSED，不据此关闭整个 change。

SQLite＋本地素材库＋loopback API/Web 仍是正式使用方案。所有本批验证使用临时副本；不升级正式数据库，不改素材路径、凭据或既有 Worker，不发送模型生成、公众号或专业工具请求。

## 已安装 Codex 的真实 MCP 连接

- 客户端为实际安装的 `/opt/homebrew/bin/codex`，版本 `0.160.0`，使用其 `app-server --stdio` 和本机生成的协议 schema。
- MCP 仅通过该隔离子进程的 `-c` 参数连接 `http://127.0.0.1:15431/api/v1/creative-mcp`。测试 token 仅进入子进程环境；没有修改用户全局配置。
- 实际 initialize、initialized、`mcpServerStatus/list` 成功；识别服务 `aics-creative` v1.0、15 个白名单工具、1 个资源和 4 个资源模板。
- 实际 `mcpServer/resource/read` 读取 owned Project 1 / Unit 4 context 成功。不是自行实现的 Test Agent 冒充 Codex 客户端。
- 0 model turns，0 execution/domain writes，未调用审批、发布、SQL、正文保存或任意文件系统工具。没有为验证连接创建用户聊天。
- CLI 的 `runtimeStatus` 返回 null；不据此声称运行状态投影已提供。服务端握手、工具目录和资源读取成功是本任务的实际连接证据。
- 临时脚本：`/tmp/aics-recovery.O4LrqA/codex-client.cjs`；schema 位于同目录 `protocol/`，仅为验收输出。

## SQLite 与素材配套恢复

复用已有 `apps/api/scripts/rehearse_sqlite_recovery.py` 和 `rehearse_storage_cutover.py`。SQLite backup 本来覆盖所有表，无需为六张新增表发明第二个备份器。

来源为已停止的第五批隔离环境 `/tmp/aics-director.pFKi2i`；恢复目标为新建 `/tmp/aics-recovery.O4LrqA`。未恢复至用户正式目录。

| 验证 | 实际结果 |
|---|---|
| 源 / 恢复 SQLite integrity | 两者 `ok`；各 1560576 bytes |
| 恢复 Alembic head | `aco000000001`，与源一致 |
| 六张新增表逐行完整比较 | Package 6、Execution 14、Output 14、Artifact 20、ArtifactRevision 36、Use 5，全部 tuple 精确一致 |
| 素材引用与复制 | 15/15 引用 hash 验证，7/7 精确文件复制，0 failure |
| 已接受输出恢复 | 13 个 accepted output 对应的 MaterialRevision 文件及 SHA256 全部一致 |
| 暂存 / executor work directory | 不复制；不是 accepted 历史恢复依赖 |
| 历史 Video Candidate local ZIP | 从恢复后的真实隔离 API 重新导出，与原 ZIP 完全相同 |

完整 ZIP SHA256 为 `9889528e53c4f99d3667ab43de0c3e8d5726593026932833db345c18e4df4605`。临时核验脚本和重新导出的包为 `verify-restored.py` / `restored-director.zip`。

以上比较发生于本批浏览器新增临时 Master/Package/Execution/Capability 记录之前；不能把之后的测试写入误判为恢复差异。独立恢复复核进一步核对全部 90 张表的逐行数据、schema/约束、FK/integrity，结论 APPROVE。

## Executor 声明与真实受控文件恢复

- kind/key/version 与 supports_checkpoint/revert/recover、1–4 个唯一 output kinds 复用原 checkpoint metadata，不新增 Registry/表。新完整声明严格验证三个 bool、全部输出角色和声明不可变；旧 partial metadata 可读及幂等重放。
- 页面明确显示 declared / undeclared 和 `runtime_verified=false`；默认未声明。实际视频页面建立 Director Package 并 prepare，刷新后声明精确回读，执行仍为 prepared / not_dispatched，未调用专业工具或生成模型。
- 受控 executor 实际完成 checkpoint→临时项目文件损坏→failure/unknown→读取损坏 hash→明确 revert/recover→新结果；两条路径各只有一次 dispatch。服务端不访问任意外部项目路径，恢复证据仍需 exact executor、CAS、原 checkpoint binding 和匹配 observation/readback。
- 新 Python 进程读取两条 `result_ready`、恢复动作、文件与 staged output hash 均一致。未解决 Unknown 禁止继续/换 key 重发，恢复不能伪造 failed-before-dispatch。
- 父层修正后重跑 `/tmp/aics-executor-recovery.QWPAqm/test_descriptor.py`：**28 passed / 1 existing warning，7.53 秒**，使用全新 `/tmp/aics-batch6-final.msvOUr/descriptor`。同目录 revert/recover evidence 指向该次新 fixture；两个 `--readback` 新进程再次通过。
- 浏览器 `/tmp/aics-recovery.O4LrqA/descriptor-browser.cjs` 通过，0 page error；完整声明保存/刷新通过，无其他 Master/native/LLM/Candidate/Review/Delivery/Output 写入。

## 已保存人工编辑 → 偏好候选

- 使用同一 owned Project/Unit 至少两次已保存、实际改变正文的人工 Master 编辑。服务端逐项重验 ID/revision/payload/context、精确 parent/hash、actor、schema/modality、冻结 context ownership 与已存 AI receipt。
- 首稿、升级、seed、未保存草稿、只有 intent/context/attestation/render binding 的变化、伪造 hash/parent/AI 来源、外来/归档/viewer 都不能充当重复接受编辑。
- 人工选择精确编辑并填写偏好，结果仅是 project-scoped `preference candidate`；不存来源正文、不自动 saved/pinned、不应用偏好。去重只返回 candidate，已有 saved/pinned 不被新捕获悄悄复用。
- 实际浏览器验证未保存标题不出现在来源清单；明确保存后可选择；篡改提交 hash 触发真实 409 并保留名称/选择；重新读取后明确 capture；另行人工晋升 saved，刷新读取精确 provenance。
- 父层修正后重跑 `/tmp/aics-preference.N7xJtt/fixture.py`：正向 capture/dedupe/单独晋升及 **33 类负向全部通过**，其他业务记录不变。页面脚本 `preference-browser.cjs` 通过，0 page error。

## Secrets、安全错误与只读零 dispatch

独立安全复核先发现 execution metadata/recovery 与 MCP RPC ID 对 Google/Stripe/编码赋值及签名 URL 扫描不完整。父层临时复现，再仅补 shared secret scanner：NFKC/最多三层 percent decoding 只用于扫描，不改持久正文或 canonical hash；整体拒绝，不静默清洗。长度先于扫描；MCP 在 response ID 赋值和任何业务 dispatch 前拒绝。

- `/tmp/aics-secret-review.M6k7Wd/check_secrets.py`：RED 57/57 被接受 → GREEN **57/57 拒绝**，普通摘要及安全 RPC ID 保持可用。
- `check_transport.cjs`：真实隔离 HTTP 对 10 个敏感 ID/metadata 请求提前拒绝，response ID 为 null、不回显秘密；**90 表逐行不变**，普通 ping 成功。
- 独立安全复核修正后 APPROVE：原 3 类 progress、3 类 recovery、5 类 credential RPC ID 均拒绝，checkpoint/revision/event/audit 不写入，正常 URL 仍保留合法 ID 回显。
- 父层新鲜重跑 `/bin/sh /tmp/aics-batch6-security.5RPoJl/rerun.sh source`：23/23；`rerun.sh full`：**325/325 临时检查通过**，新 fixture `/tmp/aics-batch6-security.5gixKT`。含 29 个只读 surfaces、89 个 ORM 业务表、descriptor/recovery/preference、create/import/use/export、审计/日志/异常安全；0 network/process/provider/native/external/professional effect，源文件运行期间不变。
- 五个日常页面只读打开再次通过：Home/Production/Assets/Settings/Video，11 类业务表不变、0 写请求、0 page error；10 个既有外部字体请求被阻断，不扩大本批为字体重构。

## 最终门禁与复核

| 门禁 | 修正后实际结果 |
|---|---|
| 全量后端 | `APP_ENV=test .venv/bin/python -m pytest -q`：1660 passed / 28 skipped / 8 existing warnings，89.89 秒 |
| 前端 | TypeScript/Vite PASS，2366 modules；FE-P1 PASS |
| Bundle raw/gzip | Projects 225.03/72.99 kB；common Production 279.62/89.36；Execution lazy 267.66/86.37；Capability lazy 267.60/85.69 |
| Heavy dependencies | Text TipTap lazy 606.37/189.58 kB；Graphic/Video/common Production 无 TipTap/XYFlow |
| OpenSpec | `openspec validate --all --strict` 35/35 PASS |
| Ruff / whitespace | Ruff PASS；tracked diff 与 54 个 owned untracked 文件 PASS |
| F8 ownership | 13 文件 SHA256 byte-for-byte 不变 |
| 正式库只读核验 | head 仍 `f7d000000001`，未 migration/写库 |
| 独立复核 | 计划/SPEC、恢复/偏好实施、TypeScript/产品、安全、配套恢复均 APPROVE；不是整个 change 的最终复核 |

修正后实际 Codex app-server 握手、15 工具和 owned context 资源读取再次通过。只停止本批隔离 API/Web 15431/15432，保留临时证据；正式 API/Web/Worker 不动。

本轮写集为既有 Creative Execution service/contracts/router/MCP input 与页面，Capability Memory service/router/types/页面，以及上述 shared secret scanner 和 change-local 文档。无新增 durable 对象/迁移/依赖/永久测试。剩余：7 项 Legacy 操作承接/兼容导航与浏览器、7 项完整终验/复核/交付记录、2 项贯穿结束的安全停止条件。

## 明确限制

Executor 的 `supports_checkpoint/revert/recover` 是操作者声明，不是自动能力验证。本批受控文件恢复不证明真实 Premiere、After Effects、Resolve 或 Photoshop 自动化；专业 pilot 在首批验收范围之外，未执行。连接 Codex MCP 不代表已付费调用模型或完成专业内容创作，更不证明生成质量优于现有工具。

Capability Memory 保存方法，不自动应用偏好、执行代码或改写 Identity、Fact Boundary、Master、Variant、Candidate、Approval、Delivery 或 PublishedContent。正式 SQLite migration、最终全 change 验收、canonical sync/archive、本地提交及远端 push/deploy 均不属于本批动作。

本轮实际使用技能：using-superpowers、openspec-apply-change、writing-plans、executing-plans、dispatching-parallel-agents、subagent-driven-development、requesting/receiving-code-review、systematic-debugging、test-driven-development（仅临时断言）、verification-before-completion。brainstorming 仅复用已批准方向；using-git-worktrees 按用户明确要求保留 main，不创建 worktree。
