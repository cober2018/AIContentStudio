# Persona Creative Studio 流程框架交接

## 2026-10-09 使用配置回执（当前）

用户明确同意补齐配置，已通过现有接口保存并即时生效，无业务代码或启动方式变化。当前仍146/156、10项开放。

| 项目 | 实际结果 |
| --- | --- |
| Chat预算 | max_tokens=8192、max_items=3、timeout_seconds=120；候选上限不是新增并发请求 |
| 正式配置修订 | 5→6（chat预算）→7（一次音色目录同步）；API正式回读一致 |
| 音色目录 | MiniMax既有CLI一次返回273项，页面全目录搜索/语言/收藏入口可见，最多展示100匹配项；未生成试听/自动选声，不声称所有克隆ID均返回 |
| 文字就绪 | 科技Persona2和生活Persona3均ready，仍默认gemini-3.8-flash-high；仅配置就绪，不是新真实生成验收 |
| 保全 | 5,162其他行逐hash相同，原Provider/Key/API/default/profile等值，旧image/TTS/ASR限额与67素材/32,992,851字节/runtime.env不变；schema仍crs |
| 私有备份 | `backups/persona-config-20261009.LayCFa/content_studio.db`在线备份integrity=ok；同目录hash/receipt及维护脚本权限收紧，既有完整配套素材备份保留 |
| 操作范围 | 仅chat配置＋一次目录读取；零CPA/生成/试听/Unknown重发、迁移、重启、持久测试或sync/archive/commit/push |

首次维护PUT漏带现有Plugin引用的profile，被422/plugin_binding_missing拒绝且无写入。随请求携带其精确既有声明/binding后，原profiles等值和校验通过，CAS成功；不是放宽接口或盲目重试供应商。

Audio仍需你从已登记目录明确选择voice ID并在项目选Recipe；选声后实际执行仍走原runtime/bytes/hash/QC门禁。Graphic需项目Master/精确renderer scope。本次不扩大原image1候选/TTS10秒等限额，也不把目录当完整成品质量证据。

本轮新鲜门禁：OpenSpec strict38/38、git diff --check exit0，8个范围文档无trailing whitespace，私有备份Gitignored。既有fullbackend/Web结果是历史，配置操作不重复生成或全量验收。实际技能OpenSpec apply、systematic-debugging、完成前核验。

## 2026-10-09 本机启用回执（配置补齐前历史）

**146/156，10项开放；正式角色初始化完成，不等于全部默认生成已就绪。** 用户授权配套备份、刷新现有API、初始化两个角色/默认流程和关键功能冒烟；不扩展到新Provider调用、使用配置覆写或规格生命周期。

| 项目 | 实际结果 |
| --- | --- |
| SQLite/素材备份 | 私有`backups/persona-enable-20261009.DdDdKc/content_studio.db`与完整`media-root/`；67文件、32,992,851字节，逐hash一致；引用文件核验无失败 |
| 原有数据 | 5,147条旧行逐hash保全，正式素材及runtime.env不变；schema `crs000000001`，身份字段保持null/inert |
| 科技角色 | Persona2 / revision1；Text Workflow7、Graphic8、Video9，各v1 |
| 生活角色 | Persona3 / revision1；Text Workflow10、Graphic11、Video12，各v1 |
| 幂等 | 再次初始化均already_initialized；无新增/覆写，仅本次新增2角色、2修订、6Workflow及6默认关联 |
| 运行服务 | 原launchd API/Worker恢复，API `/api/v1/health/ready` 200/ready=true；Vite在127.0.0.1:5173运行，未新增持久启动体系 |
| 页面冒烟 | 两角色独立风格/四形态配置、默认Workflow、生产/Recipe选择器、原生媒体及ChatGPT手动提示词/上传入口可见，无console error；未采用新流程或修改旧Master |

### 使用配置待确认（历史；已由上面的独立授权补齐）

自动续行已只读核对现有代码和正式配置：现有保存服务已经支持chat预算与revision CAS，音色目录刷新已有MiniMaxCLI入口（10秒等待、零重试、不生成音频）。建议待人工批准后一次新增chat限额：8192输出tokens、最多3候选、120秒等待，并读取/登记现有音色一次；不增加适配器/持久表，不改Provider/Key/默认Gemini或现有媒体额度。候选上限不等于新增并发请求。目录登记也不替用户选择声音，不生成试听。此建议尚未写入正式配置，上一条授权询问仍待人工回答。

- 正式routing revision5没有`policies.limits.chat`，文字/独立规划fail closed；不是CPA网络测试失败，本轮没有调用模型。
- 音色目录为空，两个Audio profile尚无供应商voice ID；风格名称不冒充具体音色。
- 保持原image最多1候选、TTS最多10秒、120秒等待限额，不为启用静默扩额度；URL/Key/默认Gemini保持。
- MiniMax只读inventory的凭据continuity未核验不等于凭据已失效，明确执行时仍需已有runtime核验。
- 新Persona不自动替换旧项目/Unit的身份或Workflow；音频Recipe仍在项目中明确选择，不新建Audio Master。

已关闭5.8/22.7。余下10项是新增持久覆盖13.6、两角色Graphic/Audio完整链路4项、两个人工rubric、完整成品证据21.3、独立质量22.6和生命周期22.8。用户已接受的科技/生活文字与生活三卡保留为对应样本确认，不扩大成完整音频/QC/所有质量验收。

本次新鲜文档门禁：OpenSpec strict38/38、diff-check exit0；实际任务重计146完成/10开放。无新业务代码/永久测试、Provider调用、Unknown重发、迁移、正式素材/旧行/配置改动、sync/archive/commit/push。只做本次启用与页面/接口/hash冒烟，不重跑完整backend/构建或追加审美生成。实际技能：OpenSpec apply、systematic-debugging、verification-before-completion；既有启动/目录/依赖不变。

## 本次确认

科技文字样稿、生活文字编辑稿和既有生活三卡已由用户确认可以，后续提示词/风格由用户调整。这个确认只覆盖对应样本，不等于完整图文、音频成品/QC/独立质量验收。正式Persona初始化另据上面2026-10-09回执完成。

## 已接通的产品骨架

日常入口为 `ProductionWorkspace`，统一承接：

```text
Persona / Identity
  → Creation Recipe
  → Stage Contract 与 Effective Preview
  → 本次调节 / 实际 Attempt
  → 中间结果接受
  → Content Master
  → Checks
  → Candidate / Review
  → Local Package
```

工作台中的独立承接入口为：

- `CreationRecipePanel`：阶段选择、可调字段、有效 Prompt/模型/方法预览、执行、接受/修改/拒绝和反馈。
- `ContentMasterPanel`：Master 编辑、精确素材/证据引用和显式保存。
- `GraphicStudioShell`：Visual Direction、Card Plan、确定性排版、精确素材绑定、渲染输出和 Graphic QC 承接。
- `ProviderMediaPanel`：生图/TTS 等生成任务的准备、明确执行、结果接受和素材库回接。
- `StageDomainResultPanel`：图文、音频、ASR 等领域 Stage 的结果查看与接受。
- `ChannelVariantsPanel`：基于已保存 Master 生成渠道专属变体，不改写 Master 或流程草稿。
- `CreativeExecutionPanel`：专业外部执行包、回传结果和人工接受后的素材回接。

图文链路：

```text
已接受文字/中间结果
  → Visual Direction
  → Card Plan
  → 确定性 Compose
  → Graphic Master
  → 真实渲染 MaterialRevision
  → Graphic QC
```

音频链路：

```text
已接受文字/脚本
  → Spoken Adaptation
  → Voice Direction
  → TTS 任务
  → 接受音频 MaterialRevision
  → Audio QC
  → 可选的明确执行 ASR 对稿
```

## 当前仍分开的验收门

- 图文和音频的真实 Provider 成品尚未在本记录中宣称通过。
- 真实成品需要单独记录 provider/model/profile/runtime、Prompt/config hash、artifact hash、确定性 QC 和人工 rubric。
- 正式SQLite中的两个Starter/default workflows已获授权并完成；OpenSpec archive、canonical sync、commit/push仍是未获授权的独立生命周期动作。
- 不使用旧 Text 检查结果冒充生活编辑 Master 的新检查结果；不自动发起新的模型请求。

## 前序门禁（历史，启用后的校验另见当前回执）

- OpenSpec strict：38/38，通过。
- `git diff --check`：通过。
- 这三条是本交接文档初版的门禁记录，不能冒称本次重跑；2026-10-09启用仅按授权新增角色/流程并刷新原服务，旧行、素材和模型配置保持。
