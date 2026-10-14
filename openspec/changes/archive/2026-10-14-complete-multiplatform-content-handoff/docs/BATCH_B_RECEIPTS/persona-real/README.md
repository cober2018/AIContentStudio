# 两 Persona 新 Series 真实成品

当前阶段：**用户已委托 Codex 完成质量评审；Text/Graphic 最终来源、成品绑定与完整检查通过，整模态 AI 委托质量评审亦通过，详见 [最终评审](quality-review.md)及[增量入口](final/README.md)。** 本页及 manifest/样本保留初轮历史，以下 pending/blocked 描述均对应初轮，不代表最新状态；任务记账由 owner 统一处理。

## PRD / 需求背景

从 Persona-owned Series 出发，用产品现有 Stage、真实 Provider 和明确接受动作验证两个角色的 Text/Graphic/Audio。科技稿谈一般工程设计取舍；生活稿明确是晚饭前放远手机的假想观察，不编造新闻或作者经历。实际产物全部为本轮新生成，没有复用旧文字、PNG 或 WAV。

## 代码位置与成果目录

产品代码为本仓 `apps/api` 当前工作区，版本由 owner 的 README/版本索引统一记录；本工作者没有改业务代码、测试或 Git。运行库与临时 harness：`/private/tmp/aics-persona-series-20261014.ane8u3as`，这是读正式 WAL 后建立的隔离副本，不能作为正式用户数据入口。

- [manifest.json](manifest.json)：逐 Stage/Provider 回执、身份、模型/运行指纹、全部哈希、实际 QC 和限制。
- `tech/`、`lifestyle/`：`article.md`、`text-master.json`、`graphic-master.json`、有序 `graphic-1.png` 至 `graphic-3.png`、`graphic-qc.json`、`audio.wav`、`audio-qc.json`。
- 不交付数据库、私有环境、原始 Provider 响应或认证材料。

## 已完成

| 项目 | 科技 Persona 2 | 生活 Persona 3 |
|---|---|---|
| Persona-owned Series | Series 1，账号为空 | Series 2，账号为空 |
| 文章 | Project 3 / Unit 7 / Master 11，真实 Gemini 候选明确接受 | Project 4 / Unit 8 / Master 12，真实 Gemini 候选明确接受 |
| 三卡主稿 | Graphic Unit 9 / Master 13，真实 card-plan → 接受 → compose → 接受 | Graphic Unit 10 / Master 14，同一真实链 |
| 本轮明确图文样式 | `architecture-diagram@1`，纯文字卡 | `lifestyle-cards@1`，纯文字卡 |
| 实际 PNG | 3 张，1080×1440；素材版本 11–13 明确接受 | 3 张，1080×1440；素材版本 14–16 明确接受 |
| 音频 | 新 Run 9 → spoken 44 / voice 45 / TTS 46，素材版本 10 | Run 8 → spoken 40 / voice 41 / TTS 42，素材版本 9 |
| 可解码 WAV | 107.124 秒，32 kHz，单声道 | 84.683 秒，32 kHz，单声道 |
| Audio QC | Attempt 47，pass，零问题 | Attempt 43，pass，零问题 |
| 图文 geometry / structure | pass / pass | pass / pass |
| 图文平台 QC | blocked：`graphic_inline_media_required` | 同左 |

六张图均打开检查了实际像素；10 个交付原件均按字节、大小与 SHA-256 回读一致。隔离库 `integrity_check=ok`、foreign-key check 为空，schema head `a3series00000001`。当前正式库的 91 表 / 482 个已有行在隔离副本逐主键全列比较一致；此比较不宣称其他工作者没有获准修改正式状态。

| 真实调用 | 文章 | Card plan | Spoken | Voice | TTS | 合计 |
|---|---:|---:|---:|---:|---:|---:|
| 实际次数 | 2 | 2 | 3 | 2 | 2 | **11（Chat 9 + MiniMax TTS 2）** |

没有新 Unknown、Provider 重试或 ASR 调用。原科技 spoken Attempt 38 已成功，但临时脚本分进程启动导致运行连续性密钥变化，产品拒绝接受；原回执保持未接受。本轮另获准的新 Audio Run 9 重新生成一次 spoken，并在同一持续进程完成后续接受。另一次 TTS preview 因临时环境解析错误在派发前阻断，使用原启动脚本的私有 shell 加载方式后恢复，没有重发 TTS。

## 待完成 / TODO

- 用户阅读两篇文章、逐张查看图文并实际试听，按固定 rubric 确认质量；独立创意质量评审仍待。
- Text/Graphic 当前 Master readiness 为 `evidence_missing`。本批不把模型观点或假想场景伪造成冻结事实来源；完整语义事实/身份检查未派发。
- 小红书当前 Profile 要求 inline 媒体，而平台 QC 只计算 canvas 内部 image/chart。明确选择的纯文字卡被 `graphic_inline_media_required` 阻断。回执保留这一真实限制，没有放宽检查或塞入假素材。
- 六张 PNG 和两段 WAV 的 public/model/commercial 权利均为 false，接受仅用于本机隔离验收。因此没有最终公开用途 render attestation、冻结公开包或发布成功声明。
- ASR 未运行、LUFS 未测量。Audio QC 验证了签名音色/语速、Provider、当前绑定、真实字节和可解码时长；这不代替试听。

## 关键设计决策

Persona 默认均保全，生活 `warm-magazine` 默认照片封面链没有冒称通过。本批显式项目 Stage override 只选择已有三卡样式，避免增加生图调用与无依据的图片许可。接受动作是用户授权下的技术采纳，`quality_accepted=false`；产品接受、平台 readiness、真实人工质量和公开发布分别记录。

## 依赖与使用方式

沿用 `apps/api/.venv`、已配置 Gemini/MiniMax 和已有 Chromium renderer；没有安装依赖、启动临时 API 或操作正式服务。原件可以直接打开；临时生成脚本有真实调用，**不要复跑**。只读回验使用 manifest 哈希与文件即可。已有启动方式见项目本机运行手册。

本轮实际使用：using-superpowers（读取 subagent 规则）、writing-plans（沿用 owner 同一计划）、executing-plans、openspec-apply-change（沿用已批准 change）；未执行归档或 Git 生命周期。
