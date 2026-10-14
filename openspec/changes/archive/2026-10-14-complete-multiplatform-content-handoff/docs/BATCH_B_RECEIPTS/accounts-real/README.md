# 同一技术栏目四账号真实成品本地交接

当前阶段：`LOCAL_REAL_CONTENT_ACCOUNT_INDEPENDENCE_PASSED`（任务7.3，2026-10-14）。本地账号独立流程已验；样本账号是隔离手工登记，保持 `bound_unverified`。本目录没有真实远端账号认证或发布回执。

## PRD / 需求背景

验证一个 Persona-owned 技术栏目同时向公众号、知乎、小红书 A/B 分别交接，逐账号有精确 Variant、Candidate、Review、授权和真实字节 ZIP，不能通过换号复用冻结候选。

## 代码位置与成果目录

复用当前仓库 `apps/api/app/services/channel_variants.py`、`candidates_v5.py`、`delivery.py`、`production_packages.py` 及现有产品 API；本工作者没有改业务代码或测试。版本沿用 owner 当前工作区，最终 Git/代码版本索引由 owner 收口。规范和步骤见上级 `design.md` D-v2.3/D-v2.7、`tasks.md`7.3及同一 `task_plan.md`。

- `index.json`：API逐步状态、完整四套hash、91表482条历史行精确保全、SQLite检查和来源QC实际状态。
- `<target>.json/.zip`：四个目标的安全回执和可打开的交接包。
- `adapt-preview-limitations.json`：原始文章复杂结构的两个422回执，明确人工接受排版归一后才执行确定性适配。
- `source-equivalence-and-review-readback.json`：原文/图片等价证明、16次包内媒体解码、产品Review/账号状态回读。
- `artifact-hashes.json`：本目录其他成果文件的SHA-256。

## 已完成

隔离副本由正式 `apps/api/content_studio.db` 的只读连接通过 WAL backup API 取得；素材复制到独立临时根。TestClient不启动lifespan，数据库依赖指向副本，真实Provider/publisher/网络调用硬拒绝且实测次数全为0。正式库、素材、配置、运行服务未被本链修改。

Persona2下通过产品 API 新建 Series1（revision1），同一 Project3 的文章 Unit7和图文 Unit8均不绑定源Account。正式Master6先原样接受为Master11；原文标题、正文、图片保全后显式追加仅排版归一的Master12（原Master11保留）；正式Master10原样接受为Master14，真实render Material5–8不改。

| 目标 | 隔离Account | Variant | Candidate | Review | Authorization | ZIP字节 |
|---|---:|---:|---:|---:|---:|---:|
| [公众号文章](wechat-article.zip) | 3 | 2 | 3 | 3 | 3 | 711002 |
| [知乎文章](zhihu-article.zip) | 4 | 3 | 4 | 4 | 4 | 711021 |
| [小红书A](xiaohongshu-a.zip) | 5 | 4 | 5 | 5 | 5 | 2393717 |
| [小红书B](xiaohongshu-b.zip) | 6 | 5 | 6 | 6 | 6 | 2393719 |

四目标均有单独AccountRevision和Series绑定，依次完成 target-specific adapt-preview → save → reload → ready checks → v5 freeze → Review批准 → `copy_package`授权 → ZIP → Review读取。四次换目标账号授权均409 `candidate_target_account_mismatch`。各Candidate、授权记录及其回执投影hash、export hash和ZIP hash独立；小红书A/B允许相同真实payload/media，但账号上下文、候选、审核、授权和包身份没有串用。

四包全部逐文件SHA-256通过；文章每包包含原cover及三张inline图片，图文每包包含四张真实1280×960 PNG。16次媒体出现均完整解码且等于原始MaterialRevision字节；rights保持cleared/public=true/model=false/commercial=false，署名字段沿用原始值。原文章与两个渠道文稿的有序正文/图片字段hash均为 `96e4b70ccce1cc86ea4a6191a3877f794bbce5b2f7c973c2e5bc68729af12216`。

## 待完成 / TODO

真实远端账号资格/登录、平台编辑器人工效果与公开发布没有进行；本任务只验本地交接。人类创意质量验收仍由对应任务单独处理，不由本地Review记录替代。来源语义QC仍有真实warning（provider_not_configured / visual语义未验），处置理由精确写入每个Review。中立来源的platform检查incomplete按既有source_check_exclusions交给目标Variant，四目标必要checks均pass/ready。

## 关键设计决策

没有放宽保守adapter或semantic gate。Master11的heading/list超出两个文章目标的确定性subset；Master12是明确接受的共享源排版revision，把heading转为paragraph、list按原条目换行、inline marks转为plain runs、cover引用映射为明确slot。原source payload hash与新排版hash分别保存，逐block的全文字符、顺序、原图片ID/字节和权利相等，不能声称两payload hash相等或此次为新模型生成。Candidate固定精确AccountRevision/profile/Series binding；Authorization逐账号单独记录。`authorization_hash`仅为本地回执投影SHA-256，产品没有存储该hash列；Candidate/export/ZIP hash语义各自独立。

## 依赖与使用

沿用 `apps/api/.venv`、FastAPI/TestClient/SQLAlchemy/SQLite及已有Pillow；没有新增产品依赖或迁移。包可直接打开。操作脚本仅 `/tmp/aics_accounts_real_handoff.py` 与 `/tmp/aics_accounts_real_readback.py`，不属于产品/测试代码；副本与素材保持本机私有目录，不将数据库和密钥交付到本目录。owner负责需要的最终版本/生命周期操作，本工作者没有使用Git或改任务勾选。

实际使用Skill：using-superpowers（subagent规则）、writing-plans（复用同一任务计划）、executing-plans、systematic-debugging。
