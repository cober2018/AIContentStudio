# F7 模型提交与真实调用验收

## 2026-10-03 F7主任务10.3证据归位

本轮不新增供应商调用。按用户已批准范围核对已有实际记录：

- 原私有真实图片任务`cc6f9c535ac94ab296916aff9b990d8f`仍为`result_ready/rev3`，精确模型`image-01`；JPEG33997字节，文件重新计算SHA256为`1e18a7be540f091ac7d71510a3aebe68a24ca57413f99b2e00667857c0db7298`，与原task一致。这里只证明真实生图输出，不推定HMAC跨进程恢复、正式素材接受或公开/商业许可。
- 正式库TTS任务`331e55283ab8402f9c564c3145d4a101`只读回读为`accepted/rev4`、`speech-2.8-hd`、`accepted_material_revision_id=6`；MaterialRevision6为ai_generated/audio-wav、原hash及公开/模型/商业权利false不变。Text Master9仍为text.master.v2/revision3。页面刷新与接受链路沿用下方已执行证据，不宣称本轮重跑浏览器。
- 既有真实MiniMax WAV与测试MP4音轨ASR实测继续作为云适配器证据；正式库本机Video Master5仍为video.master.v2/revision3，当前结构中43条cues，与已完成的用户视频→接受→显式保存/刷新/重启记录一致。
- MiniMax视频生成/H3仍为`excluded_by_user_scope`，不是PASS；CPA媒体未证实，Google/xAI原生适配不在本次范围；Commons仍暂缓。

本轮既有交付/能力/ASR回归119 passed/1既有warning（17.41秒），只证明当前本地兼容门禁；新网络生成、正式库写入均0。上述真实操作/接受/权利边界分别保留，不能由任务关单把不可执行或未授权操作自动升级成verified。限定独立计划/证据复核同意按该范围关闭主任务10.3，F7现105/110；提交、主规格同步和归档仍为独立任务。

## 2026-10-03：模型路由23/23实施收口

最后五项2.1/2.5/2.6/2.7/2.9已关闭。CPA精确聊天与MiniMax已执行操作沿用下方真实记录；本批没有重复付费生成或微信发送。私有真实服务Workflow完成一次合成提交、等待人工接受、exact MaterialRevision/项目输出、别名映射及下游推进，原started Attempt不变、重复resume不发送。前次2.8实际隔离浏览器与正式TTS/本机MLX字幕回读证据继续独立保留。

收尾修复五处原契约缺口：跨任务预览旧确认、接受后的输出映射、映射覆盖系统状态/素材身份、ASR凭据漂移、零帧WAV。前四类消费者/身份路径分别用真实函数、私有API或Workflow边界复验，空音频在结果落库前拒绝并保留claim。Provider reviewer通过内存epoch/音频探针；消费者reviewer通过56个跨字段别名碰撞及正常/延迟/identity/legacy映射复验，两份限定复核APPROVE。复核员没有重跑浏览器、全量、native PG或真实供应商。

最后源码补丁后主agent实际执行：全量1660 passed/28 skipped/8 warnings101.93秒、177定向5.98秒，Web TypeScript/Vite/FE-P1/state、九文件Ruff、OpenSpec strict34/34及diff均通过；明细见[最终门禁](FE_F7_FINAL_LOCAL_GATES.md)。main@8c0e3b8工作区保持未提交；没有新增依赖/表/迁移/永久测试、正式配置/库写入。当前是本模型路由change的ARCHIVE_READY，未同步/归档、未push/deploy，不冒称整个F7/F8已收口。MiniMax真实视频/H3仍excluded，CPA媒体与公开/商业许可未证明的部分保持不可用/false。

## 2026-10-03：当前产品验收补齐（下方同日旧状态为历史）

正式MiniMax TTS任务331e55283ab8402f9c564c3145d4a101已单次执行并人工接受为MaterialRevision6，经Project1引用、Unit3 Master9/v3及浏览器刷新回读；所有公开/模型/商业权利保持false，不作为可发布成品。本机MLX ASR已从用户真实视频生成43条字幕、明确接受并显式保存Video Master5/v3，刷新及API重启回读通过。语音实测、Formal启用、接受与ASR入口不再是未完成状态；下方“prepared/尚未正式启用”保留原阶段历史，不能据此重复付费调用。

生成任务3.2/3.4的本地generic可靠性已通过并发/实际进程中断/重启/key与credential/job身份/撤权/回滚验收及限定独立APPROVE；修复后全量后端1660 passed/28 skipped/8 warnings，strict34/34。所有机制夹具与真实供应商证据分开，不冒称真实视频恢复或F7整体完成。

当前又以独立临时库/API18118/Web17174进行实际页面验证：chat-only→image-plugin→准备（0发送）→合成PNG→预览→明确接受MaterialRevision1→刷新accepted/rev4；native TTS→合成WAV→明确接受Revision2；Unknown→无job状态核对保持Unknown且0补发；未配置video插件422、零task/发送；Settings限额在页面保存revision1→2，旧任务发送前409且零发送。这里只是合成Provider，不能替代真实MiniMax生图/视频/商业许可证明。初次harness漏submit_task方法被真实服务422拒绝、零claim/发送；修正harness后复用原prepared任务完成，未修改业务门禁。

发现并最小修正两处Panel体验：无插件的typed reason改为中文；execute HTTP失败后只读GET同一task回读真实状态，读失败继续保守Unknown，从不自动发送或切换Provider。实际页面确认配置已变化时任务仍prepared/rev1，错误说明真实显示，不再伪装成已发送Unknown。

私有验收证据目录：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aics-routing-browser-n3pjrc_q/`。`image-accepted.png`为隔离图片接受，`unknown-no-resubmit.png`为Unknown不重发，`routing-history.png`为最终两accepted/Unknown/旧prepared回读；控制台error为空。临时路径不是正式库、长期发布资产或供应商产物。

补丁后新鲜TypeScript/Vite/FE-P1/state与144定向回归通过；限定Panel源码/2.8证据独立APPROVE，复核员未重跑浏览器。2.8已完成，本change18/23，剩2.1/2.5/2.6/2.7/2.9；本证据不关整个F7。隔离进程已停止，未提交、推送或归档整个change。

## 2026-10-03：当前本地正式使用库接入

用户授权现有个人本机库接入，复用已有真实音频，本批新付费调用为0。先在线备份并在副本完整演练；再准确升级`apps/api/content_studio.db`从d4audit00004至f7d000000001，没有运行f8a或upgrade head。迁移边界所有原表记录数/原模型配置一致，SQLite integrity=ok；历史97条外键异常未增加。私有备份位于`backups/minimax-local-z98vx7ki/`（0700，前后数据库/配置/key均0600），安全ledger为final-safe.json，不把备份或key提交Git。

固定runtime.env显式加载MiniMax opt-in、receipt key-ID/JSON映射和Homebrew PATH。API/Worker重启后设置与任务API均200；模型配置revision4新增image-01/speech-2.8-hd/asr-1.0及对应插件、图片像素/语音10秒限额。默认Gemini、七个文本用途路由及所有原profile密钥逐项与备份比较一致；video未启用。库存不探测认证，仍显示尚未验证；明确prepare才验证当前CLI/认证并冻结路由。

| 当前正式产品动作 | 实际结果 | 不可扩大的结论 |
|---|---|---|
| `/assets`页面TTS准备 | task331e55283ab8402f9c564c3145d4a101，prepared/rev1，Gemini→MiniMax speech插件 | 未执行生成，无job/结果；不等于新供应商成功 |
| 原真实WAV从页面导入 | Material2/Revision2，audio/wav，原219618字节及SHA256不变 | source_kind=upload，不伪造隔离生成Task/owner/provenance |
| 项目精确引用 | Project1/Unit1，ProjectMaterialReference1→Revision2 | 只引用，不复制素材或授予公开权利 |
| Master显式保存 | 产品API建Master1；页面改标题并保存Master2/v2，刷新后可见 | text.master.v2附件引用，不冒称Video/ASR字幕保存 |
| API重启及独立新进程 | Master2/素材hash/路由持久化；prepared HMAC验证PASS | 只证明这个prepared回执，不覆盖所有Unknown/崩溃窗口 |

Master标题：`MiniMax 本地接入 · 正式音频已引用`。音频仍unknown/public=false/model=false/commercial=null；项目未绑定Brief/Fact Boundary/channel，页面诚实显示incomplete_context且不能freeze。没有把用户授权导入误当许可授权。当前结果可在`http://localhost:5173/projects/1/units/1/production`查看，系统库也可读到Revision2。

现场发现并最小修复：Materials表单metadata从multipart改为符合既有API的query；第一次错误Material1被默认kind=image/rights=cleared，保留为未引用复现记录、不删除，第二次页面上传正确。NodeInspector imports移至lazy初始化前，修复Vite开发TDZ；未重构Graphic/Video。

新鲜验收：118项既有定向测试PASS（1既有warning，3.44秒），TypeScript/Vite和FE-P1 PASS；Projects224.89/72.96、Assets258.86/82.83、Settings236.53/77.28、公共Production284.42/90.47kB raw/gzip，Text重型编辑器仍lazy。全部OpenSpec strict33/33、diff-check PASS；仅两源码修正/key忽略的独立只读复核APPROVE。没有新测试文件或迁移版本、未重跑全后端，下面旧全量不是本次结果。

**本地启用＋已有真实素材引用链路：PASS。新正式任务execute→preview→accept、Production ASR建议接受/字幕保存：本批未执行。** 保持路由15/23、F7未整体完成；无commit/push/deploy/公开发布或canonical sync/archive。以下语音实测章节是接入前历史，不再把其中正式缺配置状态当作当前结论。

## 范围

## 2026-10-03：本轮 MiniMax 语音实测

用户批准一个≤10秒短句TTS、一次音频ASR、一次视频音轨ASR，最多三次调用。实际只发送三次，不重试，不生成视频；原H3任务未查询或修改。

| 操作 | 本轮实际结果 | 验收边界 |
|---|---|---|
| TTS：speech-2.8-hd | PASS；WAV 3.41334375秒、219618字节 | 隔离产品generation-tasks API，prepared→result_ready/rev3；未接受正式素材 |
| 音频ASR：asr-1.0 | PASS；准确返回“这是语音能力测试，请准确转写。”；80–3140ms | 现有MiniMaxCLIASRProvider+provider_calls，真实WAV输入 |
| 视频音轨ASR：asr-1.0 | PASS；同一原句/时间戳 | 本地黑底H.264/AAC MP4、3.414秒；提取音轨转写，不是视频生成或画面理解 |

实际音频SHA256：`ac6cbb51a7ba2a8e046fd42c7d832c7fa4e0942928e4f0fad30028fdcd83b98f`。视频SHA256：`60c78641b89ed807d6381bcba297a04f69a1ac7d7e210218d8a1f8b0fa9a7bf8`。生成任务：`3b239d78b6654073a100385d8e69ac93`。

另一个进程重新加载同一0600私有验收签名key，验证任务/结果HMAC、当前CLI凭据epoch、MIME和音频原字节hash，全部通过。该证据关闭本次TTS回执跨进程连续性，不能推广成所有异步/Unknown恢复边界通过。私有目录0700，DB/key/report/WAV均0600：`/private/tmp/aics-minimax-speech-vj2UI7/`；报告为`result.json`，不把key或字节提交到Git。初次验收harness将API的task_id误读为id，在prepared阶段失败、零付费调用；只读修正后复用同一未发送task，没有重复生成。

**本轮三项供应商语音操作：PASS。正式产品启用：尚未完成。** 正式库当前缺provider_generation_task表，保存配置revision3没有媒体binding，检查进程未显式配置稳定receipt key/CLI opt-in。隔离库和签名key不是正式配置，本轮没有正式迁移/配置写入/素材接受，不授予公开或商业权利。ASR实际证明的是适配器，不是Production ASR API、字幕接受或Master保存的浏览器闭环。

新鲜既有回归：54 passed、1既有弃用warning（2.31秒）；OpenSpec strict33/33、git diff --check PASS。没有新增测试代码、业务源码或依赖，没有重跑全后端/前端、不借旧结果；路由change仍15/23，复合任务不因这三项实测自动关闭。无提交/推送/归档。

**最新范围调整（2026-10-03）：** 用户明确不要求当前 MiniMax 套餐的视频生成验收，停止 H3 提交/查询/下载重试，此项 excluded_by_user_scope，不是 PASS，也不再是本轮 F7 阻断。下方 H3/DNS 结果仅保留历史证据。用户说明套餐额度/模型有限，本文件不把它推断成所有 MiniMax API 都不支持视频。MiniMax 聚焦 TTS、ASR、已有视频提取音轨后 ASR；不生成视频，不做画面理解。用户随后批准三次≤10秒语音实测，结果见上方；未修改正式配置。

2026-10-03 用户确认：先把模型登记、能力路由的必要依赖和整理后的“模型与 AI”页面提交到本地 main，再验证已保存的 CPA 模型。其他未完成的 F7 消费者/持久任务和 F8 改动不混入本次提交。不 push、部署、迁移正式库或重复生成视频。

## 可复现提交门禁

在 main@931915d 导出快照中只加入本次选定文件，沿用已有依赖；配置类只加入 shared runtime guard 必需的 app_env，Team 页面保留已提交行为，不带入未完成 F8。

- 既有模型路由/设置回归：85 passed，1 个既有弃用警告。
- Web TypeScript/Vite、FE-P1 和既有路由状态脚本：PASS。
- /settings：236.26 kB raw / 77.16 kB gzip；/projects：224.89 / 72.97 kB。
- 全部 OpenSpec strict：33/33；范围 Ruff：PASS。
- 首次全量：1655 passed / 28 skipped / 1 failed。旧 Worker 测试使用模块级文件数据库，而导出快照未初始化该库，失败为 no such table: content_job；未修改代码，随后仅初始化隔离临时数据库重跑。
- 隔离临时库初始化后全量重跑通过；补入工作区已有的 models_section 安全投影依赖（不含同文件 F8 Team 修改）后，再次精确全量：1656 passed / 28 skipped / 8 warnings（75.69 秒）。85 项相关回归与范围 Ruff 重新通过。未新增测试代码；跳过项不算 PASS。
- 隔离进程实际验证停用默认模型后设置仍 editable、availability=false，而模型执行继续拒绝，不借读取保护放宽执行。
- 精确 index 与验证快照逐文件 hash 一致，44 个选定文件，diff-check PASS；未发现硬编码凭据。独立依赖复核首次指出遗漏的默认模型不可用投影，补入后 APPROVE（源码复核，不冒称 reviewer 重跑测试）。
- 功能已本地提交 main@8c0e3b8；其他 F7/F8 改动仍保留，未 push。

## 真实模型验收

使用系统已保存配置，凭据不回显、不改默认或用途路由。实际调用的是 AIContentStudio `/api/v1/settings/llm/test`，不是直接旁路供应商脚本。每个模型一次短聊天，无自动重试：

| 精确模型 ID | HTTP / 结果 | 服务端耗时 |
|---|---|---|
| gemini-3.8-flash-high | 200 / ok=true / 正常 | 5146 ms |
| claude-opus-4-6-thinking | 200 / ok=true / 正常 | 4129 ms |
| grok-4.7 | 200 / ok=true / 正常 | 6278 ms |

产品 `/model-registration/providers/cpa/models` 只读发现返回 HTTP 200、30 个模型，包括上述三个精确 ID。旧 401 是历史记录，本轮鉴权已通过。配置回读仍 revision 3、默认 Gemini，全部用途路由未改变。

在独立进程只读加载同一用户配置，实际消费者 `effective_llm_config()` 七个用途均匹配当前绑定：generate/rewrite/text_master_edit → Gemini，fact_check → Claude，topic_discovery/discoverability/platform_adaptation → Grok。真实 `get_provider('generate').generate_json()` 经相同已登记 CPA 适配器调用并确定性解析 `{status: 正常, count: 2}`，route provenance 精确为默认 Gemini profile/configuration_revision=3。未创建业务 Draft/Run、未持久化 LLMRun 或修改配置。

**CPA 三模型聊天 + 当前用途解析 + Gemini 结构化消费者合同：PASS。** 这不代表专业功能输出质量或 CPA 媒体合同通过。

媒体验收与聊天分开。当前配置 revision 3 没有 media_plugins 或 capability_routes；不能把 CPA 聊天成功记为图像/视频/TTS/ASR 成功。

通过本产品 `MiniMaxCLIVideoProvider.query_task()` 有界查询原 H3 任务 448101822222777：产品返回 running / generation_download_unavailable / 0 bytes。随后只读诊断确认供应商同一 job、同一 MiniMax-H3、远端状态 succeeded；成品域名 `algeng-video-infer.oss-cn-shanghai.aliyuncs.com` 当前解析为 `198.18.4.255`（VPN Fake-IP）。产品拒绝非公网下载地址符合既有安全门禁，本轮没有视频字节/hash/素材接受，也没有重发或创建替代任务。

**历史结果：MiniMax 原任务远端成功；当时产品视频下载闭环 BLOCKED_BY_DOWNLOAD_DNS。当前按用户决定已排除此项，不再把 DNS 作为本轮 F7 阻断。** 稳定 receipt/恢复、在范围内素材权利与显式接受、完整浏览器验收继续按 active OpenSpec 判断；路由 change 仍 15/23，不提前勾选复合任务或归档，不宣称 F7 整体完成。

## 依赖与操作边界

启动方式沿用根 README；无新增包或本次迁移。提交包含模型登记/路由服务、固定 MiniMax CLI adapter、模型设置 UI、已有回归文件及对应规格，不包含用户数据库、凭据或任何临时生成结果。

```text
精确提交快照 → 既有门禁/依赖复核 → 本地 commit
已保存 CPA 配置 → 实际短聊天 → 按能力记录证据
原 MiniMax job → 只读查询/安全下载 → 不确定则保留，不重发
```
