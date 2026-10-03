# F7 整阶段本地门禁与复核（2026-10-01）

## 2026-10-03：独立F7提交树最终门禁

生命周期结果：F7实施已本地main提交`3f28a51d0145c49ae558766aeebbdbed68a8fcc1`；主清单110/110（Commons用户暂缓行政关闭、非真实PASS），模型路由23/23。两个change已归档，八份delta合并七份canonical；原有54要求/146场景逐块精确保留，新增块全部吻合，范围前言保留，Purpose TBD清理，归档后strict34/34及diff通过。F8/原始资料留在工作区，未push/deploy/运行正式迁移。

本轮仅执行已授权F7生命周期收尾。共有81个文件进入私有拟提交索引；共享文件按片段隔离，F8认证/User身份、生产启动/schema检查、MinIO重接及f8a迁移均不纳入。既有f7d迁移和仅本地私有字节依赖保留，未创建新迁移或永久测试。实际源码与正式库不被临时投影覆盖。

最终限定独立归档复核APPROVE：8份delta/7canonical、95要求/261场景、原54要求/146场景逐块保留，两个归档完整、local-ASR不变、Commons延期及MiniMax视频排除如实。29文件归档索引仅含docs/spec/archive，无apps/F8。该复核只读，不冒称重跑后端、浏览器或PostgreSQL。

| 本轮实际门禁 | 结果 |
|---|---|
| F7-only全量后端 | 1660 passed / 28 skipped / 8既有warnings，87.75秒，exit0 |
| TypeScript/Vite、FE-P1、模型路由状态脚本 | PASS |
| `/projects` initial JS | 224.89 kB raw / 72.97 kB gzip |
| `/assets`、`/settings` initial JS | 258.86/82.83、236.26/77.16 kB raw/gzip |
| Common Production、Text Studio lazy closure | 284.42/90.47、611.17/190.68 kB raw/gzip；Graphic/Video排除TipTap |
| 全app Ruff、拟提交diff空白 | PASS |
| OpenSpec归档前strict | 34/34 PASS |
| 独立只读复核 | 生命周期/八份delta保留计划APPROVE；八个共享文件静态提交边界APPROVE |

第一轮临时空checkout全量为1659 passed、1 failed：旧worker测试自建Session而未使用API内存fixture，默认临时库缺content_job表。只初始化指定私有worker测试库后，原四项队列测试通过；上述最终全量使用同一私有库重新执行通过，没有改业务代码、测试源码或正式库。SQLite既有迁移往返包含在全量结果；原生PostgreSQL和浏览器采用下方已记录的验收证据，本轮不冒称重跑。

Commons按用户决定deferred/未实测行政关单，非真实PASS；MiniMax真实视频/H3为用户排除，CPA未证明媒体能力及未证明素材权利保持不可执行/false。公众号沿用已经确认的当前实现单次草稿及真实Receipt/CapabilityVerification，本轮无任何新增微信/供应商调用、正式库写入或部署。

## 2026-10-03：模型路由最后五项末轮门禁

范围为 `add-model-capability-routing` 的 2.1/2.5/2.6/2.7/2.9，基线为 `main@8c0e3b8` 加既有工作区。已记录的 CPA 三模型聊天、MiniMax 图像/TTS/ASR、本机 MLX 与页面验收继续有效；本批新增真实供应商调用和正式数据库写入均为 0。MiniMax 视频/H3 是用户排除范围，CPA 未证明的媒体操作仍不可执行，未证实的公开/模型/商业权利继续为 false。

当前五项全部完成，模型路由23/23、ARCHIVE_READY；canonical同步/归档未执行，整个F7/F8状态不由本change计数替代。

| 最后补丁后的实际门禁 | 结果 |
|---|---|
| 全量后端 `PYTHONPATH=. .venv/bin/pytest -q --tb=short` | 1660 passed / 28 skipped / 8 warnings，101.93 秒；95.39秒为别名碰撞补丁前的中间门禁，跳过项不计通过 |
| 模型路由、媒体、ASR、能力持久化、Workflow、Project Workflow 六份既有回归 | 177 passed / 4 warnings，5.98 秒；此前164项为中间门禁 |
| 九个相关 service/router 的 Ruff | PASS |
| Web TypeScript/Vite、FE-P1、`test-model-routing-state.mjs` | PASS |
| `/projects` / `/assets` / `/settings` initial JS | 224.89/72.97、258.86/82.83、236.53/77.28 kB raw/gzip |
| 公共 Production / Text Studio lazy closure | 284.42/90.47、611.17/190.69 kB raw/gzip；Graphic/Video 无 TipTap |
| `openspec validate --all --strict` 与 `git diff --check` | 34/34 与 PASS；最终文档关单后同样核对 |
| 独立 Provider/安全与 UI/Workflow 复核 | APPROVE；消费者别名碰撞发现后再定向复审APPROVE，无剩余本批阻断 |

中断后旧测试会话不可读取，所以上表来自重新执行的命令。最后源码补丁后的全量日志为`/private/tmp/aics-routing-final-backend.4x4sKH`；Web日志为`/private/tmp/aics-routing-final-web.yUqFGH`，177定向与Ruff有实际命令输出。`/private/tmp/aics-routing-final-backend.5GLwhm`和`/private/tmp/aics-routing-final-targeted.UkVEGy`为95.39秒/164项中间门禁；不包含供应商凭据，不作为正式素材。此前同数全量结果保留为历史，不冒称末轮stdout。

### 复核缺口与实际修复

只修改五个既有源码文件，并给原设计/规格补对应场景：

- `ProviderMediaPanel.tsx`：打开新任务立即清除旧媒体、确认与权利；read ID、actor 和 mounted 检查拒绝晚响应，接受时核对同一 task/result hash 和 result_ready。执行真实函数的临时 UI 探针覆盖 raw/API 失败、晚响应、actor 变化以及错 ID/hash/state 的零 POST。
- `workflow_engine.py`：普通执行和人工接受后的 resume 共用输出映射；pending 只延迟确实尚未生成的素材字段，未知映射继续拒绝。隔离真实服务走通一次合成发送→等待→明确接受→项目精确素材→输出别名→下游；started Attempt 不变、重复 resume 不增加发送或 terminal Attempt、foreign/archive/rerun/skip 均拒绝，Fact Boundary 未改变。
- `project_workflows.py`与`workflow_engine.py`共用八字段映射校验，保存定义/执行/resume均拒绝别名覆盖服务端state/task/Attempt/精确素材身份；同字段和正常别名保持兼容。实际RED复现generation_state被素材ID17覆盖；主agent真实函数GREEN与独立56个跨字段碰撞探针通过，冲突在供应商/恢复调用前拦截、0调用，accepted正常完成且重复finish无额外终态。
- `minimax_cli_provider.py`：ASR 执行指纹包含 CLI runtime、asr-1.0 与 credential epoch；静态库存仍不读取认证文件。真实私有 API 使用内存 credential 边界验证旧建议在 epoch 变化后保存 409、缺失后 422，均无 Master 写入；原 epoch 保存 200 并保留 verified_output_match。没有更改用户真实登录。
- `provider_media.py`：WAV 必须包含实际音频帧，0 帧拒绝、1 帧/正常音频通过。私有真实任务拒绝空音频后保留原 submitting claim、没有结果存储/MaterialRevision，重复 execute 拒绝；过期 claim 仍走既有 Unknown 处理，不自动重新提交。

上述临时探针经标准输入运行，不新增永久测试代码。2.8 的实际隔离浏览器证据见[模型验收](FE_F7_MODEL_VALIDATION.md)，这次五处补丁的函数/API 探针不冒称重新运行浏览器或真实供应商。

独立审查边界：Provider reviewer核对当前合同/相关服务，并执行源码提取的内存epoch/音频探针；消费者reviewer审查Panel/Workflow两处补丁，发现别名覆盖后复验全部56个跨字段负向及正常/延迟/identity/legacy正向，最终APPROVE。两者不写源码、认证、正式库，不调用供应商，不冒称重跑全量、浏览器或native PG。最后全量/177定向/构建由主agent实际执行。本轮使用using-superpowers、OpenSpec apply、writing-plans/executing-plans、并行与请求/接收复核、systematic-debugging、临时RED/GREEN验证及verification-before-completion。

## 2026-10-03：生成任务可靠性完整本地验收

本批只验收 `add-model-capability-routing` 3.2/3.4。初验沿用现有实现，在新私有 SQLite、合成 Provider 和受控临时存储中执行；后续按定向复核最小修改两个service及原规格，未增加测试文件、依赖或迁移，真实供应商调用和正式数据库写入均为 0。临时运行代码经标准输入执行，不进入仓库，临时库在验收后清理。

| 实际场景 | 结果与边界 |
|---|---|
| 同键重复准备、不同输入冲突、并行准备 | 同输入只有一个 task；不同输入 409；两线程并行准备返回同一 task |
| 两线程并发发送 | 合成 Provider 只接到一次提交；另一个调用 409；真实 CAS/事务未被替换 |
| 两线程并发接受 | 只产生一个 MaterialRevision 和一个 ProjectMaterialReference；输家 409；新 Session 重放返回同一版本 |
| 两个独立进程先后接受 | 两次返回同一 MaterialRevision；素材版本总数仍为 1 |
| 未来/过期 revision、有效 lease、晚 worker | 无发送的 409；错误 lease token 不能覆盖结果；有效 lease 阻止恢复 |
| 三个真实子进程中断窗口 | claim 后发送前、合成发送返回后结果提交前、私有字节落盘后 DB 提交前，子进程均 exit 73；任务保留 submitting/rev2，过期后 unknown/rev3，不能重发。第三窗口的一个私有孤儿文件未被误接受 |
| 成功提交后重启 | 新 Python 进程验证原 result_ready/rev3、HMAC 与实际 WAV 字节 |
| 原 job 恢复及查询边界 | 查询严格使用原 job/model/protocol；0 新提交；最短间隔 429、120 次上限 409；过期 job 保留原 ID 并为 unknown |
| receipt key 与回执 | 缺 key、撤销旧 key、错误 key、伪造签名、篡改 job/result receipt 均拒绝；保留旧 key 的轮换可在新进程验证原回执 |
| 凭据连续性 | 合成 credential epoch 变化/不可证明分别阻塞；固定 MiniMax credential 投影函数对 API key 和 OAuth access/refresh/account 的夹具变化生成不同 HMAC，不读取或轮换真实凭据 |
| 来源/字节/权限 | foreign owner 404；私有结果字节篡改、来源 model-use 撤销和项目归档均阻止接受；归档后安全历史仍可读 |
| 原子回滚 | 在真实 Material/Revision/Reference/Event/Audit 写入后、提交前注入失败：五类记录数不变，task 保持 result_ready 和原 revision，无 accepted FK |

共 38 个执行场景通过：26 个服务/并发/安全场景、4 个进程崩溃/重启场景、8 个独立准备与跨进程信任场景。Provider 和路由库存为合成边界；任务 CAS、receipt、私有落盘、素材/项目引用及提交回滚使用当前真实服务。不得称为真实 MiniMax 视频恢复，当前账号视频生成/H3 下载仍为用户排除范围；这些场景也不证明全部供应商协议或 F7 最终验收。

| 本批新鲜门禁 | 结果 |
|---|---|
| 既有模型路由/能力持久化/媒体接受/ASR 回归 | 144 passed / 1 warning |
| 最后一处Unknown修复后全量后端 | 1660 passed / 28 skipped / 8 warnings，89.66 秒；初验83.09秒和中间78.59秒只保留为历史 |
| TypeScript/Vite、FE-P1、模型路由状态脚本 | PASS；Projects 224.89/72.96 kB，公共 Production 284.42/90.46 kB raw/gzip；Text TipTap 仍 lazy |
| OpenSpec all strict | 34/34 PASS |
| 相关六个 service/router Ruff、git diff --check | PASS |

### 定向复核发现与修复

最初 38 个场景没有覆盖 MiniMax 实际 credential 派生及 terminal job 身份差异。恢复后的 reviewer 静态核对发现问题，未把初验当作完整 APPROVE；本批逐个失败复现后只修改 `generation_tasks.py` 和 `minimax_cli_provider.py`：

- 历史 credential epoch 使用 task 原 key-ID；新活动 key 不误伤保留旧 key 的任务，实际凭据变化仍拒绝。
- 所有返回的 job/file 验证类型及已有身份；已知 job 的成功/确认终态必须回传 exact job，成功字节还必须匹配 known file。MiniMax 的确认失败/取消保留原 job metadata。
- 已知 job 查询的 adapter unavailable 只证明查询不可用，不是远端确认失败；保持 unknown、原 job 和原 receipt，不授权替代发送。
- 来源排序经实际 Session 的 after-commit 故障插入核对：撤权先提交则 0 发送；claim 先提交则原授权发送一次、结果保留，但接受 409。reviewer 确认符合无网络 DB 锁的既有契约；design/spec 写清 claim commit 授权线性化点，不新增权利体系。

修复后的新鲜隔离验证包括 10 个 key/terminal-job 场景、19 组幂等/并发/原 job/回滚回归、4 个 Unknown/确认终态场景；全部通过，0 真实供应商调用。最终独立源码定向复审APPROVE（仅3.2/3.4，复核员未运行测试），最后补丁后全量后端结果见上表。

3.2/3.4已完成，本change17/23，仍未完成2.1/2.5/2.6/2.7/2.8/2.9。F7最终provider/UI审查、完整浏览器和规格归档仍是独立任务；本批定向复核不能替代它们。没有提交、推送、公开发布或正式库写入。

## 2026-10-02 公众号统一验收后的新鲜门禁

本轮沿用现有实现，仅统一记录与勾选F7 8.5，不修改业务代码/测试/配置/迁移，不新增供应商动作或commit/archive。公众号一般范围尚未完成，不称本文件为F7全阶段验收PASS。

| 本轮命令 / 检查 | 结果 |
|---|---|
| 四份既有公众号测试 | 129 passed / 1既有warning，13.15秒 |
| `PYTHONPATH=. .venv/bin/pytest -q --tb=short` | 1660 passed / 28 skipped / 8既有warnings，74.25秒 |
| Web `npm run build`（含bundle gate） | PASS；projects224.89/72.96kB raw/gzip；Production284.42/90.46；Textlazy611.17/190.68 |
| `DO_NOT_TRACK=1 openspec validate --all --strict` | 33/33 PASS |
| 公众号及MiniMax/task service范围Ruff | PASS |
| `git diff --check` | PASS |
| 原公众号私有证据只读比对 | Attempt6 succeeded、五条旧Attempt全字段不变、Receipt/Published/Verification0 |
| 原MiniMax结果只读核对 | TTS字节/hash/WAV解码一致；image Unknown无job；未验签/接受/重发 |

原生PostgreSQL及浏览器没有本轮重跑，既有PG和用户后台截图保留其历史证明范围。独立逐任务复核APPROVE仅适用于8.5和2.8a，不替代一般账号验证或整阶段2.9终审；原文件名透传差异已记入验收TODO。当前复合131/152，21项未完成。

以下为此前增量与历史门禁，旧数字不是本轮复跑结果。

## 2026-10-02 本轮证据校准与修复（当前记录）

下方同日旧增量是历史快照，不代表当前实现或完整阶段验收。此前 routing 3.5 和 registration 2.2 的复合证据不足，已先恢复为待验收；F8 MEDIA_ROOT 审计补齐 13 个调用点、10 个文件的读写/兼容性清单。

- 修复一：accepted 重放不能跳过 live runtime/source 与私有结果验签/字节校验；同时验证精确已接受 MaterialRevision、父 Material active 和库中实际字节。隔离真实 SQLite/签名/PNG 证明重复返回同一 ID、不追加 revision；父素材归档、凭据 epoch 改变、pending/library 字节或结果签名篡改均拒绝。Provider/runtime 是合成 fixture，不是供应商验收。
- 修复二：f7d 已有表保护核对列类型、PK、CHECK 实际表达式、owner/key UNIQUE 列、索引列和唯一性，而非仅约束名字。SQLite 同名 CHECK/UNIQUE、错误类型/PK/索引负向探针全部拒绝。原生 PostgreSQL 16 本轮临时实例实际执行精确 f7d up/up/down/up、12 类非法记录/FK/重复键与 retained downgrade 拒绝；修复后再次 up/down/up 并分别篡改五条 CHECK 和 UNIQUE，全部 fail closed。追加复核指出的 literal 空格、CHECK NOT VALID、partial index 旁路也已修复；最后一个独立 PG 实例实际反射 `not_valid=True` 并拒绝，正常迁移往返通过。临时实例无用户库挂载且全部已删除；不是完整生产数据库迁移或所有历史 migration 的 PG 验收。
- 合成持久任务探针另外覆盖原 job/model/protocol 查询不重发、fresh Session 幂等接受、owner 隔离、credential/key 变化、签名/字节篡改、source 撤权、归档拒绝和接受故障回滚。并行接受、全部崩溃窗口、真实供应商 job 恢复仍未据此关闭 routing 3.4。
- 模型登记浏览器：独立临时 SQLite + `18117/17173`，只登记 `.example` 地址和无效测试字符串密钥，未请求供应商；手动模型保存、默认/文字编辑选择刷新回读、空密钥保留与安全空字段、双窗口旧 revision 冲突及输家草稿保留通过。获胜方 revision 3、输家仍 revision 2 与本地名称；后端记录 409。随后保存到 revision 5，实际 `effective_llm_config` 读取 generate→model-one、text_master_edit→model-two，合成密钥未被空字段覆盖。CPA 的既有 `/models` 401 继续未验证，不用 fixture 冒充 CPA 鉴权成功。截图位于 `/tmp/aics-registration-BL1D9v/conflict-acceptance.jpg` 与 `registration-acceptance.jpg`，临时路径不是长期发布资产。
- 所有补丁后 fresh full backend：`1661 passed / 28 skipped / 8 warnings`（86.96 秒）；现有迁移 `5 passed`；范围 Ruff、OpenSpec all strict `33/33`、diff-check PASS。OpenSpec 首次遥测关闭变量拼写不适用，出现遥测网络错误，但规格验证本身通过；最终使用 `OPENSPEC_TELEMETRY=0` 复核，无遥测报错。
- 本轮前端未改；实际 TypeScript/Vite/FE-P1 build PASS：projects `224.89/72.96 kB` raw/gzip，公共 Production `284.42/90.46`，Text TipTap lazy closure `611.17/190.68`；home/opportunities/learning/assets/settings 既有预算保持。
- 本轮限定安全/证据计划与模型登记 service/UI 独立复核：APPROVE。复核员独立验证 SQLite/源码/metadata/组件，原生PG和实际浏览器由主agent运行；不声称复核员重跑了外部服务/浏览器。routing3.5重新关闭，routing14/25；registration2.2重新关闭，登记4/4；F7合计97+14+17=`128/150`，22项未完成。无新增持久测试代码、供应商调用、正式素材接受、公众号重发/公开发布、生产迁移、提交/推送/归档或 F8 激活。

## 2026-10-02 Workflow durable generation increment

- `media.generate@1` now creates a real `WorkflowStepAttempt(status=started)` before the durable provider task is dispatched. The task stores that Attempt FK; `result_ready` remains waiting for an explicit human acceptance, and acceptance appends the terminal Attempt before the existing project-output association/downstream advance.
- The Production Inspector exposes capability/profile/limit configuration and the original-task refresh/recovery/acceptance path. Generic rerun/rerun-from-here/skip controls are hidden for this side-effect node; legacy cover and other node behavior remain unchanged.
- Fresh verification: synthetic isolated WAV workflow probe passed start/wait/accept/resume/downstream/idempotent resume/foreign actor/archive and rerun rejection. This is fixture-only, with no provider call, production material acceptance, public publishing, or new test file.
- Fresh gates: backend `1661 passed / 28 skipped / 8 warnings`; frontend build/bundle PASS; scoped Ruff PASS; OpenSpec strict `33/33`; `git diff --check` PASS. Production initial bundle measured `284.42 kB raw / 90.46 kB gzip`; Text Studio remains in a lazy closure.

## 2026-10-02 concurrent send / process-crash evidence

- Private copy, two concurrent real execute calls: exactly one local-stub submission, loser409, durable unknown/rev3, subsequent send rejected. Original real TTS remains result_ready/rev3 and unaccepted.
- Actual child-process exit73 after claim/before send and after local-stub send/before job persistence retains submitting/rev2. Live lease blocks recovery; explicitly test-expired lease transitions to unknown without resubmission. This is fixture evidence, not real provider crash/recovery or concurrent acceptance proof.
- Workflow linkage remains absent in current code; design5.3 is a pending clarification, not implementation acceptance. No new test file, production/provider operation, media acceptance or F8 activation. F7 remains125/150.

## 2026-10-02 existing-table FK guard increment

- Reproduced a pre-existing task table missing all four FKs being accepted. Added exact constrained-column/target-table/target-column matching to f7d, without a new migration version.
- Isolated normal repeated upgrade/down/up PASS; missing/wrong-target FKs rejected. Existing migration tests 5 passed/5 warnings; scoped Ruff, all strict33/33 and diff-check PASS. No fresh full backend/frontend or native PostgreSQL claim. Type/check-expression/FK-option equivalence remains unaudited.
- No paid request, media acceptance, production migration, commit/push/archive or F8 activation; F7 remains125/150.

## 2026-10-02 durable-task evidence increment (not final acceptance)

- Exact f7d migration on a fresh private SQLite: up/up/down/up; four FKs; nine negative constraints rejected; downgrade with retained fixture refused and row preserved. No F8 or production migration. PostgreSQL DDL compiled only, NOT native PG acceptance.
- A fresh process verifies the original real TTS WAV (126738 bytes, original SHA256); foreign ownership404, missing receipt key409, altered result/credential receipt409, Unknown resubmission409 without provider call. Original task revisions remain3 and accepted links null.
- A private database copy verifies stale/future revision rejection, a two-session interleaved CAS loser, stale worker token, and no-job recovery without provider submission. This is NOT concurrent multi-process send/accept competition or crash injection; those remain pending.
- All strict33/33 and diff-check pass this turn. No business-code/frontend/new-test-file changes; no fresh full backend/build claimed. Full F7 remains125/150; permissions/acceptance, original-video recovery, Workflow, native PG and independent final review unresolved. Evidence fixtures do not count as paid provider verification or F8 acceptance.

## 2026-10-02 MiniMax续批门禁（不是阶段最终验收）

- 新实现：MiniMax image/TTS固定durable submit入口、图片预算内尺寸/base64。真实隔离TTS任务result_ready并新进程验签回读；图片25秒截止unknown不重发。
- 现有定向93 passed/1 warning；全量正确命令`PYTHONPATH=. .venv/bin/pytest -q --tb=short`为1661 passed/28 skipped/8 warnings（85.17秒）。首次漏PYTHONPATH产生23个scripts导入失败，已用正确命令复跑全部通过，未通过改业务代码绕过。
- 最终另有两行items类型收紧，拒绝bool；其零网络输入探针、最终定向回归/Ruff/diff另验证，不以启动更早的全量冒充这两行完整覆盖。OpenSpec全量strict33/33通过。
- 未改前端，本轮不复用旧build/浏览器作为新结果；没有新增测试文件或独立审计，没有生产迁移/配置启用/提交/推送/归档。完整F7仍未验收，Google/Grok/Commons暂缓不算成功。

## 最新本地门禁收尾（替代下文旧状态）

2026-10-01修正12项基线lint发现后，fresh后端1629 passed/28 skipped/9 warnings（86.29秒）、TS/Vite/FE-P1、全应用Ruff、OpenSpec strict31/31和diff通过。16项选中原生PG回归通过；空库全链upgrade→f7c000000001、F7 down→f6e000000001→up通过。六份修改前后规范化AST相同，六处ValueError保留安全422/节点失败、条件异常保留持久化失败Attempt，独立只读APPROVE；没有新业务行为或全局lint豁免。

仅本轮临时容器`aics-f7-lint-gates-20261001`绑定127.0.0.1:15439，无宿主挂载；stop/rm-v后exact-name空、原匿名卷不存在，确认测试数据回收。未动默认/生产库。后端9 warnings含8既有及runner的anyio提前导入rewrite提醒；跳过的真实/PG项不冒充全部平台通过。

F7 **10.7完成，97/105**，真实平台10.2/10.3/10.5/10.6、commit/archive仍未完成；公众号补充17/20、F8未apply。真实账号已成功取得token，但封面asset_0未知，未进入create/read；本批没有读凭据/再次发微信请求。下文零请求、Ruff未通过和96/105均是此前门禁历史记录，不代表最新状态。当前真实Attempt证据见[短稿验收](FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。

## 范围

基线为 `main@da73bbb` 加既有未提交 F7/官方公众号补充改动。用户目标仍为按计划完成 F8 和全产品闭环；本文件不宣布 F7/F8 完成。用户已批准醒目标注“系统联调测试，请勿发布”的短稿和测试封面；只允许草稿箱，不公开发布。当前真实账号请求仍为零。

## 新鲜执行证据

| 门禁 | 实际结果 / 边界 |
|---|---|
| 修正前全后端 | 1621 passed / 28 skipped / 8 existing warnings，71.86 秒；临时 SQLite，与默认开发库隔离 |
| 修正后最终全后端 | 1625 passed / 28 skipped / 8 existing warnings，88.23 秒；同样只在独立临时 SQLite，包含新增四个回归及迁移回归 |
| TypeScript / Vite / FE-P1 | PASS；`/projects` 224.89 kB raw / 72.96 kB gzip；Text TipTap 仍在独立 lazy chunk |
| 原生 PostgreSQL 回归 | 17 passed / 25 deselected / 1 warning；仅 localhost:15439/aics_account_test，测试 transport 不访问微信 |
| 原生 PostgreSQL 迁移 | 全链 upgrade → f7c000000001；F7 downgrade → f6e000000001 → upgrade head，PASS；未操作默认/生产库 |
| OpenSpec 全部 strict | 31/31 PASS，包含主规格和 active changes |
| 当前改动 Python Ruff | 36 个已修改/新增 Python 文件 PASS |
| 全应用 Ruff | 未通过：12 个与 HEAD 完全一致的既有问题，新增应用问题为 0；不能将范围 PASS 写成全应用 PASS |

临时 PostgreSQL 容器 `aics-f7-final-local-20261001` 已停止；随后 exact-name 查询为空，原匿名卷 inspect 返回不存在，确认回收。没有宿主项目目录挂载。

## 独立复核与修正

- Delivery/Account/官方冻结正文/claim/发送点/Unknown/CLI/界面：独立只读 Scope B APPROVE，限本地实现，不代表平台验收。
- Security/Provider/Connector/Commons：首次 Scope A CHANGES_REQUIRED。Connector 验证没有绑定 fetch/mapping 执行代码；Commons 默认 marshal 指纹受字符串 interning 影响。
- 主 Agent 实际新增 4 个 RED 回归：三个 Connector executor 替换仍沿用旧指纹、一个 Commons interning 漂移。随后最小修正：endpoint identity 加载执行代码和策略字节摘要，Commons 使用稳定 marshal v2。旧证据不可执行，但历史不删除；没有新表或迁移。
- 相关两文件 76 passed / 1 existing warning；测试 transport 在配置 profile 前安装，同一执行器的网络失败使用受控响应失败，不再把替换代码误当普通网络失败。
- 定向独立复核 APPROVE：两项发现闭合，仅批准对应修正；与原整阶段 Scope A 无其他发现和 Scope B APPROVE 合成完成 10.9。本地测试全量初次 1624 passed / 1 F2 fixture failed：旧测试在配置验证后替换 transport，已将同一夹具安装移动到配置前，81 相关通过；完整后端最终 1625 passed，退出码 0。独立复核亦确认 fixture 顺序调整未放宽断言。
- 策略源码摘要是保守失效：修改 url_fetch 模块的 legacy safe_fetch 源码也会改变 typed 身份，要求重新配置/探测；不是保证所有 legacy 改动都不影响 typed 指纹。不会改写旧历史或授予新执行权。

## 长期契约 / TODO

F7 10.9 本地独立复核已完成，进度 96/105；10.7 全部门禁仍不勾选。真实 Commons、供应商、官方 token/upload/create/readback 和一般长文合同仍未验证；F8 0.1 未解除。不得用上述本地 fixture 或已批准短稿例外生成一般 verified。

本文件与 `progress.md`、`findings.md`、active OpenSpec 为本地证据入口。依赖与启动不变：API 现有虚拟环境 pytest/Ruff、Web npm build、OpenSpec strict；PostgreSQL 仅隔离可丢弃验收库。未 commit/push/deploy、生产迁移、canonical sync/archive。
