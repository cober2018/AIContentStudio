# Director / Channel Variant / 成果绑定与清理验收

## 需求与范围

2026-10-05，第五批；基线是本地 `main@341ead8` 加同 change 前四批未提交改动。已批准 change 为 `align-creative-orchestration-product`，没有新提案或方向扩展。

本批完成 **6.9、7.6、7.7、7.9、12.3–12.9、13.1、13.5，共 13 项**。累计 **122/147，剩余 25 项**；不是整个 change 完成或归档准备就绪。

不新增表/迁移/依赖/永久测试；正式 SQLite 只读 head 仍为 `f7d000000001`。没有正式库、素材、凭据写入或正式 API/Web/Worker 重启。F8 13 个已有文件逐一 SHA256 不变。

## 文件与入口

| 位置 | 本批职责 |
| --- | --- |
| `apps/web/src/product/VideoStudioShell.tsx` | 导演日常表单、精确素材刷新、原时间线/叠字/最终渲染 Advanced、原生图像/TTS/ASR 可达 |
| `ChannelVariantsPanel.tsx`、`ChannelVariantForm.tsx` | 五种 form 的有界正文/意图、manual_edit CAS、历史只读、dirty/409 保留 |
| `ContentMasterPanel.tsx`、`ProductionWorkspace.tsx` | 导演包/执行入口回接，同一页面保留 Workflow 与 Master 各自编辑状态 |
| `apps/api/app/services/creative_execution_files.py`、`creative_executions.py` | exact-key 暂存清理、共享引用/字节校验、CAS 和持久意图/结果审计 |
| `apps/api/app/routers/creative_orchestration.py`、`CreativeExecutionPanel.tsx` | 明确清理与不可逆确认，权威状态回读，失败/缓存结果 |
| `home_projection.py`、`HomePage.tsx` | Execution 风险/人工成果待办投影、owner/归档过滤、exact deep link |
| `creative_packages.py`、`candidates_v4.py`、`candidates_v5.py`、`production_validation.py` | 精确 accepted Material provenance、v4/v5 冻结、跨项目引用及旧 hash 兼容 |
| `project_review_projection.py`、`CandidatePreview.tsx` | 从 frozen manifest 展示已纳入正文的外部来源，不读 raw result_ready |

正文改动、成果接受、素材绑定、Master 保存、attestation/checks、Candidate freeze、Approval、Delivery Authorization 继续是独立明确动作。

## 实际产品链路

```text
无最终 render 的 Video Master v2
    → Director Package
    → 受控 Test Agent MP4 / WAV / PNG 暂存
    → 三项必需输出逐项人工接受为 MaterialRevision
    → 页面刷新素材、明确绑定配音 / 封面 / render
    → 显式保存新 Master + render attestation + checks
    → Candidate v4 → Review / Approval → local ZIP
```

时间线和最终渲染仍在高级入口；旧 Video v1 必须显式 fork，历史修订与归档只读，不创建 video.master.v3。没有专业 executor 也能保存草稿/导演包；不以缺最终 MP4 伪装 Candidate-ready。

五种正文 form：WeChat article、X thread、X single、Xiaohongshu image_note、Douyin spoken_script。按各 canonical schema 编辑，稳定 ID/order 和 exact refs/citations/declarations 原样保留，服务器仍权威。HTML-template 正文不可用普通文本替换；标题/摘要/作者可按原契约编辑。新修订不改 source Master 或 sibling variant。

## 隔离浏览器与 API 证据

API/Web：`127.0.0.1:15421/15422`。SQLite/素材/截图/临时脚本：`/tmp/aics-director.pFKi2i`；使用前批 SQLite `.backup` 一致快照及隔离素材副本，不使用正式库。

受控媒体由 ffmpeg 生成：360×640、4 秒 MP4，16 kHz、4 秒 WAV，以及固定 PNG。它们有真实可读字节，但不是专业工具质量或模型能力证据。浏览器只允许 loopback 请求，真实供应商、公众号与专业编辑器均未调用。

| 验证 | 实际结果 |
| --- | --- |
| 导演包先于 render | Unit 4 的 Master 5 无 render，创建 Director Package 6；不绕过事实/精确输入门禁 |
| 逐成果接受 | Test Agent Execution 14 的 outputs 12/13/14 分别接受为 MaterialRevision 12/13/14；整单 required 合同满足，原 Master 不变 |
| 明确绑定保存 | 刷新素材后绑定 voice 13 / cover 14 / final render 12；显式保存 Master 12，再 attestation 保存 Master 13，checks/冻结通过 |
| v4 Review / Approval / ZIP | Candidate 1 从 exact Master 冻结，展示三条安全外部成果血缘；明确处置 warning 后批准、local manual account 授权和 ZIP 通过 |
| 五种 Variant | 实际 POST 修订、刷新回读、source/sibling hash/refs 保持；X single 拦住 POST 后制造真实并发，输家 409 保留本地正文与意图 |
| 历史 Video / ZIP | 另存 Master 15 后，Master 13 只读、Candidate 1 不变；重新读取整个 ZIP 的 SHA256 一致 |
| 原生生成入口 | image / TTS / ASR 从视频创作入口可达；不发送真实 provider POST，不改变 ProviderGenerationTask 真源 |
| 两份 dirty state | 修改脚本与 Workflow 新节点，两个保存按钮各自可用；开合 Advanced 保留两份本地草稿，无 POST |
| 权限/归档 | viewer 控件只读，cleanup API 403；archived Unit cleanup 409；foreign user 404。夹具状态在检查后还原 |
| 显式 cleanup | 实际 UI 确认删除三个隔离 staging 副本；正式 Material bytes/hash、全部 output/history 行和 Preview 仍保留，重复 cleanup 缓存成功，不再删除 |
| Home | result_ready exact link 可达，accepted 后消失；unknown 优先于 blocked，foreign/archived 不泄露；GET 无执行、模型、Candidate 或审计写入，缺表明确 unavailable |
| 跨项目素材冻结 | 消费 Project 2 显式引用来源 Project 1 的 accepted Material 14；实际 Candidate 2 v4 / Candidate 3 v5 均保留来源 project 1 / unit 4，而非伪造为消费项目 |

三个完整 ZIP：`director.zip`、`director-history.zip`、`director-after-cleanup.zip`，SHA256 均为：

```text
9889528e53c4f99d3667ab43de0c3e8d5726593026932833db345c18e4df4605
```

临时脚本包括 `browser.cjs`、`bind.cjs`、`close-video.cjs`、`variant-browser-next.cjs`、`history-browser.cjs`、`dirty-browser.cjs`、`cleanup-browser.cjs`、`home-check.py`、`cross-project.py`、`cross-freeze.py`。截图为 `accepted.png`、`director-bound.png`、`review.png`、`variants-complete.png`、`history.png`、`cleanup.png`；最终浏览器无 page error。早期 harness 按真实字段/路径/按钮标签修正，没有为错误夹具削弱业务门禁。

## 清理及冻结来源不变量

- 只解析所选 execution 的精确 staging key；无递归删除、无任意路径、无后台 TTL。O_NOFOLLOW、regular inode/link/hash/字节检查；共享 key 的所有 output/attempt 在同一 CAS/写入边界重验。
- unknown、未解决 blocked、待接受引用不丢 bytes。accepted 副本先重验正式 Material storage；清理不删除 MaterialRevision、ProjectMaterialReference 或不可变输出历史。
- ProjectEvent 记录清理意图/结果，AuditLog 保留诊断；失败可重试，不假成功。最新权威结果按 intent_revision 再 event ID，而不是迟到结果的写入时序，旧失败不覆盖新成功。
- 外部来源只来自精确 accepted Output / MaterialRevision / Package 的匹配。消费项目必须有明确 ProjectMaterialReference 或 WorkflowOutput；Material 本身 system_shared，原 source project/unit 不当作消费 owner，也不能被改写。
- frozen provenance 仅包含安全 ID/hash、role/index/attempt/executor projection；无路径、原始结果/错误/secret。raw result_ready 不会被当作 Candidate。旧 v4/v5 无该 optional 字段时不回填或改 hash；live rights/evidence/currentness 不放宽。

## 独立复核与修正

独立计划/SPEC、Python 安全、TypeScript 产品实现最终均 **APPROVE**。首次发现两项真实问题，先临时 RED 再最小修复：

1. 清理旧请求的失败结果可能迟到，按最后 event ID 会覆盖较新成功。加入不可变 intent_revision 排序和旧记录 fallback；执行者 32 项临时断言含 6 个审计竞争场景通过，父层重新运行 32 项通过；独立安全复核另外重放 4 个时序场景。
2. 外部 Material 跨项目显式使用被来源 project/unit 等值误拦。改为消费项目引用授权＋原接受血缘验证，直接 helper RED/GREEN 和实际 v4/v5 冻结通过；来源仍不改写。

独立审查是限定实现审查和指定时序复放，不冒充复核者重跑整套后端/浏览器。全量和构建由主执行者在最后业务修正之后实际运行。

## 最终门禁

| 门禁 | 修正后新鲜结果 |
| --- | --- |
| 全量后端 | **1660 passed / 28 skipped / 8 existing warnings，86.85 秒** |
| 暂存清理临时回归 | 32 passed / 1 warning，7.29 秒；不是新增永久测试 |
| TypeScript / Vite / FE-P1 | PASS；2366 modules，Vite 1.83 秒 |
| Projects initial JS | 225.03 kB raw / 73.01 kB gzip，250/80 预算内 |
| Home / Learning / Assets / Settings | raw 231.97 / 253.53 / 262.15 / 240.66 kB；均无 TipTap/XYFlow |
| 通用 Production | 279.62 kB raw / 89.38 kB gzip，无 TipTap/XYFlow |
| Variant lazy closure | 302.98 kB raw / 97.51 kB gzip，无 TipTap/XYFlow |
| Text lazy closure | 606.37 kB raw / 189.59 kB gzip；TipTap 保持 Text-only，Graphic/Video 不带入 |
| OpenSpec strict | 35/35 PASS，文档/勾选收尾后再次运行 |
| Ruff | 本批 9 个 Python 文件 PASS |
| diff-check | tracked + 本 change owned-untracked 空白检查 PASS |
| ownership | F8 13/13 SHA256 一致；main@341ead8、正式只读 schema head 不变 |

全量后端命令（`apps/api`）：

```bash
APP_ENV=test DATABASE_URL=sqlite:////tmp/aco-stage3-HRe8tT/final-suite.db AI_STUDIO_MEDIA_ROOT=/tmp/aco-stage3-HRe8tT/final-media .venv/bin/python -m pytest -q
```

没有新增永久测试文件/用例；既有 migration head 断言更新属于前批。文档最后收尾不改业务代码，不以措辞更新再次真实生成/发布。

## 限制与后续

剩余 25 项包括 executor descriptor/recovery、真实 Codex/Claude 本地客户端、重复编辑偏好建议、完整 Legacy operation parity/日常导航退出、配套备份恢复/安全/完整验收及持续授权边界。后续仍按批准规格推进，不提前勾选。

本批受控链路不证明 After Effects/Premiere/Resolve/Photoshop 自动化或生成质量优于现有方式。专业 pilot 不是本批验收；原生 ProviderGenerationTask 不被新 Execution 替换。

旧导航及 compatibility URLs 保留；canonical sync/archive、本地 commit、push/deploy、正式 SQLite migration 均未执行。仅停止本批隔离 15421/15422 进程，保留临时证据。清理删除的三个 staging 副本不能直接恢复，但对应成果完整字节仍在隔离正式 Material storage，原输出/接受历史及 ZIP 均可回读。
