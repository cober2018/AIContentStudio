# 当前进度

## 2026-09-29：F7 搜索素材来源地址规格预校准

- 在等待 F6D 8.4 与 F6E SPEC 独立定向复核期间，只读审计发现 F7 task 4.5 的“保存来源 URL”可能与既有签名 URL 禁存契约产生歧义；当前 `materials.create_revision()` 的 `source_url` 是原样传入持久层的字段。现仅修 F7 design/tasks/Capability delta：公开稳定引用地址须正向校验，临时签名抓取/预览地址不得落库或回显；无法证明安全时保留来源标识和单向哈希。没有修改业务代码、迁移或 F6E 门槛。
- OpenSpec all-strict 30/30、`git diff --check` 通过；F7 仍未 apply，F6D 78/79、F6E 2/100。F7 后续仍需独立 SPEC review、真实凭据/账号授权与实际平台 read-back 才能宣称外部能力 verified。

## 2026-09-29：F6D D1–D3 修复与 F6E E1 规格校准

- 外部独立复核基线 `main@364a49a` 给出 F6D 三项实施问题与 F6E 一项需求缺口；本地逐段核对后，仅修 Video v2 冻结 Review 结构展示、跨轨道 `(role, slot_key)` 唯一性与非法枚举类型的 422 领域错误。既有 v1/Text/Graphic 分支未改；没有新增表或迁移。
- 定向 Video 文档测试 71 passed；全后端 1026 passed / 2 skipped / 5 warnings。前端 TypeScript/Vite 与 FE-P1 bundle gate 通过；OpenSpec all-strict 30/30、scoped Ruff 通过。隔离 SQLite `/tmp/aicontent-f6d-acceptance.A6dQ2B/studio.db` 与同父媒体目录、独立 API/Vite 端口完成 12 项浏览器闭环，报告 `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6d-browser-evidence-4XIweO/report.json`，页面错误 0；测试服务已停止。浏览器新增验证冻结脚本/时间线/配音/字幕/叠字/封面，以及当前 Master 升版后旧 Candidate 结构不变。
- F6E 只补标准 active change：v5 以 `(unit_id, variant_key)` 系列判定 Candidate 当前性与幂等范围；三系列任意审批顺序、同系列替代、Master 真漂移及 v3/v4 共存均列为场景/任务。F6E 未做业务 apply，0.1/0.2、F6D 8.4 仍须修复后的独立定向复核；不推送/部署/生产迁移/主规格同步/归档。

## 2026-09-29：F7 既有字段脱敏规格补强（未 apply）

- 在 `main@f706e86` 复核 F7 设计与当前模型：`MaterialRevision.prompt_text/source_url/source_metadata_json/metadata_json` 和 `ConnectorEndpoint.last_pull_error` 都是真实持久字段，原 F7 广义脱敏要求未逐字段阻止 raw prompt、签名 URL 与异常文本落库。标准 F7 design、能力主 delta、tasks 3.8/5.10 现补安全投影及成功/失败两条负向校验；原始总包和业务代码未动，F7 仍 0/105。
- F6D 独立实施复核和 F6E 修订版独立 SPEC re-review 仍是业务推进门禁；本次 F7 规格预审不等于它们通过，也不开始 F7 apply。
- OpenSpec all-strict 30/30 PASS、`git diff --check` PASS；当前任务数仍 F6D 78/79、F6E 2/98、F7 0/105。仅提交本地规格检查点，不推送/部署/同步主规格/归档。

## 2026-09-29：F6E 授权 delta 一处语义收紧（未 apply）

- 本地对照 F6E 六份 delta 与 FE-F4 canonical 后，修正 FE-F4 delta 中笼统的账号/渠道/形态/动作能力闸门：手工 `copy_package`/`manual_handoff` 可在账号活动、身份归属、单元绑定及冻结目标校验后明确作为人工动作；远端效果必须额外具备精确验证，不能从自由格式账号 profile 推断。F6E 任务仍 2/98，F6D 仍 78/79；独立复核未获得，不进入业务 apply。
- 本批只改规格与跟踪文档；OpenSpec all-strict 30/30、`git diff --check` PASS。原始用户包、业务代码和迁移未改；不推送、部署、同步主规格或归档。

## 2026-09-29：F6E 0.3/0.4 前置审计完成（仅规格与证据）

- 基线 `main@c295174`、Alembic head `f6a000000001`；复读 Unit/Master/Candidate/Review/Delivery/Registry 后确认当前无 ChannelVariant/v5 模型或业务分派。审计前 tracked tree clean；用户原始规格包仍为未跟踪且未改。
- 新跑后端全套 `1009 passed / 2 skipped / 5 warnings`；前端 TypeScript/Vite/FE-P1 PASS，`/projects` 初始 JS 224.75 kB raw / 72.89 kB gzip，通用 Production 276.96 kB raw / 88.24 kB gzip。这是 F6E apply 前基线，不是 Variant/v5 验收。
- `findings.md` 已逐项映射 superseded 旧 V1 的七个 Scenario、PRD §15 的 15 条和 §16 的 30 个真实 Topic/六项指标/发布门槛；未重新激活旧 change，也未把文档映射视为验收通过。F6E 仅勾 0.3/0.4，11.8 保持待真实验收。
- F6D 8.4 独立实施复核与 F6E 修订后独立 SPEC re-review 仍缺；不进入 F6E business apply，不改业务代码/迁移，不推送、部署、同步主规格或归档。
- 本批 `openspec validate --all --strict` 30/30 PASS、`git diff --check` PASS；`openspec list` 显示 F6E 2/98、F6D 78/79。CLI 将 superseded 旧 V1 列为 in-progress 只是按未勾任务计算，不改变其 `.openspec.yaml` 的 superseded 事实。

## 2026-09-29：F6D→F7 移交义务核销

- 本地 `main@d85dc08` 核实 F6D 4.5 只要求把真实 Provider 执行、接受结果字节/许可/血缘/权利与响应脱敏写入 F7；F7 标准 spec 及未勾任务 5.1–5.11、6.1–6.7 均明确承接。仅将 F6D 4.5 的“移交完成”勾选，F7 Provider 本身仍为未实施/未验证。
- F6D 从 77/79 变为 78/79；8.4 独立 SPEC/后端/前端/Review/包/浏览器实施复核仍无结论，不称 F6D 最终通过。F6E 标准规格待独立 re-review，business apply 不启动。本批无业务代码、迁移或外部发布动作。

## 2026-09-29：F6E 五项独立 SPEC 反馈修订（未 apply）

- 基线 `main@d85dc08`；仅标准 F6E proposal/design/tasks、三份相关 delta、README 与计划/进度/发现记录更改。原始总包、业务代码与迁移未动；不推送/部署/运行生产迁移。
- 旧 V1 change 的 superseded 元数据核实；保留七个历史 Scenario 与 PRD §15/§16 义务。补 `payload_schema` 与五种有界 canonical schema、首批 v2 Master/Registry artifact_kind 矩阵、v5 唯一 Variant source pointer/投影列、`LLMRun` exact-input/accepted-output 安全血缘。F6E 任务由 96 增至 98，0 项实施完成。
- 六份 delta 原有 Scenario 标题全部保留；单 change strict PASS、全库 OpenSpec strict 30/30 PASS。独立 SPEC re-review 待取得；F6D 8.4 独立实施复核也待取得，F6E business apply 仍被门禁阻断。

## 2026-09-29：F6D 录音 WAV 闭环补强

- 真实 RIFF/WAVE 录音可上传但无法保存到 Video v2 Master：上传读客户端 `audio/wav`，后续无声明嗅探返回 octet-stream。两项定向测试先 RED；在共享嗅探器识别 RIFF/WAVE 且不误判 WEBP/未知 RIFF 后 GREEN。v4 package 的 WAV `.wav` 成员集成测试先 RED 后 GREEN。
- 全新临时数据库 `/tmp/aicontent-f6d-acceptance.jx9blb/studio.db` 与兄弟 media 目录跑完整 Video 浏览器闭环 11 项通过、页面错误 0，包含 WAV exact ref→Candidate v4→Review/Approval→本地 ZIP 字节/hash；无外部 Provider/Publisher 调用。
- 新跑全后端 1009 passed/2 skipped/5 warnings，前端构建和 FE-P1、全库 OpenSpec strict 30/30、范围内 Ruff、JS 语法和 diff-check 均通过。连接健康检查成功，但专用 ChatGPT 内置浏览器工具当前缺席，独立实施 review 仍未完成；F6D 保持 77/79，F6E 未 apply。

## 2026-09-29：F6D 验收素材隔离修补

- 查明既有隔离浏览器验收只有临时 SQLite/端口，素材仍落仓库共享 `apps/api/app/media/material/`。先写针对媒体根目录 override 的失败测试，再使 `asset_media.MEDIA_ROOT` 支持绝对路径 `AI_STUDIO_MEDIA_ROOT`；浏览器脚本强制媒体与临时数据库同父目录，并按 MaterialRevision hash 实际核查 MP4/MP3 字节。
- 最终另建全新空数据库 `/tmp/aicontent-f6d-acceptance.kubyUY/studio.db` 并升级至 head，素材根目录同父级；API/Vite 用独立 18262/15662 端口启动，浏览器 11 项闭环 PASS、页面错误 0，报告见 `docs/FE_F6D_ISOLATED_ACCEPTANCE.md`。测试进程已停止；临时文件保留供核查，旧共享素材未清理。
- 新跑全后端 1007 passed/2 skipped/5 warnings，定向 55 passed，前端 TypeScript/Vite/FE-P1 PASS，全库 OpenSpec strict 30/30 PASS。F6D 仍 77/79：4.5 真实 Provider 属 F7，8.4 独立实施复核未获；不能据自身测试宣布 F6D 全面关单或启动 F6E 业务 apply。

## 2026-09-29：规格保留审计（中断后继续）

- 当前 `main` tracked 改动仅为 F6E 标准规格及 README/task_plan/progress/findings；用户原始包仍未跟踪、未改，F6D 77/79、F6E 0/96、F7 0/105。
- F7 原始 96 条 checkbox 与标准 105 条逐行对照：`comm -23` 没有缺失行，标准版仅新增 9 条执行可用性、项目素材/权利、Provider 结果脱敏、Publisher 再验证等安全门禁。这证明任务文本保留，不是 F7 业务能力已经落地。
- F6E 原包的 X 单推适配已补回标准长期规格/任务，适配器就绪前继续显示 unavailable；F6D 未获实施独立复核，不启动 F6E 业务 apply。
- 本批最终全库 OpenSpec strict 30/30、`git diff --check` 均通过；仅规格/记录文件待本地提交，没有运行本批业务测试或迁移，不能将上轮 F6D 测试结果当本批重测。

## 2026-09-29：F6E 原包范围保留修正（未 apply）

- 对照用户总包的 F6E 原始 102 项计划与当前标准 96 项 change，确认原任务 6.2 要求已注册的 X 推串和单推均纳入适配。当前 `seed_v1_channel_profiles()` 已发布 `x/thread`、`x/single`，上轮标准规格只明确实现推串，等于把单推无授权延期；现修正为 F6E 必须分别实现/测试两种适配及本地包，适配器完成前维持 unavailable，旧 `x_thread` v3/v4 行为不变。
- Variant 修订的 source_kind/edit summary 血缘、显式 regenerate 不自动写入、X 单推浏览器闭环和 archive-readiness 交接也已补进任务/规格。尚未修改业务代码或 migration；F6D 仍待独立实施复核。
- 原包 0–11 组与标准 0–11 组已逐组映射（适配/方法、冻结字段和门禁可合并任务，不可合并掉能力）；全库 OpenSpec strict 30/30、`git diff --check` PASS。没有把 96 个标准 checkbox 冒充原包 102 项的逐条完成证据。

## 2026-09-29：F6E 规格校准（未 apply）

- 当前本地 `main@d3c37ec`，F6D 为 77/79：真实 Video/TTS/ASR Provider 接收仍属 F7，F6D 实施独立复核仍待取得；F6E 业务代码未启动。
- 审计 F6E 标准包与实际 Registry/Unit/Master/Delivery 后，只修正 proposal/design/tasks、ChannelVariant 主 delta 和 FE-F4 delta：v5 首个 X 推串目标为已发布 `x/thread`；旧 `x_thread/thread` 无发布版 profile，保留 v3/v4 行为但不得冒充 v5；已注册的 `x/single` 是适配器未实现/未验证，而非“未注册”。v5 跨渠道授权按冻结 Variant 目标渠道/形态分派，保留 Unit/身份/账号约束；远端效果需要 F7 精确验证，手工本地包不得冒充远端能力。
- OpenSpec 全库 strict 30/30 PASS；后续仍需独立 F6D 实施复核、F6E SPEC review 与前置门禁，不能据此认定 F6D/F6E 功能完成。不 push/deploy/生产迁移、不同步主规格或归档。

## 2026-09-29：FE-F6D apply（进行中）

- Video v2 隔离浏览器验收已在独立临时 SQLite/API/Vite 上通过：类型化脚本/镜头/时间线/配音/字幕/叠字及 exact refs 保存/刷新；双窗口 409 保留本地改动；真实 MP4 字节/hash 预览与输入绑定证明分离；输入改变令旧成片失效。随后 checks→Candidate v4→Review 播放→warning 处置审批→人工授权→本地 ZIP，ZIP 内各 MP4 条目逐条 SHA-256 与 MaterialRevision 一致。旧 v1 显式升级、稳定差异、派生子修订历史、撤权阻断包及归档只读也经浏览器验证，页面未出现运行时错误。验收报告位于 `docs/FE_F6D_ISOLATED_ACCEPTANCE.md`，原始本地证据目录在其中。任务现 77/79；本地范围提交 `ca16b39`，4.5 为 F7 真实 Provider 后续义务，8.4 独立实施复核尚未完成，不称最终通过。
- 新跑全后端 `1006 passed / 2 skipped / 5 warnings`，Video/Graphic/Text/F6A/Review 定向 `229 passed / 1 warning`；前端 TypeScript/Vite 与 FE-P1 PASS，Video 模型 9/9；`/projects` 初始 JS 224.75 kB raw/72.89 kB gzip，通用 Production 276.96 kB raw/88.24 kB gzip，Text TipTap 仍只在 Text 懒加载闭包；OpenSpec strict 30/30，相关 Ruff 和 diff-check PASS。F6D 实施独立复核因专用浏览器入口缺失而未能执行，绝不以本地自审冒充。
- 验收数据库/端口独立，但应用媒体根目录仍是共享的内容寻址本地目录；上传不会覆盖相同 hash 文件，本轮不删除可能被其他本地数据库引用的测试字节。报告已明确此限制。

- 6.9 前端接口已接线但尚未勾选：v1 preview 不伪造 ready v2，编辑器中的画幅/时长为待人工确认的填写起点，旧脚本与镜头 ID/顺序锁定，首个升级修订不带旧 render；服务端 CAS/警告一致性仍为最终闸门。v2 版本差异按稳定 ID 展示脚本/镜头/轨道/片段/字幕/叠字及素材/渲染/上下文，未计算伪视频文本相似度。模型 9/9、TypeScript/Vite/FE-P1 PASS；浏览器升级/冲突/归档验收前维持 56/79。

- 4.3/6.6–6.8：Video 工作台显示项目共享 image/video/audio 精确 Revision、MIME、来源、公开权与 hash；最终成片仅从可见/允许公开的 MP4 中绑定，模型不伪造 attestation。真实 MP4 预览需主动读取、限制大小并校验字节 SHA-256；结构预览明确非成片。Video/TTS/ASR 项目能力状态由后端读出，未验证时明示不可执行。绑定成片后先显式保存，再由现有输入哈希确认按钮追加修订。模型 8/8、TypeScript/Vite/FE-P1 PASS；累计 56/79。浏览器完整绑定/确认仍待 7.x 验收，不能称本次已实际浏览器跑通。

- 6.4/6.5 Video 类型化时间线与媒体面板：轨道/片段增删、start/end/trim/volume 边界反馈，Video 镜头片段与 audio/music 精确 Revision placement；整片 recorded/TTS 已导入音频、音乐、封面 exact refs；字幕 cue 编辑及有界 SRT 本地导入、叠字坐标/时间。所有编辑只改本地 draft 并令旧 render 失效，不声称已合成/ASR/TTS 成功。模型 7/7、TypeScript/Vite/FE-P1 PASS，/projects 224.75 kB raw、通用 Production 272.26 kB；累计 52/79。最终成片绑定、Video v1 UI 升级、隔离浏览器及 F7 Provider 仍待办。

- 6.3 镜头编辑：项目共享素材可按 exact Revision 选择 image/video，展示来源、权利与 hash；模型绑定 `shot_source` 的 placement/slot/sort_order，并在镜头重排/删除时同步重排，非法 kind/权利拒绝。镜头时长、用途、景别、转场、脚本关联可编辑。4/4 模型测试及 TypeScript/Vite/FE-P1 通过；本次后端全量 1006 passed/2 skipped/5 warnings。累计 50/79；其他媒体位置的 picker 仍未实现，6.6 未勾。

- 6.1/6.2/6.12 Video 前端首批：普通用户不再直接编辑 Master JSON；Video v2 typed draft 与 script/shot 稳定 ID 操作由纯模型维护，本地 dirty 与显式保存走 `video.master.v2`，旧 v1 只读。模型先 RED（模块缺失），后 3/3 GREEN；TypeScript/Vite 与 FE-P1 bundle gate 通过，Video 模型/壳仅在 Video lazy closure，通用 Production/Text/Graphic 静态闭包无泄漏。累计 49/79。镜头素材、时间线/音轨/字幕/叠层、v1 升级 UI、最终成片选择及完整浏览器验收仍未完成；全后端复测进行中。

- 4.4/4.6/4.7 成片闸门定向复核：伪造 renderer origin/version 422、wrong-kind 成片保存 422；已确认 Master 的最终视频在 freeze 前若 kind 变更、字节丢失、哈希不匹配或权利撤销均 409。payload/source/context/profile 变化产生不同当前 render-input hash，手工 attestation 仍是 manual。跨不同时钟重新构建 v4 ZIP 曾因 `writestr` 当前时间导致字节变化，固定条目时间和权限后定向两例 PASS；累计 46/79。全后端与后续浏览器仍待复核。

- 4.1/4.2 Video/TTS/ASR 能力边界：项目级 GET 返回 configured/executable/verified 各为 false、`project_provider_not_verified`，跨项目 404；三种 POST 均 typed unavailable、不回显输入 secret，也不新增 MaterialRevision、ContentMasterRevision 或项目素材引用。Video/Graphic 能力定向 2 passed；累计 43/79。真实 Provider 接收/许可/血缘和响应脱敏仍归 F7，不将静态不可用接口算作真实 Connector。

- 3.5–3.9 派生子修订闭合：新增专用 Video v2 `/derive`，仅显式 user_edit 的具体结果可追加；长转短真实缩短 duration，画幅转换真实改变 ratio，镜头再生成的手工路径必须指向经项目可见性/字节/类型/权利验证的新素材，不能用标签变化冒充。source ID/hash/context/current head 与 request-hash 幂等检查通过，普通 save 伪造 `source_kind`/`edit_summary.derived_video` 被拒；未验证 Provider 返回 503，Master 与 MaterialRevision 不增。全量后端新跑 1005 passed/2 skipped/5 warnings，OpenSpec strict 30/30、相关 Ruff 与 diff-check PASS；最后补充的无媒体写入断言另定向 1 passed。累计 41/79，前端本批未改。

- 5.6–5.10 后端闭环及旧链路回归通过：独立 Video v2 项目夹具将手工 Master→输入绑定 MP4→专业检查→Candidate v4→Review→带 warning 处置的审批→交付授权→确定性 ZIP 完整跑通，PNG/MP4 与批准 revision 字节一致，重复下载字节一致，无 Draft/Topic/Mother、远程调用或 DeliveryAttempt。freeze/approve/authorize/package 的 live rights 撤销、文件字节篡改、候选 manifest 篡改和新 Master 后旧授权均拒绝。Video/Graphic/Text/历史 Review 与交付定向 255 passed；新跑全后端 1004 passed/2 skipped/5 warnings，OpenSpec strict 30/30、相关 Ruff、diff-check PASS。累计 36/79；Provider、派生操作、前端与浏览器尚未完成，前端本批未重测。

- 5.5 冻结 Review 读取闭合：Video v2 Candidate v4 的 preview 使用 manifest 中的 canonical 脚本、镜头、时间线、语音、字幕、叠层、封面及成片；前后两份有效冻结候选的结构差异使用稳定 ID，`text` 保持 null，不伪造整片相似度。RED→GREEN，Video/Graphic/历史 Review 定向 68 passed；累计 31/79。真实 freeze/approval/package 与浏览器闭环仍未验收，本批最终全量门禁待复跑。

- 5.4 Video v2 Master 差异已补：稳定 ID 对比脚本块、镜头、时间线轨道/片段、字幕 cue、叠层，另列语音、音乐、封面、render、精确素材/证据和 context；不计算整片文字相似度。Project-scoped `/master-revisions/{id}/diff` 仅在目标为 Video v2 时分派，源版本必须同为 v2，旧 Text/Graphic/Video v1 行为不变。纯函数和 API 先见 RED 后 GREEN，Video/Graphic/Text 定向 83 passed；累计 30/79。Candidate Review 冻结差异与包仍待后续，当前全量门禁待复跑。

- 5.3 新鲜度回归：同 context 替换 exact source ref 使新 Master render-input hash 改变；同 source 更新 CreativeBrief 使旧 CheckRun stale，随后新 Master 的输入 hash 改变，旧 Master 冻结 hash 保持不变。live source 公开权撤销后 rights CheckRun stale 且 freeze 不可用。现有 Production Core 已满足定向回归，无需改服务。Video v2 定向测试新增 1 项，累计 29/79；本批全量门禁待最终复跑。

- Video v2 专业检查批次：有效/空 Master 的 structure/timeline RED→GREEN；身份由 pinned IdentitySnapshot、显式禁语与可用时的语义复核组成，画面/音频语义始终标记不可用，不把模型缺席写成 PASS。渠道检查精确读取已发布 video profile，profile 升版后旧 CheckRun 投影 stale；所有结果复用 append-only ContentMasterCheckRun。定向 46 passed，全后端 998 passed/2 skipped/5 warnings，OpenSpec strict 30/30、相关 Ruff 与 diff-check PASS。5.1/5.2 完成，累计 28/79；5.3 仍须覆盖 source/context freshness。前端本批未改，未将旧 build 当作本批验收。

- Video v1→v2 升级路径已补：preview 只投影已存脚本及稳定镜头 ID/列表顺序，明确画幅、时间线和镜头时长需用户补齐；commit 必须提交完整 canonical v2 文档、精确引用与当前警告确认，保留旧脚本/镜头、禁止继承成片，通过 source payload/context/head CAS 与 request-hash 幂等生成追加式 child。两条缺端点的 RED 分别验证，升级定向 8 passed；最后反向 schema 断言加入后全量后端重新运行 994 passed/2 skipped/5 warnings，OpenSpec strict 30/30、相关 Ruff、diff-check PASS。2.5/2.6/2.9 完成，当前 26/79；2.7 的旧 Candidate hash 回归、Video 前端和浏览器验收仍待证明。
- Video v2 时间线中已放置的 audio/music item 现必须有精确 MaterialRevision；空轨仍可编辑，全片 voice/music 声明不强迫伪造轨内位置。两条漏绑用例先 RED（此前错误保存），修复后 Video 定向 34 passed；字幕重叠与空轨/全片音源回归通过。正确 apps/api 工作目录全后端 986 passed / 2 skipped / 5 warnings，OpenSpec strict 30/30、相关 Ruff 和 diff-check PASS；3.2 完成，当前 23/79。无前端更改，不把本批计作视频浏览器或最终成片验收。
- Video v2 readiness 现返回从 canonical Master 文档确定性生成的脚本/镜头/时间线/语音/字幕/叠层/音乐/封面投影，类型明确为 `local_assembly_preview`、`final_render_verified=false`。测试先见缺失 `kind` 的 RED，修复后 Video/F6A/F6C 定向 `84 passed`、全量后端 `982 passed / 2 skipped / 5 warnings`、相关 Ruff、OpenSpec strict 30/30 与 diff-check PASS；3.4 完成，当前 22/79。它不是已生成/已验证 MP4，也未证明 Video Studio 浏览器预览。
- Video v2 叠层的有效正文与 x/y 成对显式位置现在在 canonical save 前校验；之前缺坐标或空文字会保存，两个场景先见 RED、修复后含正向用例的 Video/F6A/F6C 定向 `83 passed`，全量后端 `981 passed / 2 skipped / 5 warnings`，相关 Ruff PASS。封面精确 image 类型/真实字节/公开权限继续由已有 Master 保存闸门保障。3.3 已勾，当前 21/79；未把 UI 预览、成片或 Provider 能力视为已完成。
- Video v2 时间线补足跨字段时长约束：镜头时长不得超过文档 duration，引用该镜头的 timeline item 不能比镜头更长；start/end/trim 的既有界限保留。两个不一致场景先见 RED，修复后 Video/F6A/F6C 定向 `80 passed`，全量后端 `978 passed / 2 skipped / 5 warnings`，相关 Ruff、OpenSpec strict 30/30 与 diff-check PASS。OpenSpec 3.1 据此完成，当前 20/79；语音/字幕关联和本地预览仍未勾选。
- 冻结 Video v2 Candidate 的 Review 读增加跨字段校验：canonical v2 文档、Master payload hash、完整 exact refs、唯一 `render_output` 与 MP4/hash/rights 快照、published profile 的冻结输入哈希、人工 attestation 输出和签认人须一致。10 个篡改变体先见 RED，修复后 11 个冻结读用例 PASS；没有改 v1/Text/Graphic 分派。全量后端从正确 `apps/api` 工作目录新跑 `976 passed / 2 skipped / 5 warnings`，相关 Ruff、OpenSpec strict 30/30、diff-check PASS。任务仍 19/79：5.10 的 package 与真实候选闭环尚未验收，不提前勾选。
- 曾从仓库根目录误跑全量测试，出现 4 个运行环境失败：3 个 Alembic 相对路径找不到配置，1 个 worker 连接到错误的相对路径数据库；在 `apps/api` 工作目录重跑全绿。该误跑不是业务回归，也不修改测试或迁移来掩盖。

- 第四批将 published exact Video profile version/rules 加入 `video.master.v2` render-input hash，并让 Video v2 readiness 实际调用 fail-closed `profile_reasons`；发布新 profile 后旧 render hash 改变。测试先见同 hash 的 RED，修复后 Video/F6A 定向 41 passed、相关 Ruff PASS；1.10 完成，当前 19/79。Video 专业 check input hash/currentness 仍属 5.x 未完成。
- 最新全量后端 `965 passed / 2 skipped / 5 warnings`，未将它当作 F6D 最终验收；本批没有前端改动。
- 第三批接入 Video v2 素材保存闸门：按 shot/timeline/voice/music/cover/render 角色核对 `MaterialRevision` 类型、项目显式引用、live public-use、真实字节哈希与 MIME；错误全部在 Master/refs 写入前返回。隔离 API 验证同一图片 revision 在两个镜头保存成不同 slot，wrong kind/hash、项目解除引用、字节篡改和撤权全部阻断，历史仅 1 个 Master/2 条 ref。定向 12 passed，相关 Ruff PASS；2.2–2.4 完成，当前 18/79。检查运行、render/审批/包仍未验收。
- 本批完整后端回归 `964 passed / 2 skipped / 5 warnings`，OpenSpec strict 30/30 PASS。Ruff 首次仅指出新增测试函数内 import 样式，已定向修正；最终需复跑相关 Ruff 和 diff-check。本轮未改前端，不将旧构建计为 F6D 前端验收。
- 第二批将 Video v2 canonical payload/ref 校验接入真实 `save_revision()` 与 schema-dispatched Video v2 adapter；显式 v2 API 保存/回读、exact profile readiness、同一素材不同镜头 slot、时间线/语音/音乐/封面/最终输出位置及空草稿 0ms 的定向验证 11 passed，相关 Ruff PASS。旧无 schema Video 路径仍默认 v1，避免悄然改写历史；专业前端日后需显式发送 v2 envelope。当前 15/79，仍缺素材项目可见性/类型/字节/权利、profile freshness、render、checks、Candidate/Review/包和前端。
- 本批新跑全量后端 `963 passed / 2 skipped / 5 warnings`；非最终 F6D 验收。前端本批没有业务代码改动，沿用此前 fresh build 基线，不把它冒充 Video Studio 验收。
- F6D apply 第一批：新增 canonical `video.master.v2` 文档验证（脚本块、镜头、时间线轨/项、语音/字幕/叠层、封面与最终视频声明）及 `ContentFormSpec.video_requirements` 投影/纯规则检查。针对新文档和渠道投影先观察 RED（缺模块/字段），实现后 7 passed，相关 Ruff PASS；1.1、1.3、1.5 已完成，当前 8/79。1.10 仍待规则接入实际 Video check/可用性，不能只因纯函数通过就勾选。尚未接入 Master save/refs/adapter，不能称 Video v2 可执行。零 migration。
- 本批全量后端实跑 `958 passed / 2 skipped / 5 warnings`，前端 TypeScript/Vite/FE-P1 基线 PASS，OpenSpec strict 30/30、diff-check PASS。注意这些门禁尚不构成 F6D 端到端验收。
- 规格检查点已本地提交 `a74a7d5`；只提交标准规格与计划/进度文档，用户原始包仍未跟踪。F6D apply 基线：Alembic head `f6a000000001`，F6A/F6C 定向回归 95 passed / 1 warning，前端 TypeScript/Vite/FE-P1 PASS，Production 初始 JS 273.35 kB，Video 不含 TipTap，OpenSpec strict 30/30，tracked tree 在规格提交后 clean。现有 MasterRevision/AssetRef/EvidenceRef/CheckRun 足以承接目标 v2（若实现反证须暂停）；0.1–0.5 已据证勾选，5/79。无业务代码或迁移。
- F6C 已在本地 `main@34ef5af` 以 74/74 收尾；F6D 仍是 active change、无业务代码或 migration。ChatGPT 独立读取后提出五项必须先修的规格缺口：Video published profile、精确媒体 ref slot、受信派生 provenance、Video 显式升级 pair、Candidate 冻结完整性。当前已回写 design、tasks 与 Video/Production Core/Review delta，任务从 73 增为 79，尚未勾选。
- 本轮明确现有 `render_input_hash` 排除 `render_output` 防循环，源素材位置进入输入哈希，最终输出另行 attestation 与冻结核验。单 change strict、全库 strict 30/30 与 diff-check 已通过；ChatGPT C2C `c2c_4a78` iteration 1 实际读取修订 diff 后给出 SPEC APPROVE / DONE。F6D 可按后端优先进入 apply；未推送、部署、生产迁移、canonical sync/归档。

## 2026-09-29：FE-F6C 独立复核与最终门禁

- AIContentStudio 的公网连接短暂返回 521，按工作区范围重建后公网 `/mcp` 回到预期的未授权 401，HTTP/2 且 HA 连接数为 2；同一 ChatGPT 项目中的新审阅对话实际读取 `main@2891bac` 当前文件，SPEC 与 frontend 均 APPROVE，后端沿用前轮 APPROVE（期间无后端业务代码变动）。原 C2C task `c2c_bc87` iteration 2 返回 `STATE: DONE`。F6C 7.10 已据此勾选，现为 74/74。
- 本轮新跑后端全套 `951 passed, 2 skipped, 5 warnings`（清除本机无效 `NO_PROXY/no_proxy`）；前端 TypeScript/Vite 与 FE-P1 bundle gate PASS，Production initial JS 273.35 kB；OpenSpec 全库 strict 30/30；F6C 两次范围提交涉及的 Python 文件 Ruff PASS。额外尝试的全库 Ruff 有 23 个既有问题，未做无关格式化，也不将其写成 PASS。浏览器闭环和旧版本回归由此前隔离验收记录支持，本轮未重复浏览器执行。
- F7 的真实 Provider 接收、许可/血缘、Project 关联和响应脱敏仍未实施；F6C 的通过不等于 F7 可用。F6C canonical 同步/归档需另行授权；未 push、deploy 或执行生产 migration。

## 2026-09-29：FE-F8 标准 OpenSpec 校准（仅规格）

- 真实起点为本地 `main@361265d`，仅用户原始包/ZIP 未跟踪；上一目标轮 F7 标准规格已提交，F6C 仍 73/74 且独立复核未签发最终通过。F8 原始包有 91 项、十条新增要求，无可验收 Scenario。
- 本轮审计现有 `deps.get_current_user()` 的 Header/default-user/自动建号、`main.lifespan()` 的 `init_db()` 与模板/设置 bootstrap、`health.check_health()` 的原始错误/HTTP200降级、raw-path metrics、`MaterialRevision.file_path` 与多处直接 `MEDIA_ROOT` 读取，及 Celery/MinIO 当前仅部分覆盖；原始 F8 不能直接把这些现状标成生产可用。
- 标准 change `fe-f8-production-readiness-operations` 已写 proposal/design、新 Production Readiness 能力规格与 Product Settings delta，原 91 项任务保留并补八项现状安全门禁，现为 99 项未开始；原十条 Requirement 均有标准场景。全库 OpenSpec strict 30/30 PASS、change artifacts 4/4、tracked diff-check PASS。仅做规格，不变更认证、媒体存储、数据库、业务代码或生产环境；独立 SPEC review、F7 前置门禁及用户规则的 apply 确认仍未完成。

## 2026-09-29：FE-F7 标准 OpenSpec 校准（仅规格）

- 真实本地 `main@775294c` 的 F6B 已是 162/162；F6C 仍 73/74（独立复核未得最终 verdict），F6D/F6E 仅标准规格草案，均未 apply。用户提供的旧 F6B 131/162 是总包规划时的历史基线，不再重复实施。
- F7 用户源包 96 项任务和十条要求已读取。标准 active change `fe-f7-capability-integrations-delivery` 现有 proposal/design、新能力及 FE-F2/System Assets/Settings/FE-F4 四份 delta、105 项未勾选任务；增加精确 Provider 响应/错误/审计脱敏、Project 素材精确引用、无字节/许可不入库、legacy 未验证自动草稿开关不得绕过远端验证。只做规格，不改业务代码/迁移；F7 apply 仍取决于 F6E 验收及项目规则要求的确认。
- 源稿十条长期要求逐项映射到标准 11 条新能力要求及四份既有能力 delta；OpenSpec strict 29/29 PASS、change 4/4 artifacts ready、tracked diff-check PASS。F7 仍是待独立 review 的 SPEC DRAFT，不提前宣称 apply 或任何真实平台已验证。

## 2026-09-29：North Star 剩余开发总目标 / FE-F6C 规格校准

- ChatGPT 原会话对同轮 F6C 独立复核仍显示错误；本地 doctor/tunnel 可用不能证明 ChatGPT 已完成独立读取，F6C 7.10 仍未勾。并行完成 F6E 标准 OpenSpec 草案：新 ChannelVariant 能力与五份既有能力 delta、96 项任务。当前代码确认 Unit/Master channel 字段可空，但 v4 仍是渠道绑定路径；新规格明确 neutral Master 仅作 Variant source，Matrix 不在 Approval 前创建 DeliveryTarget。active V1 交付七场景已映射到 F6E/F7 保留义务；全库 OpenSpec strict 28/28、diff-check PASS。未改 F6E 业务代码/迁移，未将草案视为 apply 授权，独立 SPEC review 仍待完成。
- 本轮连接器本地 `workspace_info` 可读 `main@9089c8b`，但 ChatGPT 页面显示“无法加载 ChatGPT 模型”，同轮复核消息未能发送；已清理未发送草稿，F6C 7.10 继续未勾。F6D 只补规格：衍生 Video 子修订必须有明确编辑或确定性本地变换所得的具体有效 v2 内容；未验证 Provider 需要参与时 typed unavailable、无子修订/媒体/成功回执。未进入业务 apply。
- F6C 补丁已在本地 main 作为检查点 `35df0a7` 提交；仅用户原始 OpenSpec 包/ZIP 仍未跟踪，未纳入提交。F6C 73/74，独立复核仍因连接器实际读取失败待验。本轮另将 F6D 源包机械归位为标准 active OpenSpec 草案：proposal/design、新 Video Studio 规格及 Production Core/Review/FE-P1 三份 delta、73 项未开始任务；补全可验证 Scenario、明确 F6C 完成前不得 apply、真实 Provider/输出接收和执行响应脱敏归 F7、零新表目标。F6D 未改业务代码/迁移；OpenSpec 全库 strict 27/27 PASS。F6D 仍需独立规格 review 与用户明确 apply 确认。
- 独立复核第一轮：后端 APPROVE，SPEC/前端要求三处定向修复。F7 来源包原任务未显式覆盖 Provider 执行/结果响应脱敏；F6C 设计和主 delta 已写入 F7 标准化时必须新增的响应/错误/血缘脱敏要求与负向测试，未改用户源包，也未宣称 F7 已完成。GraphicStudioModel 从通用 Production 静态导入改为仅 Graphic 时动态载入，bundle gate 现直接断言其不在通用 Production/Text/Video 静态闭包；旧产物运行新 gate 如预期失败，修正后 TypeScript/Vite/FE-P1 PASS，Production 初始 JS 从 285.80 降至 273.34 kB。画布选择按钮已暴露 aria-pressed。前端模型 20/20 PASS。F6C 仍 73/74，待再次独立复核；后端本轮未改，951 passed 是前次代码门禁，不冒充重跑。
- 第二轮定向复核未取得 verdict：ChatGPT 连接器对 workspace_info、git_status、read_file、execution_output 连续返回 internal error，明确标为 NOT_VERIFIED。工作区 doctor 首次显示安全连接重建，实际读取仍失败；随后 named tunnel 重建遇 Cloudflare API EOF，doctor 再恢复后 status 显示在线，但 ChatGPT 的再次调用仍无法读到仓库，网页回复还出现 Cloudflare challenge。当前不勾 7.10、不把本地门禁代替独立复核，也不进入 F6D。最新本地 build/FE-P1、前端模型 20/20、OpenSpec strict 26/26、diff-check 均实跑通过。
- F6C 对照一次性总计划重新校准 Provider 边界：原 77 项中四条真实 Provider 接收任务由 F7 的 4.3–4.8、5.3–5.9 承接，F6C 保留一条已验证的 fail-closed/需求移交任务；现 73/74，唯一待办为独立 SPEC/后端/前端复核。F6C 原接受 Provider 结果场景改为“未验证 Provider 请求无写入”；F7 仍必须完成真实字节、Provider/版本/提示词/许可/权利血缘、显式项目绑定、密钥脱敏与负向测试。标准 change strict PASS、diff-check PASS；业务代码本轮未改，后端/前端门禁结果沿用上一个已提交代码检查点。
- F6C 范围内实现已作为本地 `main@d0f0051` 检查点提交，当前 72/77，尚非阶段最终完成。变更涉及 Graphic v2 document/check/diff 服务、Production Core/Review/ZIP/Channel/Project 能力边界、Graphic-only UI/model 与回归、active OpenSpec 和实施记录，共 33 个受控文件；用户源包/ZIP 未纳入。提交前最终门禁为全后端 951 passed/2 skipped/5 warnings、前端模型 20/20、TypeScript/Vite/FE-P1、OpenSpec strict 26/26、相关 Ruff、staged diff-check PASS。真实外部 Provider 接收/许可血缘 4 项与独立复核仍未完成；无 push/deploy/生产迁移/canonical 同步/归档，不将手工渲染声明或本地包授权当成自动渲染/已发布。
- F6C 71/77。补齐项目级自动渲染能力的诚实不可用投影；试图提交 Renderer 来源/版本/验证字段的伪造 attestation 返回 `renderer_capability_unavailable`，不新增 Master，原手工确认仍保留 `origin=manual`。RED 两项失败（缺能力键、错误码不明确）→ GREEN 定向 30 passed。最新全后端 `951 passed / 2 skipped / 5 warnings`（排除本机无效 `NO_PROXY/no_proxy`），前端模型 20/20、TypeScript/Vite/FE-P1 PASS（`/projects` 224.75/72.89 kB，Production 285.80/90.75，Graphic/Video 不含 TipTap），OpenSpec strict 26/26、相关 Ruff 和 diff-check PASS。真实 Provider 接收、独立复核与本地提交仍未完成。
- F6C 当前 69/77。新增第二个 Graphic v2 Candidate 历史回归：旧候选预览维持首版文字/检查输入哈希，新候选显示修改后的正文和独立当前检查，Review diff 是结构化变化而非假文本相似度。测试先暴露 Review Graphic 检查摘要只读 `check_kind`，而冻结 v4 清单用 `kind`，页面因此丢失检查名称；按 schema 兼容读取后通过。exact Profile 发布版变化的检查 stale、Brief/Boundary 浏览器 stale 与 F3B pinned Identity 版本契约共同覆盖 2.8。最新 F6C/F6A/F3B 定向 97 passed、全后端 951 passed/2 skipped/5 warnings（排除本机异常 NO_PROXY）、相关 Ruff/strict 26/26/diff-check PASS；前端源码未再变，上一轮 build/FE-P1 保持通过。尚余 provider 真实接收/验证、独立复核及最终交接；不声称 F6C 已关单。
- F6C 本批 67/77。隔离 SQLite + 浏览器完成两画布保存/刷新、Brief/事实边界变化使旧 Master stale、显式接纳新上下文、封面文字绑定冻结 FactPackItem、两张真实图片重绑、按当前输入哈希人工确认渲染、八项检查（六 pass、两条 semantic unavailable warning）、Candidate v4、冻结预览、两条警告人工处置、审批和 `copy_package` 授权；状态停在 `awaiting_manual_receipt`，没有回填发布。隔离 ZIP 的 `render-1.png`/`render-2.png` 与冻结输出哈希分别为 `7de3fb43…`/`442c670f…`，顺序一致。发现同一素材既用于图层又是最终渲染时 ZIP 重复 `render-2.png`，先加失败回归再改为媒体写完后按画布顺序各写一次渲染；重下包无重复条目。上传素材的真实 `candidate` revision 状态此前被误要求 `active`，也已从失败回归修正，撤权/归档仍被阻断。隔离单元归档后 Graphic 输入/保存/检查/冻结均在浏览器禁用；另一个单元被外部并发保存 v2 后，旧页面保存明确显示 409 且历史仅有两版，未覆盖外部写入。F6C + F6A 定向 83 passed，全后端排除本机异常 `NO_PROXY/no_proxy` 后 951 passed/2 skipped/5 warnings；前端模型 20/20、TypeScript/Vite/FE-P1、OpenSpec strict 26/26、相关 Ruff、diff-check PASS。人工渲染声明不等于自动 Renderer 验证；provider 接收及独立复核尚未完成，无 commit/push/deploy/生产迁移/主规格归档。
- F6C 本批 54/77：Graphic-only 画布可缩放/选择，图层可按服务端边界调整几何、文字样式、图片适配与裁剪、图表/图片 exact revision 替换、形状、顺序/可见/锁定；exact published image Profile 的尺寸 preset 仅在用户确认后改当前画布，旧 text-classified form 明示不可直接冻结。每张画布的真实最终图片可从项目共享素材显式绑定精确 MaterialRevision，按 canonical 画布顺序生成 render_output refs；这不自动产生 render attestation，后续仍需保存后确认当前输入哈希。文字层可在选择 Unicode 范围后绑定/解绑当前冻结 FactPackItem，payload claim 与 exact EvidenceRef 同步；前 12 个可见媒体层通过鉴权 raw 读取并按 SHA256 校验后预览，读取失败不展示假图片。定向前端模型 11/11、全部前端模型 20/20、TypeScript/Vite/FE-P1 PASS（`/projects` 224.75/72.89 kB；Production 285.80/90.75；Graphic/Video 不含 TipTap）。新增服务端负向回归证明 missing/duplicate/wrong-kind/out-of-order/hash-mismatch 的最终图片均被 422 拒绝，原 Master 版本数不增加；F6C 定向后端 38 passed / 1 warning，相关 Ruff、OpenSpec strict 26/26、diff-check PASS。浏览器/包闭环和 provider 验收仍待完成，不将本批视为 F6C 完成。
- F6C Graphic 历史 UI 已接显式 v1→v2 preview/fork 与 schema-aware 画布差异；历史/归档与旧 v1 只读，普通 v2 保存单独处理 409。当前 46/77。最新全后端（加入 Project 能力 fail-closed 后）951 passed / 2 skipped / 5 warnings；前端模型 15/15、TypeScript/Vite/FE-P1 PASS（`/projects` 224.75/72.91 kB，Production 278.38/88.67，Graphic/Video 首包不含 TipTap）；OpenSpec strict 26/26、相关 Ruff、diff-check PASS。浏览器与专业画布深度验收仍待完成。
- Graphic v2 本地模型现在在画布/标题/文字/素材改变时移除旧最终渲染声明和 render_output refs；无变化的文字输入不会错误解绑 evidence。画布复制使用新稳定 canvas/layer ID，复用素材需新 placement，但不复制旧 claim；删除画布同步清理 refs/变体依赖。Graphic Studio 已接项目共享素材 exact revision picker（显示来源、provider、hash、公开/商用权利）和真实能力状态；外部搜索/生成未验证时只显示不可执行。当前 45/77，前端模型 6 项和 TypeScript/Vite/FE-P1 PASS；仍未做浏览器验收，不能将 picker UI 当成权利服务端验收。
- F6C project-scoped Graphic provider 能力现在仅如实返回 `configured/executable/verified=false`，搜索/生图/变体请求为类型化 422，不创建假 MaterialRevision；现有泛用生图会自动赋公开权，不能直接当作经过 F6C 验证的 Project 能力。新 Graphic 编辑路径已改为 `graphic.master.v2` 类型化画布状态/显式保存，历史 v1 只读；画布顺序、文字层、精确媒体插入的本地模型 4 项通过，未用 JSON 框作为正常编辑入口。前端 TypeScript/Vite 与 FE-P1 预算 PASS，Graphic/Video 不含 TipTap。累计 42/77；素材/证据/渲染选择器、完整专业交互、浏览器验收未完成，不能称前端里程碑通过。
- F6C 后端窄闭环已实测：两画布 Graphic v2 → 专业/共用 checks → Candidate v4 → 项目 Review 冻结文字/画布/渲染字节 → 带 warning 精确处置的审批 → 交付授权 → 本地 ZIP；ZIP 两张图的顺序/字节与两个 MaterialRevision 一致，随后撤权再取包被 409 阻止。新增 Graphic Master 和 Candidate 结构化 diff，覆盖稳定 ID 的画布/图层新增、删除、重排、跨画布移动、尺寸、文字以及 refs/render/context；v1↔v2 差异只读且不算假文本相似度。冻结 Candidate hash 篡改的 Review 预览被阻止。累计 36/77，仍缺专业前端、真实浏览器/最终门禁与能力 hook。本批全后端 950 passed / 2 skipped / 5 warnings、OpenSpec strict 26/26、相关 Ruff、diff-check PASS。
- F6C Graphic v2 的精确已发布 image profile 现在支持可选且 fail-closed 的画布数量、尺寸、封面和 inline 图层规则；未声明的限制不凭空发明，旧 text-classified 小红书形态不被悄悄改类。四类专业检查落入现有 ContentMasterCheckRun，profile 版本进入输入哈希；新版本发布后旧平台检查投影为 stale。Fact 旧格式 snapshot 不再抛 500，而是记录 semantic unavailable；文字身份检查即使 provider 已验证，也不能冒充图像视觉身份已验证。相关 F6C 定向 32 passed；全后端本批复跑中。任务 30/77；Candidate→Review→本地包和前端仍未验收。
- 用户一次性开发总包以 `main@ca52aa5`、F6B 131/162 为计划基线；当前真实仓库是本地 `main@670dd49`，F6B 162/162 已提交，tracked clean，仅用户原始规格包/ZIP 未跟踪。F6B change 仍 active，canonical sync/archive 未授权。
- F6C 源包的 71 项为规划数，缺可验证 Scenario；已归位并校准至 `openspec/changes/fe-f6c-graphic-production-studio/`，当前 23/77。补进显式 Graphic v1→v2 fork、画布变体血缘、文字层证据/语义覆盖、画布顺序与包一致性、旧小红书 text-classified form 不暗中改类、provider/renderer 未验证不假成功。标准 change strict 与全库 OpenSpec strict 26/26 PASS，`git diff --check` PASS（已跑门禁，最终需复跑）。
- 已从失败测试开始落地 `graphic.master.v2` 的 canonical document：画布/图层稳定 ID 和顺序、几何边界、文字样式、shape、同文档变体链；v2 API 保存先规范化再哈希，旧无 schema 的 Graphic API 仍按 v1。image/chart layer 需精确 project-visible MaterialRevision 与 canvas/layer placement；wrong-kind、字节/权利不符拒绝。文字层 claim 需精确 evidence locator。当前 F6C 文档/API + F6A adapter 定向 50 PASS；render-input hash、多画布 output 顺序、完整 v1 升级及 UI 尚未完成，不能称 F6C 后端闭环。
- v2 多画布手工 render attestation 现在拒绝颠倒的声明顺序和错误 output slot/placement/sort；正确顺序包投影保留两个 exact image revision。修改文字后旧 render-input hash 无法复用，撤权后既有 render 回读变 incomplete。当前 F6C 文档/API + F6A adapter 定向 51 PASS；完整 v1 升级、Graphic checks/Review/Candidate 闭环及 UI 仍未完成。
- Graphic v1→v2 有独立 preview/commit：只转换可证明字段，旧 render 一律丢弃并要求新 attestation；缺尺寸/背景的旧结构被阻断，不臆造。普通 save 跨 schema 仍 409；升级按 source payload/context CAS、append-only、幂等键保护，旧 v1 不变。F6C/F6A/F6B-v2 定向 83 PASS；Graphic checks/Review/Candidate/UI 尚未闭环。
- 精确位置回归又验证同一 MaterialRevision 可在不同画布保存两份独立 `graphic_layer` refs（不复制素材）；冻结 FactPack 内的 FactPackItem 与文字层 `canvas/layer/range` locator、checksum 不一致会在保存时拒绝。最新全后端在正确环境 939 passed / 2 skipped / 5 warnings；相关 Ruff、OpenSpec strict 26/26、`git diff --check` 均在本批改动后复跑 PASS。F6C 仍只有 23/77，未启动最终浏览器验收。
- 全量初跑 923 passed/12 failed 是环境中 `NO_PROXY/no_proxy` 值导致的 httpx `InvalidURL`，不是业务回归；按既有基线去掉该环境变量后独立复跑 935 passed / 2 skipped / 5 warnings，后续新增场景后仍需重新跑最终全量。未修改测试套件或系统代理设置。
- Fresh 基线：后端全量 913 passed / 2 skipped / 5 warnings；前端 build/FE-P1 PASS（`/projects` 224.75/72.91 kB raw/gzip，Production 269.38/86.71，Graphic/Video 首包无 TipTap）；迁移 head `f6a000000001`，F6C 零新迁移。此为实施前门禁，不冒充后续代码验收。
- 实施计划见 `docs/superpowers/plans/2026-09-29-fe-f6c-graphic-production-studio.md`。本轮下一步先跑 fresh baseline，再从后端 Graphic v2 canonical document/adapter 开始。F6D–F8 尚未开始；总目标保持活动状态，不把 F6C 规划当作 North Star 完成。

## 2026-09-29：FE-F6B FINAL-CLOSE（进行中）

- 最终本地交付记录（162/162）：本次纳入提交的后端文件为 `apps/api/app/routers/content_masters.py`，`apps/api/app/services/{candidates_v4,content_masters,production_modalities,production_packages,production_validation,project_review_projection,text_documents,text_master_ai,text_master_checks,text_master_diff}.py`，`apps/api/app/services/generation/{mock_content,providers}.py`，以及 `apps/api/tests/test_f6a_{draft_mapping,modality_adapters}.py`、`apps/api/tests/test_f6b_{backend_milestone_b,master_checks,master_v2,text_documents}.py`；前端为 `apps/web/scripts/check-bundle.mjs`、`apps/web/src/components/ui.tsx`、`apps/web/src/product/{ContentMasterPanel,ModalityWorkspace,TextStudioModel,TextStudioShell,TextTiptapAdapter}.tsx/.ts` 和 `apps/web/tests/text-*.test.mjs`；另含标准 active OpenSpec change 与根目录 README/task_plan/progress/findings。用户原始规格包目录和 ZIP 保持未跟踪，canonical specs 与 migration 无改动。
- 最终门禁：隔离后端全量 `913 passed / 2 skipped / 5 warnings`（此次新跑）；F6A/F6B 三形态定向 `130 passed`；前端模型 9/9；TypeScript/Vite build PASS；FE-P1 PASS（`/projects` 224.75 kB raw / 72.91 kB gzip，common Production 269.38/86.71，Text lazy closure 596.13/186.92；Graphic/Video 不含 TipTap）；OpenSpec strict 25/25；本次相关 Ruff PASS；`git diff --check` PASS。独立 SPEC/backend/frontend-review-package 均 APPROVE，格式按钮无障碍复核完成。
- 已知限制：真实语义 Provider 未联机验证，不能把 unavailable/partial 写成语义 PASS；2 项 PostgreSQL opt-in 测试未跑（本阶段零迁移）；浏览器验收基于临时 `/tmp` SQLite，保留的是 `progress.md` 的可界定记录；下载事件未返回，但同库 GET ZIP 字节已核对。公众号文章仍因缺 exact cover 被 Registry 阻断，不将 inline 图片冒充封面。全仓 Ruff 另有 23 个既存非本次文件问题。只做本地 main 提交，不 push/deploy/生产迁移；canonical sync/archive 须另行授权。
- 独立复核最终结果：SPEC APPROVE（23.6）、后端 APPROVE（23.7）、前端/无障碍/性能 APPROVE（23.8）。前端复核在格式按钮修复后只读复查了 `TextStudioShell` 和 `Button` 的状态同步、语义与键盘路径，未重审后端；累计 161/162，仅剩 23.9 最终交付记录与本地提交。
- 独立只读复核：SPEC/保留性 APPROVE、backend/Text schema/check/AI provenance APPROVE；前端复核曾指出格式按钮缺少活动态/`aria-pressed`，且错误声明 `toolbar` 键盘语义。已改为普通有标签按钮组，按 TipTap transaction 同步加粗/斜体/代码/链接的视觉与无障碍状态。隔离浏览器验证选中文字后加粗 `aria-pressed` 从 0→1、Tab 到斜体按钮，再恢复；TypeScript/Vite 与 FE-P1 通过（`/projects` 224.75/72.91 kB、Production 269.38/86.71、Text lazy 596.13/186.92）。前端独立复核仍待再次确认；当前 160/162。
- 隔离验收证据：只在临时 SQLite `/tmp/aicontent-f6b-accept-9rZCbY/studio.db` 与本地 API/Vite 运行。Project #1、Text Unit #1/#2/#4、已归档 Text Unit #3、Graphic Unit #5、Video Unit #6；真实 MaterialRevision 图片 #2/图表 #1、FactPack #1/#2。浏览器 #1 v2 修订保存/精确图表和图片引用/段落与 emoji 列表双重 citation/解绑，边界换至 FactPack #2 后旧 Master 明确 stale 并禁止继续绑定；#2 v2 Candidate #1 → Review → Approval → copy_package Target #1 → 本地 ZIP，ZIP 的 `content.md` 与 manifest frozen render 哈希一致，图片字节与 MaterialRevision #2 哈希一致；未宣称远端发布。#3 真实 Draft seed 保留 Run/Attempt 血缘、归档后所有编辑/运行禁用；#4 v1→v2 fork 保留旧版。结构化 diff 实际出现 add/remove/move/modify 及 refs、AI provenance/context 变化。Workflow 草稿和 Master 本地编辑分别显示独立 dirty。Graphic/Video 页面仍是 F6A 最小壳。
- `22.13` 专项：legacy `/workspace/1` Markdown 保存、选区改写、Draft fact-check/文档合成通过；生产/Review 直接 URL 与刷新可恢复；隔离浏览器仅阻断 TextStudioShell 动态模块时出现可重试错误页，解除阻断点击“重新加载”后同页恢复。正常验收标签页 console errors 为 0；故障模拟标签页有预期的动态 import error，不冒充空控制台。
- 定向 F6A/F6B 历史、三形态渲染/冻结/Review/package 共 `130 passed`（2 warnings）；全量后端 `913 passed / 2 skipped / 6 warnings`；前端模型 9/9，TypeScript/Vite/FE-P1 PASS，OpenSpec strict `25/25`，本次相关 Python Ruff PASS，`git diff --check` PASS。零新增 migration。全仓 Ruff 尚有 23 个非本次变更文件的既存问题，因此只声明 relevant Ruff 通过。浏览器验收 22.1–22.13 全部有记录，当前任务 158/162；独立 SPEC/backend/frontend 复核与最终本地提交仍未完成。项目当前账号引用测试夹具曾混入非测试文本，仅临时库，不能作为精确账号映射证据。
- 本批继续完成 legacy `/workspace` Markdown/Draft 保存、selection rewrite、fact-check；真实 Run/Output → Draft seed v2，过期 Output 正确 409、最新成功 Output 可 seed 且显示血缘/未映射警告；v1→v2 显式预览与 fork 不改旧版；AI 五动作 Reject/本地 Accept/显式保存、stale patch 拒绝、固定身份只读均在隔离浏览器验证。Project Fact Boundary 更新到新 FactPack 后，旧 Master 显示 stale_evidence/stale_context 且禁止绑定新证据。结构化差异实际显示 add/remove/move/modify 与素材/证据/引用/AI 血缘/上下文变化。当前 146/162，剩 16 项。
- 新鲜门禁：全量后端 `913 passed / 2 skipped / 6 warnings`；前端 TypeScript/Vite 与 FE-P1 预算 PASS（`/projects` 224.72 kB raw / 72.86 kB gzip，Production 269.34/86.66，Text Studio lazy closure 595.68/186.72，Graphic/Video 不静态含 TipTap）；前端模型 9/9；OpenSpec strict 25/25；`git diff --check` PASS；F6B 涉及 Python 文件定向 Ruff PASS。全仓 Ruff 发现 23 个非本次变更文件的既存问题，不冒称全仓 PASS。migration 目录无改动。
- 浏览器 22.1/22.2/22.4/22.11 已实测：新 Text v2 区块/顺序保存回读；图片、图表精确引用及移除；stale/current/coverage；百家号 article（无封面必需项）手工 Master #11 → checks → Candidate v4 #1 → Review 预览/变更/冻结检查 → 两条 warning 人工处置 → Approval → copy_package 授权 → 本地 ZIP。浏览器下载事件未返回，但页面确认已生成，使用同一隔离后端的 GET package.zip 取回并检查 4 文件，`content.md` 与图片 SHA256 分别等于 manifest render hash 和 MaterialRevision hash。页面没有将本地包误标为已发布。累计 138/162；22.3 等剩余项不提前勾选。
- 跨层三项 5.6/6.1/6.3 已以隔离浏览器 + API 回读 + 定向测试闭合，累计 134/162。Text Studio 从 stale Master 显式接纳 Brief/Boundary 后保存 v5；图片/图表插入后保存 v6；段落 citation + exact EvidenceRef 保存 v7；带 emoji 的列表中重复引用同一 FactPackItem 保存 v8；解除列表引用并移除图表保存 v9。v8 API 回读两条 citation/locator、两条 exact MaterialRevision 和对应 EvidenceRef；v9 回读仅剩图片与段落引用，原系统素材/FactPack 未删除。AI edit provenance 此前已通过浏览器保存回读及后端 receipt/hash-chain 回归；本次定向后端 146 passed、前端模型 7 passed。此处仅关闭跨层任务，不把局部通过写成完整 22.x 浏览器验收。
- 当前 OpenSpec apply 状态经命令重读：`spec-driven`，131/162，剩 31 项；本地 `main@ca52aa5` 和已有未提交 F6B 改动保留。本轮只做隔离夹具、跨层验收、legacy/三形态回归及最终门禁，未确认的任务不预勾。
- 目标门禁为 Text Master v2 的 exact asset/evidence、AI/upgrade/seed/diff、Candidate→Review→Approval→ZIP，以及 legacy、Graphic/Video、性能与迁移零变更。最终验收记录待实际运行后补充。

## 2026-09-29：FE-F6B Professional Text Studio 前端（15–20 完成；131/162）

- 从已核后端 A/B PASS、93/162 继续；本批完成 15–20 共 38 项，累计 131/162。5.6/6.1/6.3 尚待真实 refs/seed 原子性证明；21–23 尚待完整回归/浏览器/最终门禁；未归档。
- 已建立 Text v2 typed draft / Studio Document ↔ TipTap 临时格式适配；旧 v1 只读，普通保存仍禁止隐式升级。Graphic/Video 继续使用 F6A 原 JSON 壳，Workflow 保存状态独立。
- Text 块编辑支持稳定 ID、区块顺序、基础格式；不支持的 TipTap 结构显式阻止保存。项目共享图片/图表与 FactPack 证据从真实 API 读取，本地按精确 revision/checksum 同步更新 document+refs；失效 citation 显式提示，保存后端仍复核。
- 定向 Node 模型/适配器回归 9/9；最新 TypeScript/Vite 与 FE-P1 门禁通过。`/projects` 首包 224.72 kB raw / 72.86 kB gzip，common Production 269.34 / 86.66，Text Studio lazy closure 595.68 / 186.72；Graphic/Video 静态闭包不含 TipTap。`/assets`、`/settings`、`/learning` 预算通过；打包清单动态别名有唯一入口检查。
- 完成 AI 五操作建议/本地 Accept/Reject、固定身份只读、覆盖诚实的专业检查、显式 v1 升级、结构化版本 diff、Draft seed 血缘展示。隔离 SQLite 浏览器已实测项目/身份/文字单元创建，v2 区块保存/回读，AI 改写建议→本地接受→显式修订保存与回读 AI 血缘，修订 diff、专业检查、双窗口 409、历史只读与刷新持久化。发现并修复编辑器初始化导致的假 dirty；409 保留本地编辑并给出明确重载提示。素材/证据、全形态与 Candidate/Review/package 浏览器闭环尚未验收，22.x 不提前勾。
- 本批全量后端实跑 913 passed / 2 skipped / 6 warnings；OpenSpec strict 25/25 与 diff-check 均通过。无 migration、无 commit/push/deploy/生产迁移/canonical sync/archive；F6C/F6D 未启动。

## 2026-09-29：FE-F6B Backend Milestone B（93/162，阶段完成）

- 基线 `main@ca52aa5`，在既有未提交 F6B 工作区继续；只执行任务 11–14，不动前端、DB migration、F6C/F6D，也未 commit/push/deploy 或同步归档主规格。
- AI suggestion 五种操作经项目/单元、当前 v2 Master 与 context 校验，仅返回服务端验证/内存应用的 patch；模型输出不能指定越界目标或自报可信 provenance。LLMRun 保存实际 provider/model、受限输出及服务端 receipt；引用证据只取允许模型使用的精确快照。改写覆盖引用时在建议响应中列出失效 citation 并移除对应本地 evidence ref；改写前方正文时对未受影响的后续 citation 与 evidence locator 做确定性重定位。建议本身不改 Master。
- 保存时拒绝客户端自造 `ai_provenance`，核验 receipt 所属人/项目/单元/父 Master、payload/context/input/selection/patch、状态与连续 document hash；重复、失败、外来、清除或断链收据不可信。只有提交文档确与最终输出相同才标 `verified_output_match`，后续手改标 `subsequently_modified`，不冒充浏览器点击证明。
- Structured Master diff 忽略每次追加版本产生的引用行 ID，仅比较真实素材/证据语义；v1→v2 历史 diff 只读。Candidate v4 冻结 document citations 与 EvidenceRef locator/checksum；Review 对 v2 冻结清单/hash/render 做完整性校验，v1↔v2 不伪造结构化差异。本地 ZIP 的 `content.md` 与冻结 render 字节一致，单条 AI→保存→检查→冻结→审批→授权→ZIP 无 Draft 闭环已通过。
- OpenSpec 11–14 共 27 项逐项复核后完成；累计 93/162，剩 69 项。定向回归 `21 passed`；全量后端 `913 passed / 2 skipped / 6 warnings`（37.79s）；OpenSpec strict `25/25`、Ruff、`git diff --check` PASS。前端未改，未执行本阶段前端 build/browser 验收，不把旧结果冒充当前门禁。

## 2026-09-29：FE-F6B Backend Milestone A（66/162，阶段完成）

- 从已核 51/162 继续，仅处理任务 9/10；现有 main 的 F6B 未提交改动保留。不启动 AI/前端/迁移/发布。
- 已加入 v2 每类检查 requirement/hash 解析，并连接执行、当前投影、Candidate v4 与历史包；v1 仍使用原哈希。结构/事实/身份/渠道/精确 published discoverability 处理器均已落库，仅 `ContentMasterCheckRun`；未配置/失败/禁用或截断的语义覆盖显式标记，不能假称全量通过。
- 新增 13 项定向回归：精确 profile、per-kind stale、模型使用撤权、无假语义验证、空白身份不可假称全量核验、v2 Freeze/人工 Approval、历史包新 profile 不追溯、同输入新 blocker、未知规则/SEO、Fact locator、固定 IdentitySnapshot、provider 失败/截断/无效响应、无 DraftClaim/Report 副作用。F6A/F6B 相关先前 113 项通过；旧测试所要求“v2 warning 不可冻结”与批准契约冲突，已改为“可冻结但 Approval 必须准确处置”。
- 首次全量无代理环境未配置，12 项旧 Settings/Plugin 网络状态测试因本机无效代理端口 `:1` 失败；使用本项目已记录的 `NO_PROXY='*' no_proxy='*'` 后最终全量 892 passed / 2 skipped / 6 warnings（34.47s）。最后一次实跑覆盖空白身份边界与全部代码改动，后续仅改动任务/README/进度文本。
- OpenSpec 任务9.1–9.6、10.1–10.9均已完成，累计66/162，剩96。Backend A=PASS；B（AI/receipt/diff/v2 Review/package）及 F6B 前端仍未开始。本批不改 migration、不 push/deploy/生产迁移、不归档未完成 change。Ruff/OpenSpec/diff 的最终状态见本节后续门禁记录。
- 最终轻门禁：OpenSpec strict 25/25 PASS；本批触及 Python 文件 Ruff PASS；`git diff --check` PASS。前端未改、未将旧 build 结果冒充本批验收。没有可用的只读 code-review 子 Agent 授权（用户指定单 Agent 负责本项目），本批做了主 Agent 逐文件自审，不标记独立复核。

## 2026-09-29：FE-F6B 后端第二批（51/162，转换/升级/seed）

- 用户确认39/162基线，要求后端优先：ONE converter → 显式升级 → Draft seed → 专业 checks → AI/receipt/diff/v4；只在A/B门禁通过后做前端。直接本地main@ca52aa5，前批未提交改动完整保留。
- 使用 using-superpowers、openspec-apply-change、writing-plans/executing-plans、TDD、systematic-debugging、requesting/receiving-code-review、verification-before-completion；仅主Agent写代码，两个独立Agent只读检查。图谱工具不可用，限定相关文件读取。
- 完成任务7.1–7.6、8.1–8.6共12项，累计51/162，剩111。convert_legacy_text是升级与seed唯一转换核心；逐入口真实API验证同canonical payload/document hash/locator，旧document与正文矛盾不覆盖正文。
- GET text-v2-upgrade-preview不落库，POST text-v2-upgrade追加子版本；expected revision/payload/context+latest v1+非stale+ownership/archive+原save原子边界均保留。source/request provenance仅可信服务创建；committed retry先回放，后续Brief变动或源码变化不触发重复转换；不同intent复用key409。
- 新from-output创建v2，冻结definition/identity/channel/Run/Step/最新成功Attempt/最新Draft门禁未削弱。媒体只用项目已授权精确revision/hash；证据只有已证明pack/item/checksum和唯一选文才生成citation，无法定位保留warning/unmapped/incomplete。新seed不能跨过当前v1的explicit upgrade gate。
- 历史v1保存/读取/已有seed幂等回放/Candidate v4冻结保持原样，旧Master/Draft未回填。历史v1 fixture明确构建原契约，而不是把专业v2检查伪装成pass。
- TDD先RED：10个converter缺失、7个upgrade API/来源边界、v2seed映射/一致性，及复核发现的复杂强调、code-span空白、stale-parent、重叠选文、Unicode分隔符、缩进等价、Setext/plus-list、嵌套link label均先复现再修正。无法可靠转换的有界语法保留字面内容+显式警告，不声称完整Markdown parser。
- 最终实际门禁：135项converter/upgrade/seed定向PASS；全后端879 passed/2个未配置PG的opt-in测试skip/6既有warnings（41.69s）；相关Ruff PASS；OpenSpec全量strict25/25 PASS；tracked及三份新增代码/测试whitespace检查无错误。初轮854/中间875是修正前结果，不作最终验收。
- SPEC/task只读复核APPROVE（Confucius，仅7/8共12任务）；backend终轮APPROVE（Euler，独立实跑135定向）；所有复核发现已复现并修正，包括末轮4301位数字列表标记的受控处理。两份review均只覆盖converter/upgrade/seed，不冒充整套F6B独立验收。未记录全量测试stdout到connector索引，可见证据为当前实际终端输出及本记录。
- Backend Milestone A = PARTIAL：upgrade+Draft seed通过，专业checks未做；Backend Milestone B = NOT_STARTED。不存在本批已知未处理阻挡转换/升级/seed的问题；任务9/10的profile/currentness/semantic/model-use仍待实施，专业handlers继续incomplete。
- 本批六个代码/测试文件：apps/api/app/services/text_documents.py、services/content_masters.py、routers/content_masters.py、tests/test_f6b_text_documents.py、tests/test_f6b_master_v2.py、tests/test_f6a_draft_mapping.py；同步根README/task_plan/progress/findings和标准tasks。此前F6B adapter/Candidate/package schema分派改动保留，未修改用户原始包/ZIP或canonical。
- 前端本批未修改/未重新build，不将旧build/budget冒充本阶段验收。零新表/零migration/零依赖；未commit/push/deploy/生产迁移/canonical sync/archive，仍main@ca52aa5+未提交F6B改动；F6C/F6D未启动。

## 2026-09-29：FE-F6B 第一批（39/162，后端基础）

- 用户明确“进入 F6B apply”；标准 change fe-f6b-text-production-studio（spec-driven，0/162）进入实施，不再重复询问已确认的产品范围。
- 实核本地 main@ca52aa5；tracked 改动仅上轮审计 README/task_plan/progress/findings，标准包及用户源包/ZIP 未跟踪。全部保留，业务代码初始无差异。
- 使用 Superpowers / OpenSpec Apply / writing-plans / executing-plans / TDD / verification-before-completion；主 Agent 在 main 实施，独立 Agent 只读评审。图谱工具不可用，沿用定点代码读取。
- 先补后端契约，再接前端；0新表/0迁移约束仍在。禁止 push/deploy/生产 migration/canonical sync/archive/F6C/F6D。
- Fresh 基线：初始化独立临时测试库后 backend751 passed/2个未配置PostgreSQL测试skip/6既有warnings；初次纯内存库的Celery独立session无表已用正确测试环境复跑，不改业务。TypeScript/Vite/FE-P1 PASS，projects224.68/72.86kB，Production254.44/82.27；strict25/25、相关Ruff/diff PASS。
- TDD第一段：新增44个纯文档契约先全部因service缺失失败，实现text_documents后44通过；覆盖十类blocks、mark/canonical/hash、UTF-8/codepoint/list/citation、单真源、精确ref对应、safe renderer/media mapping。尚未接Master API/checks，不能据此宣称v2闭环。
- 当前已完成39/162：0、1、2、3、4全部，5.1–5.5、6.2/6.4–6.6。已接真实v2保存/读回/append-only/CAS/幂等，旧Markdown及旧文档请求保持v1；所有持久化读取/验证/投影按精确schema分派。
- 素材验证project-visible/hash/type，图片与图表插入/移除不复制或删除资源；未使用的声明明确报告。Citation与EvidenceRef逐use对应codepoint/list-item/text hash/FactPack snapshot，范围仍在但选中文本改变必须拒绝；Boundary改变阻断继续使用旧ref，历史不改。
- 新增84项定向测试通过，包含真实API持久化、同item多citation、emoji/list、权限/归档、旧版本兼容、冲突无部分Master/ref/event、renderer/ZIP media路径和撤权。旧两项adapter测试显式指定v1，继续验证旧契约，而不是对新默认v2套用v1的固定检查集。
- 只读复核发现并先RED后修复：实体转义、强调首尾空白、inline-code换行/纯空白、严格locator整数、citation与括号误拼链接、同revision image/chart冲突；不忽略这些冻结正文细节。
- 专业text checks目前只有schema注册，未实现handler明确incomplete，假AI receipt拒绝。显式upgrade、Draft seed v2、专业checks/profile freshness、AI/receipt、diff、Review v2、前端与浏览器仍未实现；不把adapter/package projection测试冒充Candidate→Approval→ZIP闭环。
- 本批前端无改动；本轮开头fresh build/budget通过只是基线，不是新Text Studio验收。未新建表/migration、未push/deploy/生产迁移/canonical sync/archive；HEAD尚未产生F6B提交，仍ca52aa5。
- 最终本批fresh门禁：全后端835 passed /2个未配置PostgreSQL测试skip /6既有warnings（42.32s）；84项F6B定向（1.75s）；相关Ruff PASS；OpenSpec all strict25/25 PASS；tracked diff与本批新增代码/文档whitespace PASS。不是F6B最终验收，23.x仍未勾选。
- 本批后端只读复核APPROVE（Euler）；仅限schema/document/render/save/ref基础，不代表完整F6B。三份MODIFIED delta的16个旧Scenario本轮逐块保留审计PASS；canonical/models/migration差异为空。
- 阶段勾选审计（Confucius）：已读范围未发现过勾，schema/document/renderer/save/refs与测试对应；未独立读取门禁stdout或核对真实并行竞争，不冒充完整F6B独立验收。实际CAS/幂等/上下文漂移回归通过，全阶段仍39/162。

## 2026-09-29：FE-F6B SPEC_READY（等待单独 apply 授权）

- 实核 main@ca52aa5；原始包和 ZIP 为用户未跟踪文件，tracked clean；F6A 已 canonical + archive。
- 完整读取原稿 162 项实施任务和四份 delta；仅审计/校准/标准目录归位，apply 未授权。
- 三份 MODIFIED 缺少原条款旧场景，归位时必须补齐；不能以 strict 语法通过替代保留审计。
- 标准包已归位 openspec/changes/fe-f6b-text-production-studio；原始八文件与源读取基线逐文件一致，三份 canonical 未改。162 项实施任务全部未勾选。
- 校准完成：七个 MODIFIED 块保留十六旧场景；Markdown 权威转换/显式 schema upgrade；Unicode/list-item/selected-text hash/编辑失效；AI output-match 紧凑回执与 retention；warning 只在 Approval 处置；exact discoverability、nested citations→manifest、冻结媒体路径、Text/legacy 各自 lazy。
- 三独立只读复核最终全部 APPROVE：SPEC/plan、backend、frontend/Review/package。只批准规格，不是 apply 授权或实现验收。
- 本轮实跑全量 strict25/25、旧条款保留审计、tracked diff-check及新增九文件 whitespace check 均 PASS，apps 差异为空。未运行后端测试/前端构建/浏览器，不借用 F6A 结果宣称 F6B 验收。
- 使用 using-superpowers、openspec-explore、writing-plans、requesting-code-review、receiving-code-review、verification-before-completion；更新根 README/计划/进度/发现和包内 review.md。没有 commit/push/deploy/migration/canonical sync/archive，HEAD 仍 ca52aa5。

## 2026-09-29：FE-F6A 五份主规格已同步并归档

- 用户已明确授权五份canonical同步、F6A归档、strict/diff-check及本地main提交；不改业务代码，不启动F6B。
- 实核main d060428、工作区干净、4/4产物和214/214任务；仅新增production-content-master，并更新F2/F3A/F3B/F4，不覆盖原始包或其他canonical。
- 本轮使用using-superpowers、OpenSpec archive、writing-plans/executing-plans及verification-before-completion；计划按根task_plan维护，不新增无关方案或测试。
- 已完成：production-content-master新增19要求，F2/F3A/F3B/F4准确更新10要求块；四份主规格的40旧要求/149旧场景完整保留，未修改的要求块逐块一致。新Purpose已正式化，无TBD机械占位。
- 标准归档：openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/；9文件（含.openspec.yaml）SHA256与归档前相同，原始包9文件也相同；active中不再有F6A。CLI UTC目录名09-28已仅校正为本地Asia/Taipei日期09-29。
- 实际归档后全量OpenSpec strict24/24通过、git diff --check通过，apps业务代码差异为空。CLI有“超过10个delta建议拆分”的非阻塞提示，不改变已验收范围。
- 仅规格/文档本地main提交，最终hash以git log -1为准；本轮不重跑后端/浏览器，也不将昨日753测试当新运行结果。F6A状态ARCHIVED；不push/deploy/生产迁移、不启动F6B。

### FE-F6A 最终验收完成（214/214，仅本地main收尾）

- 用户本轮明确限定：只完成F6A收尾；F6B及以后禁止启动，必须先出具体方案再确认。canonical同步/归档仍按21.9另待授权；不push/deploy/生产迁移。
- 最终新临时SQLite全量实际输出753 passed / 6既有warnings / 32.06s，包含206项F6A；实际PG约束和撤权行锁2项执行通过，未skip。相关Ruff通过；SQLite及真实隔离PostgreSQL16 fresh head→f5c→head往返通过。
- 最终TypeScript/Vite及FE-P1通过：projects224.68kB raw/72.86gzip，Production254.44/82.27；既有Assets/Settings/Learning预算保持，轻路由无TipTap/XYFlow。最终OpenSpec全量strict24/24与diff检查通过。
- 完整浏览器20.1–20.14实跑通过：三形态保存/刷新、409保留编辑、Brief stale、checks/真实render/v4 freeze、Preview/Changes/Checks、Approval/授权/下载ZIP、真实Draft seed、旧v3、节点rerun/from-here/Human和dirty隔离；额外归档只读回归先RED后GREEN。
- 最终浏览器证据：/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6a-browser-evidence-KFiSr7/report.json；13 gates、consoleErrors=[]。AI provider显式mock，执行/Attempt是实际持久化；媒体是真实编码文件与明确manual attestation，不冒充真实AI/自动renderer/远端发布。
- 三项只读独立review均最终APPROVE：SPEC（旧MODIFIED要求/场景保留）、backend（live locks/embedded refs/bounds/latest warning）、frontend-review-package（form CAS/v3正文/stale历史/归档控件）。所有发现已修正并回归，主Agent独自写代码。
- 任务逐项验收映射、当前目录结构和长期不变量记录在docs/FE_F6A_FINAL_ACCEPTANCE.md；原始包和canonical未改。本轮只提交F6A白名单，最终hash以git log -1为准，规格状态ARCHIVE_READY；不得把本地验收说成生产验收。

### FE-F6A FINAL-CLOSE 实施增量（main@703d6c5）

- 完整后端初轮实跑745 passed/6既有警告（含实际PG测试），独立前端发现3项并先复现5失败后修复：合法form变更保留上游CAS、旧v3各modality正文schema分派、stale检查禁止执行且历史包按准确冻结input选latest。三形态真实浏览器save/reload/409/stale/check/freeze/Review/Approval/ZIP已通过；真实Draft seed/legacy v3/debugger正在补齐。最终全量仍待修复后重跑。
- 最新前端TypeScript/Vite与扩展Production预算检查通过：projects224.68kB/72.86gzip，Production254.46kB/82.28gzip；三最小壳独立lazy且无TipTap/XYFlow。归档单元/项目的Workflow设计、保存、执行也禁用，Master独立只读。
- 新增 verified Master Workflow Output、两会话 Freeze 幂等/历史保留、Review 三形态冻结预览与结构化 diff、Master Versions/Overview风险（Unknown优先）。相关定向37项及输出9项通过。
- 隔离本地 PostgreSQL16容器 `aicontent-f6a-postgres-acceptance`（127.0.0.1:15462/f6a_acceptance）实际 Alembic up/down/up 通过；真实唯一/FK/非破坏downgrade和两会话撤权行锁2项通过。不是生产数据库。
- 独立SPEC review APPROVE。独立后端首轮发现撤权窗口/嵌入引用/标题存储bounds/warning处置四项：已添加行锁、精确引用与路径校验、500字符标题上限、准确check-id+input-hash的审批warning处置。针对warning+原v4交付45项通过，Master/adapter/seed102项通过；还需独立复核。
- ProductionDesigner已拆分为controller + Workspace/Header/Canvas/Inspector/AssetDrawer/MasterPanel及三lazy最小壳；Review冻结渲染经项目权限/权利/字节校验后预览。TypeScript/Vite和既有route预算初跑通过；最终全量/浏览器/独立frontend仍未完成。
- 当前不勾214/214、不归档/同步、不push/deploy/生产迁移。临时PG仍运行供最终门禁；完成后仅停止本任务容器。

## 2026-09-28：FE-F6A FINAL-CLOSE

- 实核本地main703d6c5、tree clean，OpenSpec114/214；用户授权完成剩余100项并实际浏览器/独立评审验收。不进入F6B，不push/deploy/生产迁移，归档仍须另行授权。
- Skills：using-superpowers、OpenSpec apply、receiving-code-review、writing-plans/executing-plans、TDD、verification-before-completion；复用已批准设计，无新proposal或专业编辑器。新增独立评审工具现可用，仅用于只读评审，主Agent仍独自实施代码；graph MCP未提供，限定相关文件回退读取。
- 先完成project_outputs、Freeze历史/竞态、检查和迁移残余；再Review/Versions/Overview，然后Production最小壳和隔离浏览器。新门禁未执行前不引用上轮712通过作为本轮结果。

## 2026-09-28：FE-F6A v4 Approval/Authorization/Package窄闭环

- 基线main6ebc9e5、92/214，跟踪文件干净。按用户授权继续已有change，前端不动；采用OpenSpec apply、评审反馈、writing-plans/executing-plans、TDD和verification-before-completion。
- 实际确认审批draft=None阻断、项目package只接受schema3；抽共享v4 live validator，明确新审批/授权要求current Master，已有授权历史package不retarget，但持续检验冻结来源/check/render/rights。图MCP未提供，仅限定相关文件回退读取；未用无关记忆结果作为项目证据。
- TDD先复现12失败/4通过，再统一接Freeze/Approval/Authorization/Package：schema分派有Master-FK防降级；准确Candidate/Master/context/provenance与冻结check行和最新pass均验证。审批和授权在flush后刷新复核，提交前撤权时Review/Target/Event回滚。
- 无Draft/Topic/Mother/Run的Text完整走通checks→freeze v4→approve→copy/manual authorize→ZIP，检查manifest、content.md、精确媒体和guide；Master、Candidate/hash不变，Review/Target绑定准确hash，不创建DeliveryAttempt。已有Media Adapter仅输出明确manual确认的精确render，不新增能力。
- 新增44项闭环回归通过，含rights/evidence/bytes/tamper三阶段拦截、重算hash后的Master/identity/render/check/schema伪造、最新failed检查、raw asset授权旁路、提交前回滚、幂等、退改、新Master/Brief后旧target冻结历史、重跑checks不改Candidate及两种media输出；既有Freeze回归也在最终全量覆盖。
- 按requesting-code-review检查清单做单Agent复核，当前无subagent工具，不标独立APPROVE。最终实跑712 passed/6既有警告（29.22秒，165项F6A回归），新临时SQLite迁移到f6a000000001；strict24/24、触及文件Ruff、diff-check全部通过。前端未改未复跑，开发/生产库未动，不引用旧build作为本轮验收。
- OpenSpec仅新增22项已验收勾选，当前114/214。PRODUCTION CORE BACKEND MILESTONE（无Draft的Text→local ZIP）通过；并发冻结完整验收、Review v4 preview/diff、Versions/Overview、Production Workspace及浏览器验收仍未完成。原始包/canonical未动，change不归档；仅本地main阶段提交，不push/deploy/生产迁移。
- 实际skills：using-superpowers、openspec-apply-change、receiving-code-review、writing-plans、executing-plans、test-driven-development、systematic-debugging、requesting-code-review（单Agent回退）、verification-before-completion。

## 2026-09-28：FE-F6A Adapter及v4后端继续实施

- 已核main4b5c7c9，52/214；继续已批准fe-f6a-production-core-content-master（spec-driven）。用户要求保持Adapter→Draft映射→纯builder→Freeze/Approval/package顺序，前端不启动。
- 使用using-superpowers、OpenSpec apply、receiving-code-review、writing-plans/executing-plans、TDD、verification-before-completion。图MCP仍未提供，限定相关文件回退读取；原始规格包、canonical和生产库不动。
- 已完成Adapter三形态契约与readiness：人工render需明确追加保存确认，由服务端绑定actor/精确input hash/output；全canvas覆盖，字节/MIME/实时权利、非render资产与证据输入变化均回归。Channel Registry只接受真实注册的video能力，不增加或推断新渠道。
- Draft seed校验冻结Workflow version/checksum与最新成功Attempt；真实document/markdown/structured与内容hash冻结，精确素材/证据映射，source pack无法证明或素材不可见时明确unmapped并使检查incomplete。相同seed动作重试回放已冻结内容，不读取后来变化的Draft替代它。
- 已独立实现candidates_v4：load frozen inputs与纯build_manifest_v4分离，实际Identity/Brief/Boundary/FactPack checksum、Master哈希、refs/checks/render、workflow/edit provenance及citations/declarations均冻结；JSON深拷贝和key-order/hash覆盖回归通过。
- v4 Freeze已替换临时骨架：强制expected_payload_hash；latest/current context/current checks/live refs/真实render闸门；提交前刷新复核hash，漂移时Candidate/Event一起回滚。手工Text无Draft/Topic/Mother/Run可冻结；Graphic/Video只有明确manual确认可冻结。重复调用一Candidate/一事件，跨owner/归档拒绝。
- 本轮任务实核92/214；Approval仍Draft-only、copy package仍schema-v3入口，下一轮必须独立v3/v4 dispatch。完整无Draft的Approval→local package里程碑尚未通过；不勾选并发冻结/审批/交付或前端任务。
- 阶段复核使用requesting-code-review检查清单，但当前没有subagent工具，实际是单Agent逐项代码/门禁复核，不标为独立APPROVE。复核新增exact evidence checksum更换后重跑不得pass的回归；Ruff和OpenSpec all strict24/24、diff-check已实际通过。
- 最终全量实跑668 passed/6既有警告（26.25秒，包含展示标题入hash后的最终代码），新增63项（Adapter28、seed7、manifest16、Freeze12），连同58项旧Master回归共121项。使用新迁移临时SQLite，不涉及开发/生产库；strict24/24、Ruff和diff-check均通过。前端未改未复跑，不引用旧build作为本轮验收。
- 实际skills：using-superpowers、openspec-apply-change、receiving-code-review、writing-plans、executing-plans、test-driven-development、systematic-debugging、requesting-code-review（单Agent回退）、verification-before-completion。仅本地main阶段提交，不push/deploy/生产迁移/canonical同步/归档。

## 2026-09-28：FE-F6A 后端不可变量继续实施

- 基线main eb1156c，已完成44/214。按用户复核的后端顺序推进，先不改前端；当前读取确认跨Unit生成素材被错误限制，Channel/content_form尚未校验，CAS尚缺共享锁。
- 使用OpenSpec apply、receiving-code-review、writing-plans/executing-plans、TDD及verification-before-completion；图MCP未提供，回退限定文件读取。门禁结果待本轮实际执行。
- 本轮先RED再GREEN封严：共享项目事务锁覆盖Master和Project/Unit/Brief/Boundary写入；提交前刷新上下文，expected_context_hash冲突409；旧fingerprint继续可重放。SQLite双连接测试验证同键一版本/一事件、不同键同head一成功一409，锁竞争及提交时Unit/Brief/Boundary漂移均回滚。
- ProjectWorkflowOutput按project而非消费unit校验，核验成功历史Attempt、插件/Run/checksum及实际字节；外项目、裸全局ID、失败Attempt和被替换字节均拒绝。Evidence检查覆盖整个边界（含未显式引用项）；rights检查回读hash/public/status/父素材归档；live变化使旧检查stale。Candidate-only历史纳入Archive保护。
- 定向58项（新增31项），任务仅勾选已闭合8项，当前52/214；完整Adapter、Draft映射/警告、v4 builder/Freeze/Approval/package仍未完成，不能宣称里程碑已通过。没有前端改动或canonical归档。
- 最终实跑：迁移后的新临时SQLite，全量605 passed/6既有警告（22.44秒，含58项Master回归）；触及文件Ruff通过；仓库根目录OpenSpec all strict24/24、git diff --check通过。前端未改，本轮未复跑build/budget，不用上轮build冒充本轮结果；PostgreSQL实库并发及完整v4端到端仍未验收。仅本地main阶段提交，不push/deploy/生产迁移。

## 2026-09-28：FE-F6A 阶段代码本地main整合（已完成，F6A仍在开发）

- 用户授权当前阶段代码整合到main，后续直接在主工作区main开发。仍按已确认OpenSpec实施，不另开隔离开发分支；发布、生产写入、canonical同步归档不随此授权自动开放。
- 当前基线main661e30a，F6A44/214；本次不是完成F6A，只整合已实现/已回归的阶段代码及标准change、计划和文档。
- 本轮使用using-superpowers、finishing-a-development-branch（阶段整合）、writing-plans（维护计划）、verification-before-completion。
- 分支阶段提交`7c2be75`已白名单提交并快进合入main，合入前后均574 passed/6既有警告；main全量22.73秒，前端build/FE-P1预算通过（projects224.68kB raw/72.86kB gzip），strict24/24、Ruff/diff-check通过。主规格未同步，active change仍44/214。
- main原有重叠文档/标准change可恢复备份保留于stash `cbee2d1e66dfdd083814e1acdf5fce22a690782d`；核对后无main独有内容遗漏，不把旧stash重新覆盖新进度。原始包/ZIP仍未跟踪且未改动。保留原隔离分支作为阶段快照，后续实际开发路径为主工作区main。

## 2026-09-28：FE-F6A apply（隔离工作树，进行中）

- 用户提供ChatGPT连接器实际读取证据：AIContentStudio main@661e30a、两份FE-F5C主规格和f5c000000001迁移均成功；业务代码前硬门槛解除。该证据来自用户转述的连接器读取，不冒充本地工具直连。
- 复用干净的托管工作树，从main@661e30a新建codex/fe-f6a-production-core-content-master；校准后的标准change及本轮计划/记录机械复制到隔离工作树，原始规格包和main未跟踪资料未改动。
- 本轮进入持久化/服务实施。禁止push、merge、deploy、生产迁移；canonical同步与归档另待授权。
- 隔离工作树复跑：临时SQLite迁移到f5c000000001，547后端测试通过、6既有警告；首次因本机继承的畸形NO_PROXY导致12项环境错误，限定NO_PROXY后全绿。前端TypeScript/Vite/FE-P1预算通过（/projects 224.68 kB raw、72.86 kB gzip）；OpenSpec all strict 24/24、diff-check通过。Ruff基线在既有content_projects.py和project_review.py有两处import排序告警，非F6A引入，后续只对改动文件门禁并整理触及的import。
- 本轮重新核对任务和实际代码，撤销未验收的过早勾选：当前44/214。已实现持久化基础、有界详情读取、请求幂等重试、父版本检查、不完整/stale投影、检查追加历史/最新结果/输入时效、Draft当前成功Attempt血缘验证；不把唯一约束等同完整事务锁，也不把v4入口等同完整候选链路。
- TDD：先复现回退删除历史、归档写检查、假schema/假来源、上下文漂移重试、空文稿/结构深度、缺失详情/父版本、冻结输入500、检查缓存旧pass及失效Attempt seed，再按失败证据修复。当前定向27 passed（2既有依赖警告）。此前40项/12项记录不作为当前完成证明。
- 尚未完成：共享事务锁/上下文CAS、完整嵌入引用和生成素材血缘、权利与renderer/attestation、完整v4冻结/审批/交付、读模型、前端与浏览器验收；PostgreSQL实库未验收。canonical、main及原始包未改动。
- 本轮实际skills：using-superpowers、openspec-apply-change、executing-plans、writing-plans（校正计划/记录）、test-driven-development、verification-before-completion。
- 本轮新鲜门禁：临时SQLite upgrade→downgrade f5c000000001→upgrade成功；全量574 passed/6既有警告（21.22秒），包含27项F6A定向测试。前端TypeScript/Vite/build与FE-P1预算通过，/projects 224.68kB raw/72.86kB gzip；OpenSpec all strict24/24、触及文件Ruff、diff-check通过。前端本轮无功能改动，该build不代表F6A前端验收。

## 2026-09-28：FE-F6A apply 前置核验（授权，等待连接器证据）

- 用户明确授权进入apply；上一回合启动后被中断，未执行代码命令。本回合重新核对本地main `661e30a`、F5C archived、两份canonical与只读Alembic code head `f5c000000001`，OpenSpec 4/4产物齐备、214项实施任务未开始。
- F6A规格把ChatGPT连接器实际读取post-F5C main/主规格/迁移列为业务代码前硬门槛；本地git/bridge状态不能替代该证据。当前工具未提供合规的连接器端workspace_info调用，已请求用户在现有ChatGPT对话中实际读取并反馈。未创建工作树或修改业务代码。
- 在隔离临时SQLite `/tmp/aicontent-f6a-baseline-zkSC1c/studio.db` 上启动本地基线回归；不会运行生产迁移。OpenSpec all strict24/24和diff-check已通过，后端/前端结果待回收。
- 基线结果已回收：隔离SQLite迁移到f5c000000001；后端547 passed、6既有警告（22.23秒）；TypeScript/Vite/build与FE-P1 bundle预算通过，/projects 224.68kB raw/72.86kB gzip，Assets257.70kB、Settings229.76kB initial；strict24/24和diff-check通过。
- C2C本地status仅表明桥接进程在运行，近期bridge日志不包含post-F5C的ChatGPT侧workspace_info读取证据。当前缺少合规的ChatGPT端读取结果，因此按F6A硬前置停在业务代码前；无测试代码/业务代码、无工作树切换。
- 本轮实际skills：using-superpowers、openspec-apply-change、executing-plans、using-git-worktrees、test-driven-development、verification-before-completion；codex-with-chatgpt已检查但当前未通过其页面发送消息。

## 2026-09-28：FE-F6A 规格审计与归位（SPEC REVIEW通过，未apply）

- 用户确认本轮仅审计、调整和标准归位；apply仍需用户确认，不由代理自行授权。
- main实际为661e30a，FE-F5C五份canonical及归档已可在本地读取。外部ChatGPT connector是否已看到新提交尚未证实，不以本地读取冒充connector验证。
- 本轮skills：using-superpowers、writing-plans、openspec-propose、verification-before-completion。代码图MCP工具未提供，代码发现仅在相关服务范围内回退搜索。
- 标准change已生成：完整读取原稿proposal/design/tasks/五规格，四份MODIFIED保留canonical全文块。补Master-only历史、pinned身份而非latest、原子幂等/CAS、render输入hash及显式手工确认、最新检查权威、失败旧output拒绝、legacy schema/权限、v4远端能力和回退预检边界；业务代码及canonical未修改。
- 首轮全量strict实际24 passed/0 failed、diff-check通过；4/4产物done代表规格齐备，不代表业务实现完成。独立整包/计划审计进行中。
- 独立整包/计划复核发现旧F4冻结要求仍无条件强制Draft/Run，已拆为v3/工作流v4血缘校验与手工v4 Master所有权/上下文/引用/渲染闸门，并增加无Run手工Master可冻结场景；待复核确认。当前214项实施任务，未apply。
- 独立最终完整SPEC/plan复核APPROVE：上述冲突闭合，无剩余实质矛盾；批准仅规格/计划，不代表apply授权或connector验证。最终实跑全量strict24/24、diff-check及保留核验通过：23原要求标题/203原任务完整保留，10完整canonical块/33旧场景保留（4处兼容文字校准）。
- 标准proposal/design/tasks/五规格4/4产物齐备，214项实施任务0完成；原始目录与ZIP保留，canonical/业务/测试代码未改。文档未提交，未迁移/push/deploy/归档；等待用户apply及定向测试代码确认和真实connector基线证据。

## 2026-09-28：FE-F5C 五份主规格同步归档（通过）

- 基线main ac6d4dc含7956273功能提交；已跟踪文件干净，原始包/ZIP继续保留且排除提交。
- 已核对OpenSpec产物4/4 done、任务95/95；用户授权全部五份主规格同步、归档和本地提交。
- 仅文档收尾，不复跑与本轮改动无关的业务测试，不push/deploy/生产迁移；547测试/build为上轮实际证据，本轮重新运行规格保留检查、strict和diff-check。
- 本轮实际skills：using-superpowers、writing-plans、openspec-archive-change、verification-before-completion。
- OpenSpec CLI已同步五份主规格：新增system-assets-knowledge、product-settings（20项要求），更新FE-F0/F1、FE-F2、FE-F3A（4项要求），删除0项。归档路径 `openspec/changes/archive/2026-09-28-fe-f5c-system-assets-knowledge-settings/`，active change已不存在。
- 逐块核对24项delta要求与canonical完全一致；ac6d4dc中的22项既有要求和92个既有场景保留，未修改要求逐字保留。两个新增Purpose已补正式说明，修正归档工具生成的三个EOF空行。
- 归档后全量OpenSpec strict实际23 passed/0 failed、git diff --check通过；仅五份主规格、归档移动和四份记录进入本地提交。业务代码、原始包/ZIP、开发/生产数据库不变，没有push/deploy/生产迁移。

## 2026-09-28：FE-F5C 本地main整合（通过）

- 用户明确授权“融入main分支”；本轮仅本地提交/合入，归档与主规格同步仍待单独授权，不push/deploy/生产迁移。
- main及实现分支同在49d6c4b；四份根文档、标准change与计划逐项比较完全一致，主工作区没有业务代码差异。使用限定路径stash保留重叠资料后快进，不恢复旧记录覆盖新状态。
- 合入前后门禁使用新临时库/tmp/aicontent-f5c-main-integration-GvoX7B/studio.db，真实开发/生产库不变。工作树保留供F5C规格归档使用。
- 本轮实际skills：using-superpowers、writing-plans、finishing-a-development-branch、verification-before-completion。
- 功能提交 `79562731f4157bce74d7dab4c39a59f0c1f4a7e7`，36份白名单文件；本地main从49d6c4b快进合入，无冲突。原始包和ZIP仍未跟踪且未进入提交，canonical规格未修改，F5C change仍active。
- 合入前实跑547 passed（22.34秒）；合入main后复跑547 passed（20.96秒），均6既有警告。主工作区TypeScript/Vite build、bundle预算、OpenSpec all strict22/22、定向Ruff与diff-check全部通过；projects224.68kB raw/72.86kB gzip，Assets257.70kB、Settings229.76kB initial。
- main重叠资料已限定路径可恢复保存于stash `fcbbd3ed9db0c4db2f287a96e2cf17108c142e45`（fe-f5c-main-pre-integration-owned-docs）；内容已随功能提交合入，不重复apply旧文档覆盖当前进度。实现工作树和分支保留供后续主规格同步与归档，未push/deploy/生产迁移。

## 2026-09-28：FE-F5C apply 验收通过（隔离分支，未提交）

- 标准change：openspec/changes/fe-f5c-system-assets-knowledge-settings/，95/95完成；五份delta保留旧要求/场景，源包/ZIP未动，canonical尚未同步归档。
- 基线49d6c4b；业务代码仅在codex/fe-f5c-system-assets-knowledge-settings隔离工作树。main本轮只有标准规格与计划/记录变更，未合入业务实现。
- 已落地KnowledgeCollection/Item、f5c000000001、SQL有界Library/授权Usage、安全Settings投影、Assets五标签、Settings六分区、精确项目引用与显式Frozen FactPack边界；无新运行依赖或第二套Asset/Registry。
- 最终实跑：547后端测试通过（24.04秒、6既有警告）；TypeScript/Vite build与bundle门禁通过。Assets257.70kB、Settings229.76kB initial，无TipTap/XYFlow；projects224.68kB raw/72.86kB gzip。OpenSpec all strict22/22、定向Ruff（含models/main/既有引用接口）与diff-check通过。
- TDD首轮Library26 RED→33 GREEN；Settings最终53、Library+F3A最终51测试。临时SQLite迁移up/down/up、约束/并发单赢家及PG DDL编译通过；未实测PostgreSQL数据库并发。
- 独立完整SPEC/plan、Assets与Settings SPEC/QUALITY均APPROVE。闭合危险legacy库存admin权限、URL查询允许列表及地址重新输入、成员snapshot revision绑定、所选精确素材撤销回读/确认重置、Source sha256及后端撤销引用闸门。
- 隔离浏览器：集合CRUD/解除重启用/完整重排/刷新持久化；另一操作更新→旧UI409→显式刷新保留新备注；archive13只读。Source/固定素材版本项目引用、冻结包明确边界、真实PNG字节按需预览通过；撤销后固定原ID且权利/确认/引用禁用。
- 六设置分区和断连Plugin理由、只读Channel、Rule/Template区分、开发Header说明回读；viewer模型工具禁用、legacy入口拒绝。仅临时库用户样本，无真实配置/密钥保存、外网模型/Connector/发布调用或CLI配置写入。
- 临时库/tmp/aicontent-f5c-browser-mYr3Ek/studio.db；验收后停止自建API18106/Vite15186。测试PNG仅存隔离工作树忽略media；原开发/生产数据库不变。
- 实际skills：using-superpowers、openspec-propose/apply-change、writing-plans、executing-plans、using-git-worktrees、dispatching-parallel-agents、test-driven-development、receiving/requesting-code-review、systematic-debugging、verification-before-completion。用于先规范、隔离、失败证据与独立复核，不扩展发布权限。
- 待单独决定：canonical同步归档、本地commit/main整合。当前无commit/archive/merge/push/deploy/生产迁移；本地验收不是生产准入。

## 2026-09-28：FE-F5C 审计与隔离开发启动

- 实施首轮门禁：539后端测试通过（24.01秒、6既有警告），build/bundle通过，Assets255.74kB、Settings229.76kB initial，projects224.68kB raw/72.86kB gzip；strict22/22、定向Ruff/diff通过。旧F5B测试改为验证自身迁移版本，避免把旧切片写死成永远最新head。
- Settings独立SPEC通过；QUALITY发现少见URL凭据参数遗漏，已用version/api-version允许列表关闭，定向53测试通过，待独立复核。危险legacy库存新增服务端admin读取和前端入口闸门。
- Assets独立SPEC通过；QUALITY发现成员快照和父revision独立刷新、所选素材撤销回读两项竞态及Source sha256字段不齐，正在定点补齐。浏览器已实际完成集合创建/条目保存/解除与重启用、Source及精确素材项目引用、显式Frozen FactPack边界；六设置分区已回读。

- 用户明确授权完整规格review、标准归位及开发，另明确授权定向回归测试；无推送、部署或生产迁移权限。
- 真实main49d6c4b包含F5B归档与两份canonical；code migration head f5b000000001。复用干净工作树 `/Users/mshengran/.codex/worktrees/fe-f3b-content-identity/AIContentStudio`，新分支 codex/fe-f5c-system-assets-knowledge-settings 从main开始。
- 标准change已生成：五份delta，两份新增转换为ADDED格式、三份MODIFIED按完整canonical块保留旧要求/场景。补使用情况所有权、集合revision/归档竞态/排序、SQL有界筛选、false/NULL/撤销权利、安全Settings allowlist与角色能力、Assets/Settings首包门禁。源包及ZIP未更改。
- 首轮change strict及diff-check通过；独立Settings契约复核进行中，尚未修改业务代码。
- 隔离基线已实际完成：SQLite迁移到f5b000000001，pytest457 passed/6既有警告（19.12秒），前端build/bundle通过，/projects215.21kB raw/70.15kB gzip。标准全量strict22/22通过。
- Using change: fe-f5c-system-assets-knowledge-settings；OpenSpec apply为ready、93项任务。完整源包与五份规格已审查，校准不改变产品范围。按用户审查后开发授权进入apply；Assets后端与前端采用不重叠写集，Settings独立复核继续收严真实API边界。
- 独立完整SPEC/plan复核PASS：原始包要求保留，三份MODIFIED旧块完整，五份规格和实施计划一致。独立Settings反馈经代码核实补入11.7/11.8，当前95任务；冷启动Rule、版本动作、完整模型快照与显式文件/网络副作用已锁定。
- 前端两路由lazy与named budget检查先加失败断言：旧manifest实际失败“SystemAssetsKnowledgePage不是lazy route”；随后实现ProductSettingsPage安全六分区和显式按需配置工具。Library后端/Collection、Settings投影和Assets前端分不重叠写集实施，主控负责集成与验收。
- skills：using-superpowers、openspec-propose、openspec-apply-change、writing-plans、executing-plans、using-git-worktrees、dispatching-parallel-agents、test-driven-development、verification-before-completion、requesting-code-review；并行子任务仅限不重叠写集。

## 2026-09-28：FE-F5B 同步归档（通过）

- 当前真实基线 main `6452ad2` 已含功能提交 `9e0ce04`；tracked/staged/unstaged 干净，用户原始包/ZIP继续保留并排除提交。
- 归档前四项产物均 done，任务94/94；用户已授权全部六份主规格同步、归档和本地提交，不推送、部署或运行生产迁移。
- 本轮只修改规格和文档；457后端测试及前端build为上轮实际门禁，本轮重跑归档后的全量 strict、规格保留检查和 diff-check。
- 实际skills：using-superpowers、openspec-archive-change、writing-plans、verification-before-completion。
- OpenSpec内置archive实际同步六份：新增19项要求、更新4项、删除0项；归档路径 `openspec/changes/archive/2026-09-28-fe-f5b-performance-learning-memory/`。逐块比较全部delta与canonical一致，未修改的既有requirement逐字保留；Identity旧占位场景仅明确为pre-F5历史行为。
- 两份新增Purpose已补正式领域描述，修正归档工具生成的四份EOF空行；归档后全量strict实际21 passed/0 failed，git diff --check通过。仅规格及四份任务文档进入本地提交，原始包/ZIP继续未跟踪，不重跑业务测试，不推送、部署或生产迁移。

## 2026-09-28：FE-F5B 本地main整合（通过）

- 功能提交 `9e0ce04b8d076935e9b8182ce8154eb6e235e31d`，36份白名单文件；本地main从dd71a14快进到该提交，无业务冲突。
- 合入后从主工作区实际复跑：后端457 passed/6既有警告（17.64秒）；前端TypeScript/Vite/bundle PASS，/projects215.21 kB raw、70.15 kB gzip，Learning252.12 kB；OpenSpec strict20 passed/0 failed，工作区与提交diff-check PASS。测试使用隔离数据库 `/tmp/aicontent-f5b-regression-A7jHoA/migration.db`，没有改动开发或生产数据库。
- main原重叠审计资料限定路径保存于stash `756ed20db1f8dc29a5ad43e370b5f48b5c46bf50`（fe-f5b-main-pre-integration-owned-docs），其中独有SPEC审计段已整合到当前文档；标准规格除任务完成状态外一致，计划仅授权checkbox更新。备份仍保留，不重复apply旧状态造成文档/任务倒退。
- 用户原始包/ZIP仍原样未跟踪，没有进入36份提交；canonical `openspec/specs/` 与dd71a14完全一致，FE-F5B change仍active，未执行archive。保留实现工作树供后续规格收尾，无push/merge远端/deploy/生产迁移；只完成用户授权的本地main合入。

- 提交前本轮实际复跑：后端457 passed/6既有警告；前端build/bundle通过，/projects 215.21 kB/70.15 kB gzip，Learning252.12 kB；OpenSpec strict20/20及diff-check通过。标准包两边仅tasks完成状态不同，实施计划仅授权checkbox不同，其他规格内容一致。

- 用户已明确选择先将代码融入main，按分支收尾技能执行本地commit→快进→合入后门禁；不获取/推送远端、不部署或生产迁移。
- 主工作区四份重叠文档属于本任务审计与执行回链；独有SPEC审计段已保留到实施分支。用户原始包/ZIP继续排除，仅限定本任务路径备份与提交。
- 本轮skills：using-superpowers、writing-plans、executing-plans、finishing-a-development-branch、verification-before-completion。用户已选择本地合入，无需重复询问四种选项；工作树供未归档变更继续使用，不清理。

## 2026-09-28：FE-F5B apply启动

- 验收后已关闭本轮临时Chrome页并停止自建API18105/Vite15185；未停止用户原有服务。隔离数据库保留用于追溯，未删除数据。OpenSpec apply实际返回all_done、94/94，最终diff-check通过。

- 文档和94/94任务更新后的最终规格门禁：OpenSpec全量strict20 passed/0 failed，git diff --check通过。主工作区仅补执行回链，业务实现依旧在隔离分支。

- FINAL IMPLEMENTATION/REVIEW PASS：OpenSpec实施94/94。实际最终全量457 passed、6条既有警告；前端TypeScript/Vite及bundle通过，/projects 215.21 kB raw /70.15 kB gzip，Learning 252.12 kB initial，无重型编辑器。相关15份Python文件Ruff通过，最终文档后的strict/diff-check另复跑。
- 独立SPEC复审：历史/持久化/Receipt通过（63定向测试）、Learning通过；独立QUALITY复审后端与前端均APPROVE。质量反馈实际修复：AuditLog清理后恢复幂等仍受永久历史provenance保护；归档与观察写入用owner/active条件锁；异常嵌套引用在ORM前422；旧accepted只读派生可信可提升声明，不修改历史checksum/revision。
- 浏览器隔离验收完成：外部历史#1无发布时间/身份时诚实显示未知；Studio回收#2→80阅读观察#2→Insight#2→候选#2支持证据→人工accepted→角色#1记忆#1修订1。刷新身份Memory可见来源候选及single_sample/仅限隔离单样本限制；身份仍v1。DB实际readback：2条历史、1条Receipt、1条Memory/Revision、1条PersonaRevision、1条publication事件。Home已验证ready候选待办与accepted后消失。
- 本地Studio候选/目标为明确test_fixture，仅检验本地事务、浏览器和血缘，不代表真实平台发布。临时SQLite已验证升级/回退/升级、PostgreSQL方言DDL与驱动冲突注入；未实测PostgreSQL服务并发、生产迁移或真实Connector。
- 本轮实际skills：using-superpowers、openspec-apply-change、writing-plans、executing-plans、using-git-worktrees、subagent-driven-development、dispatching-parallel-agents、test-driven-development、systematic-debugging、receiving-code-review、requesting-code-review、verification-before-completion。Skill要求推动了隔离、失败优先回归、先SPEC后QUALITY复核；归档技能未执行。
- 代码尚未暂存/提交/合并/推送/部署；六份主规格同步和archive按已确认任务边界等待单独授权。用户原始规格包与主工作区无关文件保持不变。

- 最新实际门禁：437后端测试通过（6条既有警告）；前端build及bundle gate通过，/projects 215.21 kB raw /70.15 kB gzip，Learning 252.12 kB initial JS，无TipTap/XYFlow。后续契约补丁完成后仍需最终复跑。
- 浏览器项目回收发现未注册delivery.publication_confirmed事件，先补失败回归再注册事件；历史17项回归通过，浏览器现已真实保存Studio历史#2，发布时间未知仍未补成回填时间。
- 第二轮历史复核补幂等重试前当前状态/候选哈希/Receipt检查；超出分析上限coverage必须unknown而非missing，已补断言。学习验证已浏览器保存accepted，但可提升声明投影尚需后端/前端对齐后才能完成晋升。

- 用户确认校准规格及定向回归测试，使用change `fe-f5b-performance-learning-memory`，spec-driven，94项待实施。
- 复用已清洁且无需继续F5A开发的现有工作树，分支`codex/fe-f5b-performance-learning-memory`从main `dd71a14`开始；原始包与主工作区规格审计改动保留。
- 本轮不push/merge/deploy/生产迁移；主规格同步、归档和提交继续按tasks等待收尾授权。计划中的执行步骤采用`///`；先验证持久化测试失败，再实现。
- 基线实际复跑346后端测试及前端build/bundle通过。七资源模型与迁移先写失败测试，再实现通过；隔离临时SQLite升级→回退f5a→升级成功，当前head f5b000000001。
- 历史导入、快照最新值、同窗口修正与Home学习待办首批4项回归通过；时间窗口经UTC标准化比较，避免SQLite丢失时区后误拒绝修正。发布确认只回收有人工Receipt且可核实候选血缘的内容，回执提交时间不冒充发布时间。
- Skill驱动的并行实施按文件范围分离：Learning后端、Learning前端、Receipt兼容钩子；主流程维护历史/分析/Home/迁移与文档。仍在实现，不提前标记完整验收。
- 注册Learning正式路由后四个F5B测试文件71项通过；首轮全量实际424 passed，6条既有警告。此为中间结果，后续review修补后再复跑。
- 历史SPEC首轮7项边界修补：所有入库/查询时间统一UTC；数值修正不可变文字；大于10000观察明确不可计算不返回过期值；metric/key/unit/cutoff覆盖按实际选中观察计；日期缺失按同范围计；flush冲突整批回滚重试；恢复确认复用已有Receipt。补充granularity/cutoff及同目标反馈血缘，当前14项历史回归通过。
- 迁移历史回退再升级保留既有User记录且不自动创建发布历史；七资源DDL可按PostgreSQL方言编译，未实测PostgreSQL服务。Receipt worker完成新旧钩子与43项回归；全部原有路由测试亦通过。
- 前端SPEC通过，发现冻结证据数读取层级错误，正在补；浏览器完成外部历史导入、刷新、追加150浏览快照、保存人工Insight和创建候选，完整验证/晋升/身份投影待收尾。
- Learning SPEC发现任意记忆新主张借用旧候选、锁顺序和嵌套Insight覆盖3项，已交由原owned worker按TDD修补。不要将中间绿灯视作最终验收。

## 2026-09-28：FE-F5B 规格审计与归位（SPEC_REVIEW_PASSED / 待确认apply）

- 当前真实基线 main `dd71a14`，F5A 归档与两份canonical存在；Alembic代码head为`f5a000000001`，未核对或迁移任何生产数据库。
- 标准提案位于 `openspec/changes/fe-f5b-performance-learning-memory/`，原始 `openspec/fe-f5b-performance-learning-memory/` 与ZIP不改。
- 已补四份MODIFIED完整旧契约、新规格ADDED格式；修正Receipt确认时间与实际发布时间区别、receipt-less reconciliation不合成发布、指标测量粒度和修正链、候选验证冻结、Memory所有写入口及并发/幂等闸门。
- 单项strict PASS，4/4 artifacts done仅代表规格完整，不代表实现完成。全量门禁与独立规格复核待完成；实施计划在`docs/superpowers/plans/2026-09-28-fe-f5b-performance-learning-memory.md`。
- 按项目OpenSpec规则，在这份校准proposal获得明确确认前暂停apply；未创建业务实现、测试代码、迁移或提交，不push/merge/deploy。计划中的定向测试仍待apply授权。
- 独立规格复核首轮指出receipt-less reconciliation缺恢复入口；当前代码对账后目标human_confirmed，而两个Receipt API均拒绝此状态。已在spec/design/tasks/plan补显式confirm-reconciled人工确认动作及原子/幂等/权限/无远端副作用边界，等待针对性复核。
- 针对性复核最终APPROVE，该恢复入口问题已关闭，首轮其余边界无新增发现。校准后`openspec validate --all --strict`20/20 PASS，diff-check PASS；源包10/10文件未变，四份MODIFIED完整旧块保留（旧Memory占位明确为历史场景）。94项实施任务未执行，主规格未同步、未归档、未提交，业务代码未改。
- requesting-code-review安排独立只读复核，receiving-code-review核对代码证据并修正一项规格缺口；reviewer已关闭。下一步仅等待用户确认这份校准proposal及其定向回归范围后apply。
- 本轮实际skills：using-superpowers、openspec-explore、openspec-propose、writing-plans、requesting-code-review、verification-before-completion。explore用于只读审计，propose用于规格归位；writing-plans安排独立复核；不将严格校验等同于业务验收。

## 2026-09-28：FE-F5A 六份主规格同步与归档

- 用户已明确授权同步全部六份 canonical specs 并归档；当前 main `682df71`，4/4 产物与17/17任务完成。
- 本轮仅处理规格与收尾文档，核对旧契约保留后本地提交，不推送、部署、生产迁移或实施 FE-F5B。
- `openspec archive fe-f5a-home-opportunity --yes` 已同步全部六份主规格，报告 +11 / ~10 / -0 / rename 0，归档目录为 `openspec/changes/archive/2026-09-28-fe-f5a-home-opportunity/`，17/17任务完整。工具提示建议拆分超过10条delta，属于已完成切片的非阻塞建议。
- 已逐块验证21个delta与canonical一致、四份旧主规格全部37个旧要求及场景正文保留；新增两份 Purpose 已补正式说明。首次 strict 19/19 通过，diff-check发现工具生成的四处EOF空行，已修正，最终校验待复跑。
- 修正后的最终门禁：`openspec validate --all --strict` 19 passed / 0 failed（18份主规格及1个既有active change），`git diff --check` PASS。本次仅规格和文档变化，不重复执行已在main验证的346项业务测试与前端构建；待提交本地main，未推送、部署或运行生产迁移。
- 本轮实际 skills：using-superpowers、openspec-archive-change、writing-plans、verification-before-completion。归档 skill 用于完整性和同步检查，按明确授权使用 OpenSpec CLI 同步并归档；未新增业务或测试代码。

## 2026-09-28：FE-F5A 本地 main 整合

- 用户授权合入本地 main；已核对主工作区 main 与隔离分支共同基线 `2f52053`，主工作区无已跟踪改动，原始规格包保留。
- 功能提交 `3012fe5`（30 个本任务文件）已从 `codex/fe-f5a-home-opportunity` 快进合入主工作区 main；未将用户原始规格包加入提交。
- 提交前及合入 main 后均实际复跑：346 后端测试通过（6 条既有警告）、前端 TypeScript/Vite build/bundle gate 通过、OpenSpec all strict 18/18 通过、diff-check 通过。测试只使用已迁移的隔离临时库。
- 六份 delta 同步与归档仍待确认；未推送、部署或运行生产迁移，保留隔离工作树用于后续收尾。
- 本轮实际 skills：using-superpowers、writing-plans、finishing-a-development-branch、verification-before-completion；没有新增业务实现或测试代码。

## 2026-09-28：FE-F5A apply（IMPLEMENTED / REVIEW_PASSED，待归档确认）

- 基线：main `2f52053`；业务改动仅在隔离工作树、`codex/fe-f5a-home-opportunity`。
- 已实现 Opportunity、Signal、AssessmentRevision、Conversion，复用 AuditLog 和 ProjectEvent；转换不创建 Topic / FactPack / Fact Boundary / IdentitySnapshot。
- 首轮回归暴露并修正失败锁事务残留、Brief scope 类型检查、首页机会先截断后排序；独立复核补齐旧项目 unknown 不可遗漏与真实近期活动。
- 临时库 `/tmp/aicontent-f5a-yDS9qM/migration.db` 升级→回退→升级通过，head `f5a000000001`。初始迁移使用当前 metadata，新增迁移沿用既有幂等建表策略。
- 当前全量后端 331 passed（指定上述已迁移临时库，避免既有 worker 测试访问空默认数据库）；OpenSpec strict 18 passed，diff-check 通过。最终批量投影改动后须重跑，不将当前结果当作最终门禁。
- 浏览器实际完成新建机会、人工信号、评估 v1、qualified 转项目及刷新；项目 Brief v1、来源机会回链存在，Overview 为 evidence_needed。
- 最终门禁：346 后端测试 passed（含 15 F5A 领域测试和 13 批量投影测试）；前端 TypeScript/Vite build/bundle gate PASS；OpenSpec all strict 18 passed；Ruff 定向检查及 diff-check PASS。既有 6 条弃用/SQLAlchemy 警告未扩展修复。SQLite 独立 Session 并发回归通过，未进行 PostgreSQL 实测。
- `/projects` 首包 215.09 kB raw / 70.12 kB gzip，Home 231.11 kB、Opportunity 247.32 kB raw；三个入口均不包含 TipTap/XYFlow。
- 后端独立复核 APPROVE；前端两项阻断（Brief 身份对象损坏、HTTP LAN UUID 缺失）已关闭，前端最终 APPROVE。身份 Brand-only 转换后只改目标的 Brief v1→v2 实际浏览器保存/刷新验证通过，身份对象不变。UUID native/fallback 与稳定重试 key 已定向验证，未实际部署 LAN。
- Home 全部自有活动项目按 100 个批量扫描决策，近期卡片独立限额20；不读取历史候选/回执全文，实时证据/媒体权利门禁复用并回归。近期活动是真实 ProjectEvent。
- OpenSpec 17/17 apply 任务完成。四份 MODIFIED delta 已补成保留既有要求/场景的完整块，修正 Unknown 标题匹配，避免将来归档覆盖旧契约；canonical specs 尚未同步。归档同步问题已发给用户，等待确认。
- apply 收尾时未归档、未提交业务改动、未推送/合并/部署/生产迁移；随后本地 main 整合结果见顶部记录。临时验收服务已停止，临时数据库保留在隔离路径以便追溯。
- 本轮实际 skills：using-superpowers、openspec-apply-change、writing-plans、executing-plans、subagent-driven-development、test-driven-development、systematic-debugging、requesting-code-review、receiving-code-review、verification-before-completion；openspec-archive-change 完成同步评估并要求暂停等待用户确认，未执行归档。

## 2026-09-28：FE-F5A-SPEC-R1（规格修订完成，未 apply）

- 已核对 review 指出的 6 项阻塞与 2 项补充项，确认均适用于当前 OpenSpec。
- 已补充 Opportunity `converted/archived` 状态闸门、合法 triage/reopen、Assessment `expected_revision`/409/race/无部分提交、AuditLog 与 ProjectEvent 分工、Signal 派生来源类型、Home 排序/决策优先级/去重，以及核心投影失败的 `incomplete/section_errors` 语义。
- 已将 proposal 的 Modified Capabilities 补齐 FE-F0/F1、FE-F3A、FE-F3B、FE-F4；tasks 改为要求定向自动化回归。
- `openspec validate --all --strict`：18/18 通过；`git diff --check`：通过。
- 仍未执行业务代码 apply、数据库迁移、推送、部署或生产写入；状态为 `SPEC_R1_READY`，等待独立确认后再授权 apply。

## 2026-09-28：FE-F5A Home + Opportunity 标准包审计（SPEC_READY，未 apply）

- 用户提供并解压标准包于 `/Users/mshengran/Project/AIContentStudio/openspec/fe-f5a-home-opportunity/`；原始目录保留不改。
- 已确认本地隔离工作树基线为 `85b8c08`，FE-P1 canonical spec 与归档变更存在；connector 仍需外部刷新确认，未把本地证据冒充 connector 已同步。
- 已将 F5A 新规格及 FE-F0/F1、FE-F3A、FE-F3B、FE-F4 四份 delta 归位到 `openspec/changes/fe-f5a-home-opportunity/`。
- 审计并修正一个语义差异：转换只允许用户明确选择的 SourceDocument signal 建立普通 ProjectSourceBinding，但绝不自动创建、冻结或绑定 Fact Boundary；自动分析能力不可用时不得伪造 Assessment。
- `openspec validate fe-f5a-home-opportunity --strict` 通过；`git diff --check` 通过。未修改业务代码、未执行迁移、未 apply、未推送/合并/部署。
- 下一步前置：connector 真实可读 FE-F4/FE-P1 最终基线后，才可执行 `/opsx:apply fe-f5a-home-opportunity`。

## 2026-09-28：FE-F5A Home + Opportunity 规格提案

- FE-P1 已在本地提交为 `85b8c08`，随后创建分支 `codex/fe-f5a-home-opportunity` 作为下一阶段规格基线；未推送、合并或部署。
- 已审计现状：`/home`、`/opportunities` 仍由 `ProductPlaceholder` 提供；项目 Overview 已能派生 Brief/Evidence/Identity/blocked/stale/review/delivery 风险；SourceDocument、DataSnapshot、ProjectEvent、Review、DeliveryTarget 均可复用。当前没有 ContentOpportunity、HomeTask 或调度实体。
- 已创建 `openspec/changes/fe-f5a-home-opportunity/`，包含 proposal、design、三份 delta spec 和 tasks。F5A 明确分为 Opportunity（三类持久对象、评估版本、显式转项目）与 Home（现有事实 Projection），不自动绑定 Evidence、不创建 Topic、不自动更新 Identity、不引入新闻抓取系统。
- OpenSpec strict 校验和归档前复核待完成；F5A 业务代码 apply 必须先确认 connector 能读到 FE-P1 `85b8c08` 和 canonical spec。

## 2026-09-28：FE-P1 主规格同步与归档

- 用户明确选择将五条 FE-P1 长期要求全部同步到主规格并归档。`openspec archive fe-p1-frontend-bundle-performance --yes` 报告 10/10 任务完成、5 added / 0 modified / 0 removed；新增 `openspec/specs/fe-p1-frontend-bundle-performance/spec.md`，归档到工具实际生成的 `openspec/changes/archive/2026-09-27-fe-p1-frontend-bundle-performance/`。已将自动生成的 Purpose TBD 改为正式契约描述。归档后全部 16 份主规格 strict 为 16 passed / 0 failed；前端 TypeScript/Vite 构建及预算通过（`/projects` 初始 JS 214.45 kB raw / 69.98 kB gzip），`git diff --check` 通过。没有提交、推送、合并或部署。

## 2026-09-28：FE-P1 apply

- 用户明确输入 `/opsx:apply`；在已有隔离工作树 `codex/fe-p1-frontend-bundle-performance`（起点 `6d1ecbb`）实施，不改本地 `main`。OpenSpec `spec-driven` 4/4 产物完整、10 项任务待做；详细步骤见 `docs/superpowers/plans/2026-09-28-fe-p1-frontend-bundle-performance.md`。本轮不推送、合并、部署或执行生产操作。
- Task 1.1 基线复跑：TypeScript/Vite build 通过，单 JS 1,095.28 kB（gzip 351.06 kB），CSS 48.52 kB；隔离 preview 对 `/`、`/projects`、演示/数字项目、生产、review、identity 与两条重型旧路由均返回 SPA HTML 200。该 HTTP 检查只证明直接链接服务回退，不等于页面交互已验收。端口 15176 已关闭。
- Task 1.2–1.4：真实项目列表、详情、生产 wrapper 与共享类型已拆成独立模块；`App.tsx` 现以 `React.lazy` 加载页面，并在保留 sidebar 的 route 区域显示状态/可重载错误。`npx tsc -b` 通过，静态导入检查显示项目列表不再连到七标签或生产设计器、详情不再连到生产设计器；浏览器交互见下方 Task 3.2。
- Task 2.1–2.3：正常 `npm run build` 生成 manifest 并执行预算脚本；按入口加 `/projects` 静态导入闭包去重后为 214.45 kB raw / 69.98 kB gzip（4 个 chunk），比 FE-F4 1,095.28 kB raw 基线低 80.4%；全站生成 JS 1,138.41 kB raw / 375.65 kB gzip，独立报告而非首包门禁。详情与生产 chunk 均不在项目列表静态闭包；构建时还从 Rollup module ID 生成重型模块归属表，明确 TipTap 只在 Workspace chunk、XYFlow 只在 Workflows chunk，预算脚本会拒绝它们进入 `/projects` 静态闭包。未设置 `manualChunks`。最新 `npm run build`（TypeScript + Vite + 预算）通过。
- Task 3.2：生产 preview 直接进入 `/`、`/projects`、数字详情/生产、`/review`、`/identities`、`/workspace`、`/workflows` 和非数字演示路径，页面模块均可加载；preview 无 API 代理，故数字项目真实内容仅在随后隔离 API 联调验收。慢网条件下可见有可访问状态的“正在加载页面…”且导航壳层保留；拦截 Workflows chunk 后出现错误说明/重载按钮，转回项目列表恢复。隔离临时 SQLite + 127.0.0.1:18083/15177 下创建项目 #1、身份 #1、文字单元 #1，进入生产保存 System 常量节点项目覆盖 v1、启动 Run #1 succeeded；刷新仍可见固定工作流 #1、Run #1 和冻结定义 checksum。验收服务已停止，仅含测试数据的临时 SQLite 已删除，未操作正式数据库。
- 首轮独立代码复核发现 `location.key` 会因 query-only 导航变化而重挂载整个页面；已改为按 `pathname` 重置错误边界，避免项目标签或 Review 筛选切换丢失本地状态。复核还指出仅排除路由 chunk 不足以证明重型依赖缺席；现已增加 Rollup module 归属门禁，构建证实 TipTap/XYFlow 分别位于 Workspace/Workflows。README 已更新；复核后的浏览器检查和最终记录仍待完成，不提前归档。
- 修正后已重新通过 `npm run build`（含 TypeScript/Vite/预算）、`openspec validate fe-p1-frontend-bundle-performance --strict` 和 `git diff --check`。生产 preview 再次验证演示项目同路径 `?tab=matrix` 标签切换；拦截 Workflows chunk 后错误说明/重载按钮可见，点击侧栏项目路由恢复。preview 无 API 代理时列表显示 `Not Found`，真实 API 联调结果以上述独立临时库为准。第二次独立只读复核正在进行。
- 第二次独立针对性复核已给出 `APPROVE`，没有新的高/中风险发现；复核者只读核对模块拆分、pathname 边界、重型依赖模块归属和现有构建产物，构建与浏览器复测由本轮直接执行。OpenSpec 10/10 任务均完成；后续同步与归档结果见本文件顶部。

## 2026-09-28：FE-P1 前端首包性能规格审计

- 用户授权审计 FE-F4 分支并提出 FE-P1 OpenSpec，未授权 apply。已在干净的 FE-F4 `2f3ced2` 上创建 `codex/fe-p1-frontend-bundle-performance` 与标准变更目录。
- 重新运行 `npm run build`：JS 单文件 1,095.28 kB（gzip 351.06 kB），CSS 48.52 kB；`App.tsx` 静态加载全部现有/旧页面，`PersistentProjectPages.tsx` 同时承载列表、详情、生产并静态加载 `ProductionDesigner` 和七标签。当前 web 包无独立测试脚本；规格和门禁待完成。
- FE-P1 proposal、design、新能力 delta spec、tasks 已按 OpenSpec `spec-driven` 顺序写入；范围为路由/项目生产边界、初始 JS 预算、可恢复加载与路由冒烟；不含业务代码或后端变更。规格验证与独立复核待执行。
- `openspec validate fe-p1-frontend-bundle-performance --strict` 通过；OpenSpec 状态 4/4 artifacts complete，JSON 回读确认 5 条 ADDED 要求与对应场景均被解析。`git diff --check` 通过；仅提案、README、任务/进度/发现文件发生变化。独立复核未执行，不将 strict 校验称为正式 review；等待用户确认后才进入 apply。

## 2026-09-28：FE-F4 apply 启动

- 用户明确选择五份 delta 全部同步主规格。归档前比对四份 MODIFIED 的 9 条要求、28 个旧场景标题全部保留；`openspec archive fe-f4-project-review-distribution --yes` 报告新增 11 条、修改 9 条、删除 0 条，归档实际路径是 `openspec/changes/archive/2026-09-27-fe-f4-project-review-distribution/`（工具使用宿主机日期）。新增主规格的机械 Purpose 已改成正式产品契约说明。归档后五份主规格保留 delta 与旧契约，全体 15 份主规格 strict 校验 15 passed / 0 failed，`git diff --check` 通过；本地提交待执行。
- 归档后重新隔离运行后端全量 318 passed / 6 warnings，前端构建通过（主包 1,095.28 kB 警告）。此前 FE-F4 定向 8 passed、Ruff F 通过；`openspec status` 四类产物均 done，tasks 57/57 勾选。未推送、合并、部署或运行生产迁移。
- 独立复核最终一项（历史 Candidate 裸审批）已确认关闭，无剩余高风险问题。FE-F4 OpenSpec 任务现全勾选；非 Draft v3 包回归实际检查 PNG 字节和正确素材文件名，定向 8 passed。OpenSpec strict、`git diff --check`、本次后端 Ruff F 通过；最终后端全套正在复跑。五份 delta 同步主规格的归档选项已向用户确认，回复前不归档。
- 二次独立复核仅剩历史 Candidate 仍可从裸审批 API 再次批准或退改；现已按当前 Candidate ID 在服务端同时封住 approve/request-changes，并增加历史候选负例。定向 FE-F4 8 passed；复核最后一项正在回读。前端 build 和上一轮后端全量均通过，最终全量需在最后改动后复跑。
- 独立代码复核首次指出四项阻断：旧项目 Draft 素材裸 ID、Unknown 普通回执绕过对账、历史 Candidate 新增授权、批准后前端详情不刷新。现分别补上共享 Project Run 所有者闸门（覆盖旧 Draft/Job/素材/检查/文档/Discoverability）、Unknown 回执拒绝并要求对账、当前 Candidate 判定、审批后重取详情。定向 FE-F4 7 passed；第二轮独立复核进行中。修后全量后端 317 passed / 6 warnings，前端 build 通过；新增更细断言后定向 7 passed。归档/提交仍未执行。
- 最终门禁首轮复跑：隔离 SQLite 全量后端 317 passed / 6 warnings；前端 TypeScript/Vite build 通过（1,095.18 kB 主包警告）；FE-F4 OpenSpec strict 与 `git diff --check` 通过。旧 article-handoff 与通用 DeliveryTarget 授权入口已调整为先核验项目所有者再返回状态，避免跨项目状态探测。独立代码复核已发起；尚未归档/提交。
- FE-F4 浏览器门禁补齐：隔离验收库（与用户当前服务分离）依次验证 Blocked 无 Draft 输出时 Freeze 禁用、Unknown 展示人工对账且无重发按钮、更新 Candidate 后旧 Unknown 不覆盖当前 Stale、Stale 当前候选 Approve/Authorize 禁用、历史 Candidate 仅显示只读提示。首次鼠标 click 自动化未切换 tab，改用真实键盘 Enter 后交付 tab 控件与状态均在可访问树中核验；此非产品逻辑错误。临时浏览器页与 18082/15175 服务已关闭。验收库内造数仅用于 UI 状态，不当成真实 Freeze→Approve→Delivery 业务验收；真实链路由后端集成测试覆盖。
- FE-F4 第五批：独立临时 SQLite 上后端全量 317 passed / 6 warnings；另一独立临时库 Alembic 从空库升到 `f4a000000001`、退回 FE-F3B、再升 FE-F4 均通过。隔离 127.0.0.1:18082/15175 浏览器验证 `/review` 可显示真实项目/单元受阻状态；在隔离验收库注入待核对目标后，页面可见 `unknown` 与“先对账、不可自动重发”说明。交付标签点击的 UI 自动化未产生状态变化，浏览器交互门禁尚不算通过；不会把截图/页面加载误报为完整交互验收。OpenSpec strict、diff-check 通过；任务 4.4、5.4、8–9 仍待收口。
- FE-F4 第四批：`/review` 从 placeholder 改为真实项目审核页，分项目/单元、状态筛选、候选预览/变更/检查/交付四栏，区分 Freeze、审批、授权、ZIP、人工作业回填与 unknown 对账；历史 Candidate 的交付操作隐藏，自动草稿因无已验证账号映射不开放。项目 Overview/Versions 接入相同审核投影，旧 `/review-publish` 未改。前端 TypeScript/Vite build 通过（bundle 1,095.18 kB，原有体积警告）。服务端额外封闭已批准候选的退改状态歧义，ZIP 下载本身推进待人工回填，并按实时 FactPack item 权利检查交付（避免 ORM 关系缓存掩盖撤权）；FE-F4/F3A/delivery 定向 28 passed。浏览器验收与最终全量门禁未完成。
- FE-F4 第三批：Project Review Center 新增项目/单元/候选只读投影及 Candidate diff；状态只按当前 Candidate/Target 计算，旧 Candidate 的 unknown 不污染新候选，当前目标的 unresolved unknown 优先。旧 article-handoff 的 project-bound alias 已做所有者检查并拒绝混用 v1 包路径；旧 Topic Review read model 排除 project-bound run。冻结来源不能悄悄替换成同 Job 的较新 Draft；并发同 Project/Unit/hash 冻结有数据库唯一键与冲突回读。交付授权、结果、对账、回执开始与项目事件同事务记录。FE-F4 + delivery + review + v2 candidate 定向 21 passed。全量测试首次因本机 `NO_PROXY/no_proxy` 配置出现 13 个无关失败；去掉二者后为 316 passed / 1 个既有 worker 默认 SQLite 未初始化失败；已建立独立临时测试库供最终复跑，不改生产或主工作区。
- FE-F4 第二批：Draft-backed WorkflowOutput 可冻结 v3 Candidate，Freeze/Content Approval/退改分离；项目账号授权沿稳定 ContentAccount 键幂等。旧裸 `/assets` 的项目候选读取按所有者隔离，项目候选不能经旧素材增删/导出接口修改；匿名封面/媒体直链对项目候选关闭。项目 manual_handoff 已改走 v3 manifest 成品包（真实媒体字节与实时权限校验），随后可人工回填 Receipt；旧 v1 手工交付路径保持。定向 FE-F4 + delivery + v2 candidate 测试 17 passed。项目 Review Center 投影、前端、其他 raw-ID/alias 审计及全量门禁仍待完成。
- 持久化 1.1–1.4 完成：稳定 `authorization_account_key` 取代仅 `account_ref` 的唯一约束；同引用不同 ContentAccount 可分别授权、同账号幂等，引用改变须新授权版本。用旧 FE-F3B checkout 构造真实旧结构并插入 Asset/Review/Target/Attempt/Receipt，隔离库升级→回退→再升级后 5 类旧行及历史 account_ref 均保持，未伪造项目或账号链接。新建库往返亦通过。相关定向测试 10 passed。
- 首批模型与迁移：ContentAsset 新增 Project/Unit/IdentitySnapshot/Run 与独立 `candidate_hash` 字段；Review 可绑定 Candidate 且项目原生行可无旧 Draft；DeliveryTarget 增加 ContentAccount 和稳定授权账号键。隔离 SQLite 新建库往返通过；旧 delivery/review 与新 schema 定向测试 10 passed。此时稳定账号幂等及旧行往返尚待补齐，已由上一条闭合。
- 用户明确授权 FE-F4 apply；在隔离分支 `codex/fe-f4-project-review-distribution` 执行，不改本地 `main`。OpenSpec `spec-driven` 起点为 57 项、已完成 3 项基线任务；计划见 `docs/superpowers/plans/2026-09-28-fe-f4-project-review-distribution.md`。启动时业务代码、迁移和验收均未完成；本轮不推送/合并/部署/运行生产迁移。

## 2026-09-28：FE-F4 规格审计

- 后续本地主工作区 `main` 已从 `c044085` 快进到 FE-F3B `55eba02`。已核实 FE-F3B 四份主规格、`ContentAccount`/`IdentitySnapshot`、身份路由和迁移 head；隔离 SQLite 基线后端 310 passed、前端 build、14 份主规格 strict 均通过。连接器自身回读未验证；FE-F4 尚未 apply。
- 初审时主工作区 `/Users/mshengran/Project/AIContentStudio` 为 `1fa4520`，仅有用户提供的未跟踪 FE-F4/FE-F3B 来源包；当时看不到 FE-F3B 代码。因而复用隔离工作树并从 FE-F3B `55eba02` 建 `codex/fe-f4-project-review-distribution`；后续本地 `main` 已同步，见上条。
- 来源目录无 README，9 个文件与 zip 清单一致。初审发现四份 MODIFIED delta 只有新增句子，直接归档将覆盖原主规格场景；现有 ContentAsset/Review 的 Topic/Draft 必填列也需要在 FE-F4 设计中明示兼容迁移。准备归位与校准；来源包保持原样。
- 标准 `openspec/changes/fe-f4-project-review-distribution/` 已建立；五份 delta 均归位。四份 MODIFIED 已从 canonical specs 复制完整同名 Requirement 与所有旧场景，再加入 FE-F4 合同；逐条场景比对无丢失。新能力规格补齐权限、v3、候选冻结/批准/授权、Unknown、投影、前端和项目历史场景。设计/任务明确迁移可空列、候选哈希、受支持来源适配、账号能力验证和 raw-ID 保护。当前 OpenSpec strict 与 `git diff --check` 通过；独立只读规格复核进行中。
- 进一步检查 OpenSpec 解析 JSON 发现第二段规范文字不进入 `requirement.text`；九个 MODIFIED 要求的新增句子已并回首段，CLI JSON 回读确认。保留的旧场景未改写；本轮仍只修改规格与记录。
- 独立审阅第一轮指出 v3 非 Draft 人工成品包不可直接走 v1 `article_handoff`，以及两个同 `account_ref` 的 ContentAccount 会被旧唯一约束合并。已补 v3 manifest-based 本地包路径、不可用形态阻断、稳定授权账号键/迁移/幂等任务与场景；OpenSpec strict、diff-check 再次通过，等待针对性复核。
- 独立针对性复核 `PASS`：上述两处高风险规格缺口均闭合，没有新的 critical/high/medium/low 问题。仅为规格复核，不是实现或 apply 授权；当时 FE-F3B 主工作区可见性门槛尚未满足。
- 本轮规格门禁：`openspec validate fe-f4-project-review-distribution --strict` 通过，`git diff --check` 通过，`git diff --exit-code -- apps/api apps/web` 无业务代码变更。标准变更位于 FE-F3B `55eba02` 基线的隔离工作树；本地主工作区 `main` 现已具有 FE-F3B canonical spec、IdentitySnapshot 和 ContentAccount。状态为 `SPEC_READY / APPLY_AWAITING_EXPLICIT_APPROVAL`；连接器回读未独立验证。本轮仅准备在 FE-F4 分支本地提交规格，不推送、合并 FE-F4、部署或执行迁移。

## 2026-09-27：FE-F3B 审计与 apply 起点

- 用户明确授权四份 delta 全部同步。`openspec archive fe-f3b-content-identity --yes` 已更新 FE-F0/F1、FE-F2、FE-F3A 主规格并新增 FE-F3B 主规格；工具实际归档目录是 `openspec/changes/archive/2026-09-27-fe-f3b-content-identity/`。四份主规格的 Purpose 已校正；归档后主规格 strict、diff-check 和本地提交待完成。未推送、合并、部署或执行生产迁移。
- 归档后核验：四份主规格均包含各自 FE-F3B delta，`IdentitySnapshot`、Series > Account > Persona、`identity_unready` 和 Brief identity scope 均可检索；全体 14 份主规格 strict 校验 14 passed / 0 failed，`git diff --check` 通过，受影响主规格无 `Purpose: TBD`。提交前重新完整运行后端 310 passed / 5 既有 warnings、前端构建通过；现有主 JS bundle 1,079.36 kB 提醒未在本切片处理。
- 2026-09-28 独立复核修补：任何 Unit 身份/形态/工作流重绑均生成新快照；同层级纯身份刷新保留兼容的项目覆盖（含有 Run 后 fork 的新 Unit），旧 Run 仍固定旧快照。长期观点改为保留结构的 JSON 编辑；修订 409 后锁定旧草稿并要求显式加载最新版本；历史 Run 仅以冻结 ID/快照表示历史身份，当前名称明确标注为当前值。FE-F3B 定向回归 14 passed；全量门禁与二次复核待运行。
- 2026-09-28 修补后门禁：清除本机异常 `NO_PROXY/no_proxy`，用独立临时 SQLite 初始化 worker 数据库后，全量后端 310 passed / 5 既有 warnings；前端 `npm run build`、OpenSpec strict、`git diff --check` 通过。未改环境持久配置、未碰生产库；等待独立二次复核。
- 2026-09-28 独立二次复核 `REVIEW_PASSED`：五项收尾问题均闭合；复核者另跑 FE-F3B 14 项、FE-F2/F3A 27 项及 TypeScript/diff-check。OpenSpec 11.8 已完成，归档前等待四份 delta spec 同步选择；不将本地回归视为生产验收。

- 用户确认 FE-F3B 整包进入 apply。工作树 `/Users/mshengran/.codex/worktrees/fe-f3b-content-identity/AIContentStudio` 从 FE-F3A 提交 `1fa4520` 建立，分支 `codex/fe-f3b-content-identity`；来源目录仍留在主工作区，未修改。
- 已将来源 proposal/design/specs/tasks 纳入标准 `openspec/changes/fe-f3b-content-identity/`；新能力规格改为 ADDED delta，三份旧能力规格补全 MODIFIED 原要求，OpenSpec strict 通过。
- 审计补强：现有 BrandVoiceVersion 是无 owner 字段的全局版本资源；brandless 历史 Persona 不补造 Brand/修订；归档祖先不得参与新生产；重绑父级时不得悄然丢弃不兼容子级；旧裸 Workflow API 仍须保护 Account/Series 默认定义。
- 基线第一次后端全套 295/296：唯一失败是新工作树默认 worker SQLite 文件缺表，`test_task_queue` 的 Celery task 不使用测试内存库。使用独立临时 SQLite 并初始化后，296 passed、5 warnings；前端 build 通过，现有主包 1,060.65 kB 提醒。未改代码、未触及生产库。
- 模型已加 Brand/Persona/Account/Series 的稳定实体与修订、IdentitySnapshot、两类新默认绑定，并为 Persona/Unit/Run 添可空引用。定向模型结构测试先按缺表/缺列失败、实现后 2 passed。隔离空库迁移初次因新增外键无名称而失败；显式命名后 `f3a→f3b→f3a→f3b` 通过。带历史样本的迁移回读仍待做。
- 内容身份服务和新路由已接入：四级层级所有权、Pydantic override 字段校验、追加修订与 409、缺失/显式 null/整体替换解析、全局 published BrandVoice 检查、快照构造与所有者读取。第一批 API 定向测试先 404 后 3 passed；Unit/Run 接线和跨所有者/归档回归仍待完成。
- 新 Unit 已持久化 IdentitySnapshot，Run 启动时复制精确 snapshot ID，并在归档身份祖先时拒绝新运行，历史 Run 仍可读取。相关测试先因序列化缺字段失败、修正后通过；现有工作仅完成此纵切片，重绑/默认/前端仍待实现。
- 显式身份重绑已接入 Unit PATCH：无 Run/Snapshot/Output 历史时原地生成新快照；有历史时创建替代 Unit、归档旧 Unit，旧 Run 固定旧快照。父级变化而未显式处理子级时返回 422；定向 FE-F3B/FE-F2 回归 25 passed。层级默认工作流尚未接入，当前重绑仍仅解析角色默认。
- 账号/栏目默认工作流的 GET/POST、乐观修订冲突、可移植性校验和有效优先级已接入；新 Unit 固定 Series > Account > Persona，旧 Unit 不自动重绑。旧裸 Workflow API 的 owner 检查覆盖账号/栏目 scope；定向 FE-F3B/FE-F2 回归 26 passed。
- FE-F3A 读模型已接入真实快照条目及 legacy 状态，Overview 对活动单元的缺失/空身份给 `identity_unready`；新 Brief 版本里的结构化身份 ID 会校验 owner 与层级，旧字符串标签保留。定向 FE-F3B/FE-F2 回归 27 passed。
- `/identities` 已换为后端持久层级工作区：树、四级修订字段、继承/覆盖/清空、历史、账号/栏目、工作流偏好和诚实的内容记忆空态；前端构建通过。项目版本页也显示真实身份快照及 Legacy 条目。浏览器交互与项目/生产上下文仍待验收。
- 在独立临时 SQLite 上，先由 FE-F3A 原代码建真实旧 schema 并插入 owner/Persona/Project/Unit/Workflow/Run，再由 FE-F3B 执行 upgrade→downgrade→upgrade；旧 Run checksum 原样、Unit/Run 快照仍 NULL、IdentitySnapshot 0 行，`foreign_key_check` 空。迁移有既存 workflow parent FK 的 SQLAlchemy 警告，非失败；未碰项目数据库或生产库。
- 项目矩阵账号/栏目选择、有效默认预览、显式身份刷新和生产页四级 Context Header/只读快照已接入；最新前端 build 通过，现有主 bundle >500 kB 提醒仍在。浏览器端到端验收尚未做。
- 全量后端首次 303 passed / 1 failed：旧 FE-F3A Overview 测试假设唯一风险为 `unit_blocked`，与 FE-F3B 新 `identity_unready` 合同冲突。按新合同加入确定性的身份下一步并更新该断言后，全量 304 passed / 5 既有 warnings。该调整仅涉及风险读模型与既有回归预期，不抹掉真实风险。
- 追加 FE-F3B 定向回归：身份归档后 project-scoped 与 legacy Run rerun、项目覆盖保存均拒绝；发布 BrandVoice 可入快照、草稿版本不可引用；身份新修订不改旧快照，显式重绑生成新 checksum。FE-F3B 定向 9 passed，最新前端改动后 build 通过；后续需重跑全量。
- 最新本地门禁：后端全量 305 passed / 5 warnings；前端 TypeScript/Vite build 通过（主包 1,078.53 kB 提醒）；OpenSpec strict、`git diff --check`、涉及后端文件 Ruff F 检查通过。独立代码审阅已发起，尚未归档/提交。
- 补充 Snapshot `readiness`/原因元数据，以及 Unit 创建、原地重绑、替换事件的结构化旧/新 snapshot ID。定向测试最初误把 Activity 分页对象当数组，按既有 `items` 契约修正测试后 9 passed；全量门禁需在审阅修订后再次运行。
- 扩充 FE-F3B 定向测试至 12 passed：跨层级/跨所有者、归档祖先、唯一键竞态回滚、数组/对象整体替换、BrandVoice 覆盖和账号默认模板可移植性。隔离浏览器与 API 共同验收：四级身份创建/刷新、栏目默认 v1 保存后旧 Unit 未自动改绑、新 Unit 固定 v1、品牌修订 v2 后旧快照仍 v1、无历史原地刷新到新快照、真实 Human Run 固定快照、再刷新创建替代 Unit 并归档旧 Unit。临时库读回旧 Run checksum 不变。
- 最新完整门禁：后端 308 passed / 5 warnings，前端 build 通过（主包 1,078.53 kB 警告），OpenSpec strict、diff-check、Ruff F 通过。独立审阅结论仍待回，未归档/提交。

## 2026-09-27：FE-F3A apply 起点

- 用户已明确授权进入 apply；使用标准变更 `fe-f3a-content-project-core-completion`，spec-driven 产物 4/4，任务 2/54 完成。
- 当前分支 `codex/fe-f3a-project-core-completion` 基于 FE-F2 `734990c`，存在上一轮尚未提交的规格/README/记录改动和用户原始 FE-F3A 包；这些均保留，不新建丢失规格的工作树。
- 实施顺序记录于 `docs/superpowers/plans/2026-09-27-fe-f3a-project-core.md`。尚未运行生产迁移，也不推送/合并。
- 1.1/1.2：五个模型和增量迁移文件已加入；FE-F3A 表结构测试先因缺表失败，新增模型后单测通过。下一步在隔离库验证迁移 up/down/up，并实施事件/归档语义。
- 1.3 部分：隔离临时 SQLite 已完成 `e5fef2000001 → f3a000000001 → e5fef2000001 → f3a000000001`；仓库初始迁移会按当前模型预建新表，因此 FE-F3A 迁移使用既有的表/索引存在性防御。尚未在该迁移链路里插入并回读 FE-F2 历史行。
- 2.x 部分：项目创建/编辑/归档、单元创建/编辑/替换/删除、项目工作流保存、项目来源角色默认保存、快照与关联产物写入 ProjectEvent；当前事件/项目及 FE-F2 Data/Output 定向测试 11 passed。项目归档后新旧 Run 修改权限加了保护，后续仍需更完整回归。`project_events.py` 的稳定常量与 2.5 全路径验证尚未完成。
- 3.1/3.2：Brief 已有当前/历史/详情/追加版本 API；保存按 expected_revision 对比，唯一键并发冲突回滚为 409，事件同事务写入。先验证无路由 404，再实现后定向 4 passed；前端尚未接入，完整字段校验和并发双会话验证待做。
- 4.1/4.2/4.4：项目 Source 引用可附加、幂等重复、解除并重新激活，旧全局 Source 保持可读；Fact Boundary 可读取当前/历史并只绑定有 checksum 的冻结 FactPack，revision 冲突返回 409。相关测试先 404 失败后定向 6 passed。项目级 Clone/Freeze-and-bind、全局 FactPack 服务共用规则、前端 Evidence 仍待实现。
- 4.3/4.5：全局与项目级 FactPack Clone/Freeze 现复用 `factpack_service`，项目级 freeze-and-bind 要求当前边界的直接草稿子版本，冻结、审计和边界修订同一数据库事务。克隆→冻结→新边界→旧历史可读的定向测试先失败后通过；FE-F3A+FE-F2 项目定向 13 passed。前端 Evidence 仍未接入。
- 后续实现已接入 Brief、Evidence、Assets、Overview、Versions、Activity 后端与项目七标签前端；此前后端全套 289 passed、前端 build 通过，最终门禁待重跑。新归档项目回归证明历史 Run 可读、旧裸 Run mutation 与项目 mutation 均拒绝。
- 收尾修正：项目 PATCH 不允许绕过专用归档接口直接设置 archived；生产工作台共享素材按项目上传/系统引用/工作流产物区分，图文与视频“已生成”列表只显示工作流产物。
- 定向补测通过：项目 PATCH 直接归档返回 422；注入上传事务内事件失败时 Material、MaterialRevision、项目引用均回滚，预先存在的同哈希共享字节保持不删。FE-F3A 定向测试 12 passed；此前全套 290 passed，最终变更后需再跑。
- Evidence 返回项目页后可从 FactPack 列表恢复当前边界的最新草稿，避免“编辑后无法冻结并绑定”；Matrix 已提取为独立 Tab 组件并隐藏已归档项目的矩阵写入按钮。前端构建再次通过（主 bundle 1,057.94 kB，原有体积提醒）。
- 隔离迁移库带真实 FE-F2 ContentProject、ContentUnit、WorkflowRun(checksum) 完成 e5→f3a→e5→f3a；三条历史行与 checksum 回读一致。未触及生产库。
- 隔离浏览器验收：创建项目、Brief v1/v2、文本 Source 创建并关联、冻结 FactPack 绑定、项目边界 Clone→跳转编辑→返回恢复草稿→冻结并绑定、PNG 项目上传、同版本再次引用幂等、Overview/Versions/Activity 真读模型、七标签逐一刷新均成功。验收使用独立临时 SQLite 与 127.0.0.1:18081/15174。
- 归档状态的普通 PATCH 旁路已同步堵住：Project 必须走 DELETE→archive，ContentUnit 必须走已有删除/归档语义；避免写成通用 updated 事件或绕过历史保护。
- 新定向用例先发现 Overview 把 `waiting_human` 单元误归为普通生产；已补待人工聚合，并区分最新 Run 的 stale/failed/waiting_input 节点状态。Brief 同内容显式保存会形成新修订、checksum 相同。FE-F3A 定向现为 13 passed。
- Overview 前端将风险/人工状态代码翻成用户可读中文，并显示待处理项对应单元；不在 React 重算阶段。
- 新增跨所有项目核心读模型的归档/跨所有者回归：归档后 Brief、Boundary、Assets、Versions、Activity、Overview 可读，Source 解绑不改已冻结边界；另一用户均 404，归档项目的新写入均 409。FE-F3A 定向现为 14 passed。
- 当前最终本地门禁：后端全套 293 passed / 5 warnings；前端 `npm run build`（含 TypeScript）通过，主 JS 1,058.31 kB 非阻塞提醒；OpenSpec strict、`git diff --check`、本次后端文件 Ruff F 检查通过。独立代码复核已发起，OpenSpec 归档与提交保持等待。
- 定向回归进一步验证 Clone 后编辑草稿再冻结会产生不同 checksum 且旧 FactPack item 数不变；重复 Source/Material 关联不重复写项目事件。新增断言后 FE-F3A 定向 14 passed；全套门禁仍需最终复跑。
- 在 FE-F2 素材真实字节/Attempt 回归上增加 FE-F3A 并集断言：同一 MaterialRevision 同时由 workflow 与 system_reference 合法展示，两个稳定 key，数据库仍只有一条 Revision；定向测试通过。
- 独立审阅首次结论为不准归档/提交，指出 5 个重要缺口。已逐项修：新哈希上传失败单独记录可核对的 `material.upload_orphan_candidate` AuditLog，不删除共享字节；归档 Evidence 隐藏创建/绑定并在全局 Source 创建前再次核对项目状态；项目 PATCH 不能修改 objective；显式素材回传 MaterialRevision 来源信息；Evidence 增加当前冻结 FactPack 条目区，Brief 历史可展开全文。定向单测与前端 build 已针对相关修改通过，最终全套和复审待跑。
- 隔离浏览器归档后复验：Evidence 的 Source 创建/解绑和边界绑定控件均不出现，事实条目和边界历史仍可读；Brief/Assets/Matrix 的项目级写入控件不出现。
- 二次复审又发现 orphan candidate 的 `AuditLog.entity_id` 超过 PostgreSQL 的 50 字符限制、且未被清理消费。现只在该列存 50 字符哈希前缀，完整哈希留在 detail；既有 `run_retention` 以一日宽限、每批上限处理候选，先检验路径与已提交 MaterialRevision/DraftMedia/AssetMedia 引用，再删除无引用字节或保留共享字节。未处理候选不受普通 90 天 AuditLog 清理影响。新增新文件删除/共享文件保留/过期候选保留测试均通过，复审待重跑。
- 最新本地门禁：后端全套 294 passed / 5 warnings，前端 TypeScript/Vite build 通过（主包 1,060.65 kB 非阻塞提醒），OpenSpec strict、`git diff --check`、涉及后端文件 Ruff F 检查通过。独立审阅正在复核最后两个上传清理边界，9.6 尚未完成。
- 第三轮审阅指出清理任务未注册、同哈希上传与清理可能竞态。已注册现有 beat 配置的 `retention_sweep`；MaterialRevision 写入持有哈希分片文件锁到外层事务结束，保留流程在引用检查与 unlink 期间持同锁，并逐候选提交。新增任务注册与跨线程锁释放回归；清除本机异常 `NO_PROXY/no_proxy` 后后端全套 296 passed / 5 warnings，前端 build、OpenSpec strict、diff-check、Ruff F 通过。最终独立复核进行中，仍未归档/提交。
- 独立复核最终 PASS、无剩余 blocker；9.6 已勾选。用户确认同步主规格后，OpenSpec 已归档至 `openspec/changes/archive/2026-09-27-fe-f3a-content-project-core-completion/`，同步两项旧能力规格并新增 FE-F3A 主规格（9 added / 3 modified）；三份主规格 strict 均通过。待核对暂存快照并提交本地分支；不推送、合并或部署。

## 2026-09-27：FE-F3A 规格复核与归位（仅文档）

- 以 `734990c` 为基线创建 `codex/fe-f3a-project-core-completion`，把用户提供的结构化 FE-F3A proposal/design/tasks/三份 spec 归入 `openspec/changes/fe-f3a-content-project-core-completion/`。原始目录、ZIP 与合并文档保持原状，便于追溯。
- 对照 FE-F2 实际项目、单元、Source、FactPack、MaterialRevision 和迁移头复核；旧 Source/FactPack/Material 为全局资源，项目引用不等于获得资源所有权。现有项目 DELETE 可物理删除无单元项目，与新增 append-only 活动/子表冲突，已在规范中改为归档语义。
- 已补强事件同库事务、Brief/Fact Boundary 并发冲突转 409、Source/Material 唯一绑定重新激活、素材字节写入后的失败清理边界。业务代码和数据库未改动；`openspec validate fe-f3a-content-project-core-completion --strict` 通过，纳入新增规格文件后的 `git diff --check` 通过。
- `tasks.md` 仅将分支/规格门禁 0.1–0.2 标记完成；所有实施任务仍待明确 apply 授权，不因 4/4 规格产物齐全而视为功能已完成。

## 2026-09-27：FE-F2-R1 复核通过，归档与本地提交

- 外部复核已明确给出 `REVIEW_PASSED`，范围仅限 R1 五项收尾问题，不把结论外推为完整 PRD/V1 或生产验收。
- 已勾选 OpenSpec 6.3；按用户授权归档 `fe-f2-persistent-production-workflow` 并提交当前 `codex/fe-f2-persistent-production-workflow` 分支。最终命令输出及 commit hash 以本轮实际执行结果为准；不推送、不合并、不部署、不运行生产迁移。
- 归档命令完成：`openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/`；主规格更新 `fe-f0-f1-project-experience` 一项、新建 `fe-f2-persistent-production-workflow` 八项。归档后重新验证：后端全量 279 passed、前端 build 通过、12 份主规格 strict 校验通过、`git diff --check` 通过。归档工具给 FE-F0-F1 主规格增加的末尾空行已修正；待暂存快照核对及本地提交。

## 2026-09-27：FE-F2-R1 review 收尾

- 用户确认：仅保存项目覆盖但尚无 Run、快照、产物的单元，身份/形态/工作流可原地修改；一旦有执行历史，替换为新单元并归档旧单元。
- 已补 OpenSpec 场景并落地：unit-scoped effective-workflow 保持 Designer 与 pinned version 一致；矩阵恢复身份/形态/工作流重绑编辑，历史单元归档且可回读；模板可移植性仅在运行时解析的 config 中参数化；Step 保存 Kind；失败 rerun 不携带旧输出。
- 定向测试先红后绿；全量后端 279 passed，前端 `npm run build` 通过。首次全量出现 1 个新增测试夹具不符合模板 config allow-list，修正夹具后复测通过。OpenSpec strict 与 `git diff --check` 通过；主 JS 包体积警告仍在。归档、提交、推送和生产迁移均未执行，等待 R1 小补丁外部复核。

## 2026-09-27：FE-F2 apply

- 当前分支 `codex/fe-f2-persistent-production-workflow` 从干净的 `main@c044085` 创建；先前脏工作树已由其他提交收敛，本轮不搬运旧改动。
- OpenSpec `fe-f2-persistent-production-workflow` 是 spec-driven，0/21 任务完成；已建立实施计划，先处理持久化与旧 API 权限。
- 基线：`test_workflows.py` 10 passed，前端 `npm run build` 通过（主包体积警告）；Alembic head 为 `d4audit00004`。没有执行生产迁移或发布。
- OpenSpec 1.1：新增项目/单元/内容 Persona、两类工作流绑定、DataSnapshot、项目产物关联与可空 `WorkflowRun.content_unit_id`；定向模型测试先红后绿。隔离临时 SQLite 上从旧版本升级到 `e5fef2000001`、回退到 `d4audit00004`、再升级均成功。未修改已有正式数据库。
- OpenSpec 1.2/1.3：项目、角色、单元 CRUD 与创建者隔离已接 API；旧 Workflow 的 run/attempt/重跑/人工完成/取消/列表和 definition 列表、clone/publish/raw create-run 均接统一项目权限。项目工作流版本增加持久 owner/scope，阻断绑定变更后的遗留旁路。`test_fe_f2_projects.py` 与 `test_workflows.py` 共 14 passed；隔离 SQLite 全量迁移至新 head 成功。下一步补工作流校验和双保存。
- OpenSpec 2.2：项目覆盖另存生成不可变 Workflow 新版本，绑定修订号比较并在失配时返回 409；旧 Run 保留版本/checksum。角色默认另存入口已有初版，但可移植性 allow-list 仍须收严，2.3/2.4 暂不勾选。
- OpenSpec 3.1–3.3：Data Source 六类描述符及断连状态已接服务端；Studio Source 只读快照限制 20k 字、保留 source/version/lineage/checksum。项目 Run 经原引擎记录 Attempt；相同快照不使下游 stale，变化只标记依赖后代；断连插件在启动前被拒绝。快照可按所属单元读取。当前项目/工作流/Data 定向回归与旧工作流回归共 21 passed。
- OpenSpec 2.1/2.3–2.5、4.1：六类节点校验、条件/失败策略及映射参与真实执行；角色默认对同项目/单元 ID 使用上下文占位，对数据 source_ref 用运行参数占位，其他绑定值拒绝。已有 Draft、批准 Candidate 和真实 MaterialRevision 才能被关联项目。定向测试包含生成图实际字节落 MaterialRevision→共享池、历史 checksum、旧 API 旁路和副作用重跑。
- 前端当前接入真实项目 CRUD、角色默认版本选择、单条画布、Inspector、双保存和实际 Run；Mock 单独保留在 `/projects/demo`。隔离 SQLite `e5fef2000001` + 本地 18080/15173 联动浏览器实测：创建项目/身份/单元 → 保存 System 工作流 → Run succeeded/Attempt 输出 → 刷新后仍可读取。没有触碰原 8000 端口上的进程或已有数据库。
- 2026-09-27 续作：隔离 API 旧进程导致 `/outputs` 404，重启后为 200；文字/图文/视频三形态工作台均在浏览器读到持久单元。AI Provider/Model 只允许绑定后端当前执行路由，保存和启动均验证，不暴露密钥；UI 已选中 mock/mocked model 并显示在 Inspector。素材关联增加真实文件与哈希复核，缺失字节不入池。定向后端 30 passed、前端构建通过（包体积警告仍在）。
- FE-F2 最终本地验收：角色默认 v1 另存后，后续单元固定新版本，原单元仍固定项目覆盖；带 snapshot_id 的默认模板保存 422 且绑定不变；Notion 断连启动 409，隔离库对应 Run/Snapshot 均为 0；非所有者走遗留裸 run API 为 404。浏览器验证文字/图文/视频壳层及项目共享素材抽屉。后端 274 passed（需清除本机异常 NO_PROXY/no_proxy）、前端 build 通过、OpenSpec strict 与 diff-check 通过；待规格同步/归档。
- 最终双保存按钮复核：已保存项目覆盖且页面无未保存修改时，“另存为角色默认”现在仍可点击；服务端可移植性 Gate 继续决定能否成功，项目绑定不会被此操作改写。待最新前端构建复核。
- 隔离库保存项目 v2 后发现 Run #1 的冻结定义与当前草稿不同；已修正画布为运行模式显示 Run #1 原节点/成功状态，设计模式显示项目 v2 新节点且不混用旧状态。最新前端 build 通过。
- 全量后端测试 253 passed / 12 failed；12 项均是旧 DSH 代理端口 `:1` 导致的 `httpx.InvalidURL`，与本轮定向链路一致未扩大。前端 `npm run build` 和 OpenSpec strict 通过，主 JS bundle >500 kB 警告仍在。FE-F2 尚有专属三形态界面、Provider/Model/Tool 选择语义及最终本地验收，不可归档。

## 2026-09-27：FE-F2 正式 review 补强（未 apply）

- 已核对旧 Workflow API：除裸 run 详情、attempt、retry、节点重跑和人工完成，运行列表、取消、定义列表/clone/publish 及 raw create-run 也需要纳入同一项目权限边界。
- 已在 FE-F2 proposal/design/spec/tasks 补入统一授权、角色默认模板服务端可移植性 Gate、视觉顺序与依赖图分离、以及现有测试基础上的定向回归覆盖。
- 用户明确要求 FE-F2 新增回归测试，因此旧任务中“不新增测试代码”的限制已在该变更任务条款中替换；本轮只订正规范，尚未新增或运行测试、业务代码和迁移。
- 新版 `openspec validate fe-f2-persistent-production-workflow --strict` 和 `git diff --check` 均通过；未将规范校验误当成功能验收。

## 2026-09-27：FE-F2 V5 规格校准（未 apply）

- 用户确认 FE-F2 须真实持久化“角色 × 内容形态”默认工作流新版本，并供后续 Content Unit 选择；项目覆盖与角色默认保存须分离。
- 已订正 FE-F2 proposal/design/specs/tasks：六类节点、拖拽排序、可扩展 Data Source Plugin 六类来源及断连不可执行、快照 stale、项目共享素材产物关联。
- `openspec validate fe-f2-persistent-production-workflow --strict` 与 `git diff --check` 均通过；本轮未运行应用构建，因没有改业务代码。
- 仅修改规范和记录；没有业务代码、迁移、真实 Connector 或远端动作。校准后的完整提案仍待用户确认后才可 apply。

## 2026-09-27：FE-F0-F1 复核补丁

- 主规格缺口已补：异常项目的总览与内容矩阵显示五种状态说明；生产页原有说明仍保留。
- 本轮 `npm run build` 成功；浏览器已看到异常项目矩阵和总览的状态说明。正在隔离 FE-F0-F1 暂存范围，历史 API/迁移和 FE-F2 提案不纳入本次提交。

## 2026-09-27：FE-F2 提案（未实施）

- 用户明确工作流调试器须后端持久化并真实执行，不能只做前端 mock。
- 已核对现有 Workflow/Run/Step/Attempt 与重跑接口；它们仍以 Topic/渠道组织，FE-F0-F1 项目数据仍在浏览器 `localStorage`。
- 已建立 `fe-f2-persistent-production-workflow` 的 proposal/design/specs/tasks，`openspec validate --strict` 通过；等待用户确认，未运行 apply、未改业务代码或数据库。
- 建议以新增项目/内容单元持久化和项目级不可变工作流版本复用现有引擎；此处原“首个 Data Source Plugin”表述已被上面的 V5 校准覆盖：契约可扩展，首个可执行适配器才是 Studio Source。

## 2026-09-27：FE-F0-F1

- 已确认当前工作区为 AIContentStudio；North Star V2、V5 原型、前端契约和 HANDOFF 均已核对本切片范围。
- OpenSpec `implement-fe-f0-f1-product-shell` 的提案、设计、规格和任务齐全，严格校验通过并已实施、归档。
- 当前工作树已有大量用户改动，本切片只改前端相关文件和本任务文档。
- 已建立类型化本地模拟项目、内容单元和素材版本数据；含健康、异常两类项目，扩展状态徽标且沿用已有弹窗/抽屉。
- 已实现九入口主导航、项目列表、七个 URL 标签、内容单元增删改、本地持久化、共享素材抽屉和生产入口；`npm run build` 已通过，Vite 提示现有主包较大。
- 浏览器实测：项目列表、七标签、内容单元新增/编辑/删除、生产入口、共享素材来源筛选和异常样本的受阻/已过期/待核对区分可见；删除改为站内确认弹窗，验收样本已清理。
- 最新核验：`apps/web` 的 `npm run build` 成功；`openspec validate implement-fe-f0-f1-product-shell --strict` 和 `git diff --check` 成功。前端无单独 lint/test 脚本，本轮未新增测试代码。
- 交付边界：项目数据只在浏览器本地演示，未接后端、未增加迁移、未实现 FE-F2 工作流调试器；旧审核/素材页改用 `/legacy/review`、`/legacy/assets` 别名访问。
- OpenSpec 已归档到 `openspec/changes/archive/2026-09-27-implement-fe-f0-f1-product-shell/`，新增主规格 `openspec/specs/fe-f0-f1-project-experience/spec.md`。

## 2026-09-24：PRD 三渠道补齐提案

- 用户明确 `03_ai_content_studio_PRD.md` 是产品长期目标，并纠正三渠道误读：完整 V1 还包括百家号等 11 个文章/图文/社交平台，另保留抖音脚本。
- 已核对抖音和小红书具备旧生成/导出入口，但缺 M1 受控成品交付；其余长文/问答/社交平台缺原生适配。已把完整范围补入 PRD §3.1，正在修订 OpenSpec `complete-prd-v1-channel-deliverables`；当前仅规划文档，未改业务代码。
- OpenSpec 严格校验通过，4/4 产物齐全；`git diff --check` 通过。下一步是用户确认具体提案，然后按 OpenSpec 流程实施与归档。

- 已配置固定域名连接：`kayoyo.top`
- 已创建连接器：`Codex with ChatGPT · AIContentStudio`
- 已完成 ChatGPT 授权与安全配对
- 已为新 ChatGPT 账号 `Austin` 重新完成同一连接器授权
- 已绑定项目「AIContentStudio」，记忆为「仅限项目记忆」
- 已完成工作区读取验证，返回当前工作区 `AIContentStudio`

## 2026-09-22：V1 蓝图对齐

- 已找到指定原对话及用户最新需求；当前阶段仅做规划。
- 本地连接检查通过，复用原连接与浏览器，不重新配置。
- 正在核对代码并准备三轮讨论；尚未修改业务代码或运行对外发布。
- 源码核对完成，证据已记录到 findings.md；生成/审核/素材/工作流的可复用点及缺口已区分。
- 已形成 `docs/AI_CONTENT_STUDIO_V1_ALIGNMENT_PLAN.md` 讨论草案，等待 ChatGPT 回复及用户分发验收选择；正在做独立文档复核。
- 已补读原对话 R2 完整附件，并将需求编号映射到实施阶段；本轮尚未执行业务能力验收。
- 独立复核指出候选采纳及 Topic 创建顺序遗漏，已修正文档；ChatGPT 第一轮仍在生成，未重复发送。
- README 已增加下一版规划入口、当前未实现项及静态核对边界，原有用户改动保留。
- 文档二次复核要求将单目标交付可靠性前置；已补为自动建稿启用门槛，阶段 C 只做多目标扩展，待最终复核。
- 独立文档最终复核通过；两项问题已闭合。ChatGPT 三轮讨论尚未完成，不能据此宣称共同结论。
- 后续刷新发现首条 INIT 未保存；此前“正在生成”仅为页面提示，不构成有效讨论证据。恢复聊天模式后重新请求工作区/README 读取，页面再次报错，单次重试仍失败。当前连接检查全部通过，未重建连接器，正在核对原会话是否可继续。
- 经已保存会话及项目列表恢复原对话后，仍未取得新答复。已保留原对话和协作检查点，草案明确标为未完成 ChatGPT 讨论；本轮仅修改规划文档及 README，未运行生成/发布、未新增测试、未执行 OpenSpec 实施或提交推送。
- 用户确认可以回复后继续：原对话可见用户新消息“1”；已点击发送简短的当前工作区/README 核验请求，页面显示思考中。尚未取得实际文件读取结果，不将用户可发送消息等同于连接器核验成功。
- 本次核验成功：ChatGPT 返回工作区 AIContentStudio，并引用 README 第 3 行当前三渠道链及第 9–13 行新增 V1 草案说明；原会话恢复文件读取。已将本任务协作地址绑定到指定蓝图对话，开始三轮规划讨论。
- 第一轮规划请求已发送并可见；ChatGPT 已确认只规划，页面出现事实冻结、素材、选题及审批源码核对进展，尚未形成最终方案。
- 第一轮完整 PLAN 已收到并读完，新增源码观察已定点复核；第二轮设计挑战已发送。拟前置双渠道受控复用与最小反馈，尚待第二轮收敛及最终文档审阅。
- 对齐草案已补录第一轮结论与第二轮讨论问题，阶段正文待第二轮完整答复后统一修订；依旧未获得实施授权。
- 第二轮完整 PLAN 已收到并读完；已将首批 M1 与后续 A/B/C/D 分开，补类型化证据、语义检查覆盖、稿件期素材、双层审批、公开包隔离和旧调用入口防绕过。远端建稿独立准入，本轮不启用或停用任何业务功能。准备第三轮及新版独立复核。
- 新版独立复核指出 X Articles 范围及逐形态验收不够明确，已修正为按“平台 × 内容形态”验收，M1 仍仅做 X 线程，不以线程成功替代 X 全覆盖。ChatGPT 第三轮审阅进行中。
- 第三轮完成：ChatGPT 完整读取修订方案和 findings.md，判定规划 DONE，无严重修正；仅提醒历史类型迁移、M1 边界及重复/中断/未知结果验收。已补录这些提醒，明确本地防重不承诺人工或平台端绝对仅执行一次。
- 新版独立复审 Approved；三轮规划已形成建议共识，首批渠道与自动化下限仍待用户确认。没有创建 OpenSpec 提案，没有修改业务代码、生成测试代码、调用模型生成/发布、提交或推送。
- 收尾核对：已跟踪变更的差异检查通过；新增规划文件逐项检查未报告空白格式问题（与空文件比较的退出码 1 表示新增差异）。用户原有 PRD、澄清稿和 docs/superpowers/ 保留，未暂存或提交。本轮验证仅限文档和连接读取，不构成功能验收。
- ChatGPT 最终复核已确认规划层面 DONE：M1 采用类型化证据冻结、母稿版本、公众号 + X 线程成品包、人工交付回执与反馈；不把公众号自动草稿作为首批硬门槛。
- 已创建 OpenSpec 变更 `add-evidence-bound-article-handoff`，完成 proposal/design/specs/tasks 四类产物；严格校验通过，apply 前任务为 0/24。
- 当前执行边界：只实现本地成品包与人工回填，不调用远端发布 API；尚未修改业务代码、运行功能验收或归档 OpenSpec。
- 已开始执行 OpenSpec：完成数据模型扩展、X Thread 最小形态、增量迁移、类型化证据快照写入、母稿导入/适配、候选哈希、人工目标/本地包/回执/反馈接口，以及 M1 旧公众号远程副作用的部分工作流闸门。
- 本地迁移已执行到 `d31415926535`；API 模块语法检查、OpenAPI 路由读取、`git diff --check` 通过。新增人工交付包明确不调用平台 API，也不上传对象存储。
- 现有测试：项目虚拟环境中 129 通过、12 失败；失败集中在既有 DSH 配置值 `:1` 被 httpx 当成非法端口，未经过本次新增链路。系统 Python 的 `make test` 另因缺少 `pypdf` 在收集阶段失败。
- M1 本地实现与验收完成：类型化快照、母稿/适配稿、DraftMedia、完整候选批准、人工目标、ZIP 成品包、回填、反馈和旧工作流远端调用闸门均已落地。公众号实际封面字节被写入 ZIP 并按批准哈希校验；X Thread 路径已单独验证。
- 独立复核提出的四项问题已修复：ZIP 包含实际媒体、终态不因重新取包回退、目标与回执在并发重复请求下回读、目标只能由授权操作人处理；迁移先回填可关联历史 hash，无法关联的历史行保持 legacy/ineligible。
- 公开使用权限可以只撤销不能恢复；素材或冻结证据撤销会使未完成目标进入 `blocked`，已人工确认历史不被改写。
- 验证通过：空 SQLite 迁移到 `g31415926535`、`test_core_pipeline.py` + `test_workflows.py`（23 passed）、前端生产构建、严格 OpenSpec 校验、空白差异检查，以及临时本地数据的公众号实际媒体 ZIP / 账号隔离 / 终态保护 / 权限撤销链路。
- 全量测试仍为 129 passed / 12 failed；12 项均为既有 DSH 状态探测把环境代理地址 `:1` 传给 httpx 的非法端口，未扩大本次范围修复。
- ChatGPT 最终代码复核请求已发送到原对话；浏览器调试连接当前无法附着，因此暂未能读取其回复。OpenSpec archive 因此保持未归档。
- 已补完陈旧候选拒绝与人工结果未知（`reconciliation_needed`）的独立本地验收；同一未知回填重复提交不会新增第二条回执。
- ChatGPT 最终代码复核指出旧工作流默认仍生成公众号草稿节点；已将模板默认改为本地导出，并为遗留远端草稿增加显式开关与服务端闸门，M1 母稿仍不可进入该路径。
- ChatGPT 对上述修复返回 DONE；已完成 `add-evidence-bound-article-handoff` 的 OpenSpec 归档，归档目录为 `openspec/changes/archive/2026-09-22-add-evidence-bound-article-handoff/`。
# 2026-09-27：连接器故障检查

- C2C 更新检查无新版本；授权白名单已配置。
- 固定域名配置正常；`C2C_TUNNEL_PROTOCOL=http2` 已在当前环境及 `~/.zprofile` 配置。
- 用户确认四种独立读取均返回 `internal error`。进一步外部复核发现公开连接返回 530，且该工作区的健康连接数为 0；协议配置正确。
- 已执行 `c2c restart --tunnel`。复核通过：HTTP/2 正确、健康连接数大于 0、公开 MCP 未授权请求返回预期 401。
- 待用户在 ChatGPT 中重试 `workspace_info`，确认连接器端到端恢复。
- 2026-09-27 再次复查：本地诊断无修复项，外部探测仍返回 401，HTTP/2 与健康连接数正常；未重复重启。状态输出含一条 Cloudflare edge 地址警告，但当前传输探测通过。
