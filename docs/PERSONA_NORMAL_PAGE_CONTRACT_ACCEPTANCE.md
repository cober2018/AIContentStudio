# Persona Creative Studio — 普通页面跨形态合同验收

## 当前结论（2026-10-07）

`add-persona-creative-studio` 当前 **122/147，剩25项**（6.4已独立复核收口，19.5已完成prepared-handoff功能验收）。以下Text/Graphic/Audio普通页面和whole22.4/22.5证据保留原批次归属，不冒称本次重跑；这不是全部规格完成、真实创作质量批准或正式角色初始化授权。

后续Video先通过默认四阶段隔离API37点与比例修复/233项相关回归，再实际完成两个角色普通页面21点、pageErrors=[]。脚本/镜头不创建假Master；明确接受video.master.v2和director.video.v1包，刷新不生成新结果。只读隔离库确认2Master/2Package、零Execution/输出/Provider任务/Material/Candidate，包及接受投影hash各自一致。19.5仅关闭prepared交接功能，不声称真实脚本/最终视频质量；追加独立窄review此前额度耗尽无结论，不记录新APPROVE。完整命令/hash和权限边界见[后续执行回执](../openspec/changes/add-persona-creative-studio/progress.md)。

Video页面证据另存 `/private/tmp/persona-video-normal.1BFel2/report.json`（21checks），最终数据库 `page-acceptance.db`。两张 `*-director-acceptance.png` 已实际查看，显示包已接受但 execution 未准备、not_dispatched。临时API18335/Web15335已停止并确认无监听；正式服务未操作。真实Text/Graphic/Audio、固定rubric和正式初始化仍分别开放。

本批文档/任务更新的新鲜门禁：OpenSpec strict38/38、git diff-check、六份精确untracked文件空白检查PASS；没有业务源码变化，未重复后端全量或前端构建，也不把前批结果改写成本次执行。

基线为本地 `main@341ead8` 加保留的 F8/ACO/Creation Recipe/Persona 未提交工作。数据库、素材与服务均使用隔离目录 `/private/tmp/aics-persona-normal-ui.R2oajI`，API18331/Web15331仅loopback，验收后已停止；本次收尾重新用lsof确认两个端口均无监听。没有操作正式8000/5173/Worker、正式库/模型配置/凭据，也没有真实供应商或公众号调用。

## 已完成的普通页面操作

| 形态 | 证据与时间范围 | 实际链路 | 不证明什么 |
|---|---|---|---|
| Text | 本轮读取既有[24点回执](PERSONA_TEXT_CONTRACT_ACCEPTANCE.md)，没有重跑 | 两角色默认Recipe、候选/修改/显式接受、Master、检查、Candidate v4、Review、授权及本地ZIP | Mock正文不证明真实文章质量或公开发布 |
| Graphic | 同一续作链前一轮完成，本轮读取report并重新校验两张PNG字节hash；10个正常页面检查点、零pageErrors | 视觉方向/卡片计划接受、确定性排版、真实1080×1440 PNG、人工素材接受、显式Master保存、精确render attestation、QC警告处置与可冻结投影 | Mock规划/合成图不证明真实视觉创作质量；警告未改成pass |
| Audio | 本轮实际执行22个检查点、两个角色、零pageErrors、零ASR调用 | 已接受Text→口语稿/声音方向→明确TTS配置/voice/rate→签名任务→原字节校验/真实播放→人工Material接受→QC→估算SRT下载/哈希核对→人工警告处置 | 下层transport使用合成tone，不是真实MiniMax朗读或声音质量；估算SRT不是ASR时轴 |
| Video | 后续单独实际执行21个页面检查点、两角色、零pageErrors；此前API37点保留原批次归属 | 接受脚本/镜头→显式Video Master v2→prepared Director包接受→刷新hash不变 | Mock不证明创作质量；没有最终MP4、外部派发、素材接受、Candidate或发布 |

图文正常链路：

```text
接受视觉方向/卡片计划 → 确定性Graphic Master → 真实PNG
→ 人工接受Material → 显式绑定/保存新Master → exact render attestation
→ current checks + 逐项warning说明 → 人工接受QC
```

音频正常链路：

```text
已接受Text Master（保持不变） → 接受口语稿 → 接受声音方向
→ 可见exact TTS模型/voice/rate Preview → 执行签名任务 → 试听/校验hash
→ 人工确认许可与权利 → MaterialRevision → Audio QC
→ ESTIMATED标记SRT/下载hash → 明确接受warning
```

普通页面没有要求手写Workflow JSON或Prompt grammar。Voice风格描述没有冒充真实Provider voice ID；音频没有引入Audio Master，也没有修改已有Text内容/上下文。素材接受仍不自动绑定其他Master或提升权利。

## 本轮发现并修复的实际断点

TTS Stage在读取模型清单时崩溃，`pageErrors`为`Cannot read properties of undefined (reading 'tts')`。实际methods响应的fallback chat row没有`capabilities`；同时媒体库存仅从chat登记构建，漏掉已存在的native-only TTS配置。

修复现有三个文件：

- `apps/api/app/services/creation_recipe_learning.py`：媒体库存直接投影既有capability-routing；逐能力展示exact provider/model、声明/配置/可执行/verified状态，不复制URL、credential_ref或凭据。
- `apps/web/src/product/StageContractControls.tsx`：安全排除缺失元数据/不匹配能力，禁用不可执行配置，不把配置可用说成真实生成已验收。
- `apps/web/src/product/creationRecipeState.ts`：类型兼容历史缺字段，模型信息按当前能力表示。

先在既有delta补正常页面场景，再最小改实现。临时backend探针先失败于native-only TTS遗漏，修复后通过；真实Audio页面随后完整通过。独立只读UI探针覆盖旧缺字段、错误能力、disabled配置、精确provider/model以及零mutation。探针初次只因HTML option不可见/拦截顺序而未完成，修正临时probe后通过，没有为此放宽业务门禁。

前续fixture失败分别涉及误读`is_current`投影、错误`/invoke`路径、假设“查看结果”必触发新GET，以及`domain`/`domain_output`字段误用。这些只修临时脚本。后来证实的TTS页面崩溃与库存遗漏是实际业务断点，已另行修复，不把两类失败混为同一问题。

## 精确产物与真源

Graphic（前续正常页面证据）：

| Persona | Project/Unit | 最终Master | PNG Material | PNG SHA256 |
|---|---|---|---|---|
| 科技 | 4/4 | 9，revision3 | 4 | `20fb670ce636f2a4f3e3e669c23fab7280d86471f2389e7d2b6040f2c4b2a4af` |
| 生活 | 5/5 | 12，revision3 | 5 | `29decc118dbd9af6bc96f6f82b6931e223f1459b344d100f86320f246491eb58` |

两张PNG均1080×1440。科技背景`#101827`、正文34；生活背景`#fff6e9`、正文38，均由各自Persona preset确定。Render input hashes分别为`7cfc5380b6be196e3f4c88a76c0e0940a1f3ec02759dd22b26d2ae41c8ed2f5e`与`a14ab307c9348f5058cf4c451e041768c0c73caff864dcca915e54b3da9febdd`；public=true、model/commercial=false，来源为明确合成合同输入，不是真实新闻图片。

Audio（本轮实际运行）：

| Persona | Project/Unit | 原Text Master（不变） | 已接受Task | Material | WAV SHA256 |
|---|---|---|---|---|---|
| 科技 | 11/11 | 18 | `29687ef92c1e45e7b466589f571a6d12` | 6 | `b84a24614a04599962868f5627f8d4d7afe9177460519c20ad7dabc97d3e0549` |
| 生活 | 12/12 | 19 | `e7f157ed94224cd4b3683d4bf33493bd` | 7 | `c235834a87510be939c3b4e97f56874b364b0cf0abef41997541de322e63c222` |

两个文件真实播放2秒，signed receipt验证exact voice/rate/runtime。用户页面许可选择self_owned、model=true、public/commercial=false；这里仅指自制合成tone fixture的权利，不是MiniMax输出许可证认定。两Unit均只有原Text Master一条修订，原ID/payload hash/context hash不变；四个Audio Stage均接受。

QC仍为warning：bytes/hash/duration/voice/rate/binding已验证，ASR为not_run、perceptual_quality为human_review_required，响度只有RMS而非完整LUFS。用户明确选择estimated，下载`audio-estimated.srt`包含`[ESTIMATED / 估算；非ASR时轴]`；两个SRT SHA256均为`cd96c3cbfc166642fe444028450b9794b4a635e38f95f91305fb9a5b2936c876`。

报告、截图、PNG/WAV/SRT留在上述隔离目录供检查；它们不写入正式素材库，也不算正式角色初始化。

## 集中门禁与独立复核

### 整体后端复核新增修复（2026-10-07）

whole22.4独立复核另发现两处实际安全缺口：Master成功回执仍可能保存未接受的额外Provider字段；已接受中间产物的素材再次供下游使用时缺少父素材及派生祖先实时权利检查。先补既有delta，再最小修正stage_master_proposals.py和creative_method_stage.py；历史Attempt/legacy recorder保持不变。

隔离34项检查修前12失败、修后34/34通过，覆盖额外diagnostics/local path不得进入成功receipt、原响应hash仍保留、归档/异常素材及祖先撤权/许可义务丢失必须阻断。临时fixture目录重用失败另行纠正，不伪装为业务门禁。原reviewer Nash随后对whole22.4完整后端／数据／安全重新复核APPROVE，未发现剩余确认缺陷；明确不是两个finding的窄批准。仅据此关闭22.4，当前120/147。

| 项目 | 执行证据与批次 |
|---|---|
| Full existing backend | 两处最终后端修复后新跑：1968 passed /28 skipped /80 warnings，104.40s，exit0；development/mock、已初始化临时Worker SQLite、本地临时素材、native/ASR禁用；先前106.02s为历史批次 |
| TypeScript/Vite/FE-P1 | 两处最终后端修复后新跑：PASS，exit0；Projects224.26/72.75kB，commonProduction283.17/90.53kB，Text lazy609.92/190.75kB；Graphic/Video/common无TipTap，common无XYFlow |
| 最终安全红绿 | 34/34临时检查PASS；修前12项失败，修后normalized Master receipt、原response hash和live素材/祖先rights均通过；不替代永久测试 |
| Native-only库存红绿 | PASS；native-only、disabled与无URL/credential公开投影 |
| 库存只读UI负向 | 五项PASS、pageErrors=[]、mutations=[] |
| 整体22.5产品/UX复核 | Euclid APPROVE；独立检查当前源码、报告、截图与SRT hash，未重跑作者浏览器或调用供应商 |
| 整体22.4后端/数据/安全复核 | Nash whole APPROVE；只读检查当前源码与调用链、读取回执，未重跑作者34项临时probe或全量测试；两项原finding均已闭合 |
| Ruff/OpenSpec strict | 本次文档收尾重新执行：全app Ruff PASS；根目录strict38 passed/0 failed，均exit0 |
| 产物回读/临时服务 | 本次重新校验两PNG、两WAV、两SRT，全部SHA256与上述记录一致；lsof18331/15331为空，两个自有临时服务已停止 |
| git diff-check | 最终tracked和本批相关untracked空白检查结果记入change progress；不将空白检查当业务验收 |

两份独立复核仅关闭22.4安全合同和22.5普通产品操作合同，不批准22.6真实创作质量、6.4待定组合语义或最终发布/归档。八个永久回归义务仍开放：临时脚本不是持久测试，遵守当前“不新增测试代码”的约束。

## 待完成、依赖和启动方式

剩27项包括：3项历史/暂停change依赖、8项持久测试义务、6.4方向选择、12项真实成品/授权/rubric、2项正式初始化以及1项生命周期授权。不是27个都尚未开发的新功能；整体backend/security复核22.4已关闭。

6.4仍等待用户选择非AI排版/渲染如何消费组合方法；未替用户决定，不新增隐式模型调用。正式角色初始化、付费Text/Graphic/Audio验收、canonical同步/归档/提交/push均仍遵循分别授权。

沿用现有SQLite、本地素材库、API/Web/Worker和既有headless renderer；不新增依赖、表或migration。临时18331/15331已停止，正式服务未操作。日常启动仍以根README和现有运行手册为准。

本轮skills：using-superpowers、openspec-apply-change、writing-plans、executing-plans、systematic-debugging、receiving-code-review、test-driven-development（临时红绿复现，未新增永久测试）、requesting-code-review、verification-before-completion。
