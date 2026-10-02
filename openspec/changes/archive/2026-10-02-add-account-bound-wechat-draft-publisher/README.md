# 账号隔离的微信公众号草稿交付方案

2026-10-02 精确输入授权后的真实草稿验收成功：Candidate6/Target6/Attempt6仅执行一次，token/asset_0/create完成、有效media_id落库，状态succeeded/awaiting_manual_receipt；未公开发布、可选远端回读或重试，五条旧记录全字段不变。2.8a完成，当前19/22，剩余2.8一般合同/平台范围、2.9终验/提交、2.10单独归档。只更新验收记录，无业务代码/依赖/迁移、正式库/配置或启动变化；以下阻断/18/22为历史。

2026-10-02 新授权测试稿已在私有副本经产品链路冻结审批/预检（Candidate6，118字节HTML，原19723字节封面，保留五条旧Unknown）；本机auto-review在进程启动前拒绝外发，要求用户明确具体账号/正文/封面。未调用微信、无新Target/Attempt，不能绕过；仍18/22，保留预览等待精确授权。无业务代码/新依赖/迁移或启动变化，详见根验收文档。

2026-10-02 本地响应兼容修正已获授权并实施：application/json或text/plain均必须严格解析JSON并验证操作字段/media_id，其他失败门槛不变。129定向、全后端1660 passed/28 skipped（77.68秒）、15正向/16拒绝无网络probe、strict33/Ruff/diff及独立窄复核APPROVE。未调用微信、不重试旧Unknown或归档；仍18/22，四项真实验收/终验/归档继续待办。无新依赖、迁移、前端或启动变化；以下待批准兼容等是此前阶段记录。

2026-10-02 新授权一次测试已执行：token成功，asset_0 HTTP200/text/plain被产品application/json响应门槛拒绝；新Attempt5 Unknown，无create/media_id。WeWrite实际源码直接resp.json()，此兼容差异已定位但本轮未修订接受合同或业务代码。旧四条全字段未变，不重试；仍18/22，无新依赖、迁移或启动变化，不算真实平台通过。详情见根验收文档。

2026-10-02 仅本地诊断细化已实现：未来Attempt增加固定phase/reason、有界整数http_status与response_type分类，持久化再次过滤且无原始header/body/error；缺media_id归响应合同失败。129定向、全后端1660/28 skipped（74.80秒）、strict33/33、Ruff/diff、无网络探针及独立诊断窄复核通过；仍18/22，未调用接口、未改旧Unknown，不宣称真实上传已修复。无新依赖、迁移、前端或启动变化；门禁最终结果见根progress.md。

2026-10-02 最新授权实验仍未通过：产品 token 成功，asset_0 上传响应未确认，Attempt 4 Unknown，无 draft/add/media_id；旧三条保持原样、不重试。预检/冻结审批和实际记录在私有验收副本，未写正式库或公开发布。本轮只更新证据，无业务代码/新依赖/迁移/启动变化；仍 18/22，2.8/2.8a 不关闭，不能用旧全量结果代替本轮真实失败。

2026-10-02 当前准确状态为 18/22，剩余 2.8、2.8a、2.9、2.10。前一批 token 改了 GET 却遗漏 endpoint，本轮纠正为 `/cgi-bin/token`，并修正接口拒绝的 dispatched 证据；既有回归先失败后通过，110 定向、全后端 1660 passed / 28 skipped / 8 existing warnings（81.27秒）、Ruff/strict/diff 及独立窄复核通过。最新真实 Attempt 3 停在 token，无上传/create/remote_id；本轮不发送新请求或改写旧 Unknown。不关闭真实平台/全阶段/归档任务，无新依赖或启动变化；下文 17/20 等为历史记录。

2026-10-01最新修订：用户批准指定账号的<2048 UTF-8字节最终HTML草稿实验，仅token/上传/create/readback，非公开发布或长文合同解除。scope必须绑定exact账号/Candidate/hash/Target/Attempt/action/expiry并经产品链路执行；默认合同gate保持false。active四份规格已补齐，受限实现/真实验收仍待完成，任务仍17/20，无新依赖/迁移或启动变化。

## 需求背景

用户确认：一角色多账号，每个真实账号只属于一个角色；需可替换发布API适配器，而非全局当前账号。基线main@da73bbb，F7仍95/105。

## 目录结构

proposal.md说明范围；design.md定义账号/凭据/冻结内容边界；specs/保存新增长期契约；tasks.md按两大批组织实施。

## 已完成

最新2026-10-01：2.2/2.6/2.7已完成，17/20。跨项目共享Profile/registration实际锁交错、退化锁序mutation、prepare后轮换与foreign账号负向、41隔离UI均通过，详细数值见根progress.md。独立本地窄复核APPROVE；不是平台端成功。无业务代码/依赖/新迁移，启动方式沿用，临时PG/Vite已回收。

最新PG验收增量：6 native PG + 7连接隔离guard通过，同项目授权/执行和两种registration锁等待已实测；独立账号迁移/绑定竞争另1项通过。专用临时库已回收，未改业务/前端/迁移。仍14/20；2.2/2.6尚需跨项目共享profile强制锁交错证据，不用本轮同项目竞争代替。以下“PG未验”是历史阶段记录，当前已证范围以上述边界为准。

最新双账号交付/Receipt及恢复入口已补：A/B精确runtime/history独立，A轮换B继续；官方草稿human_confirmed只作为交付回执，不同步发布历史。ProjectReviewCenter可显式回读known ID和对账running中断，取消/归档无动作。80定向、9 UI gate、build预算通过，最终结果见progress.md。仍14/20，PG/真实平台/完整revoke UI及全阶段验收仍TODO；无新表/依赖/迁移，API/UI启动沿用。

修复后最终1554 backend/19 skipped、68定向、36 UI fixture、TS/Vite/FE-P1/strict31/Ruff/diff及修复复核APPROVE。official未决prepared/running的Receipt以DB查询拒绝；exact official mutate project→target锁refresh/re-auth，legacy不改。以下80/1548等均为修复前记录，不作为最终证据；仍不证明PG或真实账号验收。

最新14/20：2.3的整条内文图片Delivery隔离验收通过，18项定向证明exact cover/inline bytes及批准HTML固定槽位替换，cover后inline撤权/文件变化拒绝create并保留partial。业务规则/依赖/启动方式不变；全量与窄复核见progress.md。双账号完整Delivery、PG竞争、恢复UI/浏览器及真实平台仍待完成，下面13/20是上一批历史记录。

最新13/20：旧候选缺render拒远端且不补字段、partial安全metadata/known-ID、严格readback闭合（1.6/2.4/2.5）。新wechat_official_delivery.py通过exact key接Delivery，prepare和每步durable in_flight、私有claim/live锁与项目审计；显式人工恢复使旧claim失效，未交付确认后才新编号。已知草稿可POST official-readback，只读不create。十五本地回归含SQLite双connection唯一prepare、156定向与1543全后端/19 skipped、build/strict/Ruff/diff及修复复核通过；不是PG或微信平台验收。

最新10/20：task2.1官方bounded transport实现完成；固定host/path、一次解析公网IP pin与原host TLS、bounded DNS/25秒/头及字节预算、单次请求且无代理/重试/重定向。纯render映射绑定账号/runtime/槽/hash，严格readback；还不是DB/Delivery闭环。非法URL port脱敏和transport/render代码指纹回归先RED后GREEN，独立foundation复核APPROVE。当前1528全后端/19 skipped、141定向、构建/预算/strict31/31/Ruff/diff通过；没有本轮浏览器重跑或真实平台验收。以下9/20为历史。

最新9/20：1.5冻结表示、1.7两入口账号配置、1.8本地回归/独立复核完成。祖先归档只读缺口经三API RED→GREEN和两UI入口验证闭合；最终1501后端/19 skipped、139定向/1 skipped、15账号/12预览UI fixture、构建预算/strict/Ruff/diff通过。1.6未来dispatch缺render拒绝仍待Batch B，当前零效果descriptor不能证明transport已实现。F7/F8与真实平台保持未完成，以下6/20及待复核文字是历史。

Settings渠道分区已复用lazy账号面板，viewer所属账号只读与管理员A/B隔离保存通过13项账号UI fixture；12项冻结预览重新通过。新全后端1498/19 skipped、定向136/1 skipped、构建预算/strict31/31/Ruff/diff通过。Batch A独立复核尚待返回，任务仍6/20；以下旧记录保留为历史，不表示inline或Settings仍未实施。当前TODO是transport/Delivery、全阶段/真实验收；无新依赖/迁移/真实请求。

独立图片链路复核APPROVE：pure contract与SHA256大字节边界实际验证、历史canonical一致；仅本轮范围，不代表整个Batch A/F7或真实平台通过。source正文图片已实现，后续TODO是全Batch A收口、Settings、官方transport/Delivery和真实验收，而非重新实现inline位置。

最新正文图片批：兼容image block+exact inline slot、source Text v2精确映射、live素材校验、冻结Review/本地ZIP通过；预览PNG/JPEG真实字节hash匹配后按冻结位置显示，LAN SHA256兼容，无外部网络/脚本权限。全后端1498/19 skipped、10项组件UI fixture、构建/FE-P1/strict31/31/范围Ruff通过，最终独立窄复核待回读，不代表真实账号验收。无新依赖/迁移；复跑沿用原API/Web方式和既有UI脚本。

Review前端已接入同一冻结official_render，使用sandbox/CSP只读预览并显示精确槽位/不可用原因；新组件与UI夹具位于apps/web/src/product/OfficialArticlePreview.tsx和apps/web/scripts/fe-f7-official-preview-ui-acceptance.mjs。此子集不关闭1.5，inline定位仍未完成；55项后端定向、构建/预算及独立窄复核通过，未进行真实平台动作。

最终8项UI fixture gate、strict31/31、范围Ruff和diff-check通过。此脚本只运行真实预览组件及冻结数据夹具，不是平台/全链路验收；无新依赖或启动方式变更。

当前最新6/20：task1.4账号runtime与安全缓存完成，exact新key的server-derived verification/目标核验分派不放宽legacy；稳定环境HMAC key缺失不可用。正文/cover冻结后端子集已落地，inline定位/UI仍待完成。定向125/1 skipped、全后端1487/19 skipped、构建预算、strict31/31及窄复核通过；本轮未跑浏览器/真实平台，不用旧记录冒充新验收。

上一批达到5/20：0.1/0.2和1.1–1.3完成，账号身份约束、管理员绑定/CAS安全配置、f7c000000001迁移及Identity面板基础已实现。隔离SQLite/PostgreSQL真实双连接竞争与迁移往返通过；该批全后端1478 passed/19 skipped、构建/FE-P1、最终9项UI fixture gate通过。独立后端窄复核不是整体F7或真实微信验收。

## 待完成

当前准确剩余3项：2.8真实平台验收（需已核实官方合同、具体账号/凭据及动作授权）、2.9全阶段复核/本地提交、2.10单独授权canonical同步归档。以下6项/7项等均历史，不将fixture成功转成真实verified或F7/F8完成。

当前仍6项：2.2/2.6–2.10；跨项目锁顺序、完整revoke/不可用UI、真实接口与阶段终验/提交/授权归档保持未完成。下文旧7项等仅历史记录，不作为当前准确任务数。

当前剩余准确7项：2.2/2.3/2.6–2.10。2.2已落地锁/CAS但PG授权/执行竞争未验，不提前勾；2.3需inline真实Delivery夹具；2.6双账号/PG/Receipt，2.7恢复UI/浏览器，2.8真实平台，2.9阶段终验/提交，2.10单独授权归档。新API前端入口仍待2.7；以下1.6等TODO为历史记录。

当前准确剩余：1.6与2.2–2.10。首先接target/Account/registration/source锁、唯一执行claim、partial安全metadata和未知结果对账，再做DB/浏览器端到端与真实合同/平台门槛；纯函数不能替代这些验收。官方remote_contract_ready仍false，fixture不会解锁生产请求。

用户已确认首批微信公众号草稿箱/素材管理权限开放，不再要求重复确认；该陈述不是实际API验证。task0.1剩余官方正文限制冲突未消除，真实账号动作仍单独授权。

用户于2026-09-30批准正文限额冲突仅阻断远端执行，不阻断本地apply。待完成：账号resolver/verification指纹、审批前冻结官方render、Settings完整入口、Delivery adapter/本地回归及真实合同/平台验收。真实上传/回读另需精确账号及动作授权。F7/F8并未因此完成。

## 关键设计决策

最终本地UI为9项fixture gate，包含历史导航恢复；前端独立窄复核问题已闭合。此结果只覆盖本批账号基础，不是完整Publisher或F7验收。

保留现有Persona父级，不多对多；新Publisher身份不继承旧WeWrite验证；发布只消费审批前冻结内容，不能临时转换Markdown改稿。

## 依赖与启动

本批沿用启动/依赖，无新表/迁移。API新路由`POST /api/v1/delivery-targets/{id}/official-readback`只接受`expected_attempt_id`，需editor及owned exact authorized actor；不接受客户端draft ID/正文/secret。复跑`.venv/bin/python -m pytest -q tests/test_f7_wechat_official_delivery.py`；真实contract gate仍false，禁止根据fixture解锁。

本批仅stdlib实现，没有新增依赖或迁移；API定向复跑 `.venv/bin/python -m pytest -q tests/test_f7_wechat_official_transport.py tests/test_f7_wechat_official_render.py tests/test_f7_capability_persistence.py tests/test_f6e_freeze_v5.py`。原启动方式不变。

沿用OpenSpec CLI和已有API/Web启动方式，无新依赖。`openspec validate add-account-bound-wechat-draft-publisher --strict`；API回归在apps/api执行`.venv/bin/python -m pytest -q tests/test_fe_f3b_content_identity.py tests/test_migrations.py`。新迁移只在隔离库执行，凭据只用账号级环境引用，不在文档/UI输入secret。
