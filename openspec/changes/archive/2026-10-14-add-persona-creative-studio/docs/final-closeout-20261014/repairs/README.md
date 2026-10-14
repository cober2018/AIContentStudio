# Persona 默认图卡质量修复回执

本目录记录用户委托的隔离数据修复：科技图卡恢复 `technical-editorial` 默认风格，生活图卡恢复 `warm-magazine` 默认风格并替换空泛正文。已有文章、音频、已归档多平台 change 与正式数据保持原样。本记录仅证明图卡实物、引用和产品检查；独立 AI 质量结论由上级收尾评审给出。

## 需求背景与范围

复用既有 Text Master 21/22 与已建立的事实边界，编辑压缩为三卡计划。科技内容明确属于架构意见；生活内容明确是假想晚饭场景。生活封面只复用 2026-10-09 原验收包中 SHA 为 `a0f86a965df961f6edca8b08ee2707e71155b0cbed863113ebc49c6486b34e20` 的实际 PNG。缺失的原 JPEG 未被恢复，旧图也不代表真实晚饭照片。

新计划署名为用户授权下的 Codex `user_edit`，不声称由模型 Stage 生成，不复制旧 Stage provenance。渲染使用已有 canvas 图片层的 crop，未用 Python 编辑位图。零新增生成或语义供应商请求。

## 目录结构

- `manifest.json`：精确来源、计划作者、Master/Series/素材 ID、产物 SHA 与权利链。
- `verification.json`：六个 PNG 字节、权限、原行与来源/归档保全的独立读取结果。
- `current-readback.json`：新鲜 GET 回读的 Master 当前性与八项产品检查。
- `repair-run.log`、`current-readback.log`：最终执行与只读回读日志。
- `tech/`、`lifestyle/`：各三张 `graphic-1.png` 至 `graphic-3.png`，以及 `graphic-master.json`、`editorial-plan.json`、`checks.json`、`identity-preset.json`。

## 已完成

| 内容 | 科技 Persona | 生活 Persona |
| --- | --- | --- |
| Persona / Series | 2 / 3（revision 1） | 3 / 4（revision 1） |
| Unit / 最终 Master / Identity Snapshot | 13 / 24 / 13 | 14 / 26 / 14 |
| 默认风格 | `studio.graphic.technical-editorial@1` | `studio.graphic.warm-magazine@1` |
| 实际输出 MaterialRevision | 29、30、31 | 34、35、36 |
| PNG | 三张 1080×1440，解码及 SHA 一致 | 三张 1080×1440，解码及 SHA 一致 |
| 产品检查 | 6 pass、2 warning，全部 current | 6 pass、2 warning，全部 current |

两项 warning 分别为 `graphic_fact`、`graphic_identity`：本批语义调用预算为零，coverage 明确为 `unavailable`，未改写为 pass。结构、schema、evidence、rights、render、platform 六项通过。正式产品的 `human_review_required` 保留；人工视觉或音频感官验收不在此声称。

隔离副本中的 91 表、779 个原记录逐主键/整行 SHA 保全，0 修改、0 删除，SQLite integrity `ok`、外键问题 0。真实执行表计数为 `workflow_step_attempt` 51→51、`llm_run` 34→34、`provider_generation_task` 6→6；这些是保留的历史任务数量，新增供应商请求为零。来源库与 71 个来源素材文件的指纹保持；多平台归档全部 160 文件 SHA 保持。

## 待完成 / TODO

- 上级独立 AI 已按六张新图与精确正文完成事实、身份、信息密度和视觉复核并通过；详见 `../final-quality.json`、`../quality-review.md`，本数据回执仍只证明出处与产品检查。
- 正常产品入口的两角色创建/继承/Preview与已有结果审阅见 `../daily-product-entry.json`；未声称正式新全流程生成。
- 人工感官验收、远程账号验证及公开发布未在本批执行，不用本地产品检查代替。

## 关键设计决策

新 Series/Unit/Master 均通过现有产品能力追加，未覆盖历史身份或作品。生活 PNG 入库复用现有上传 API；该 API 不暴露 commercial 参数，因此初次新 Revision 32 的 `commercial_use_allowed=null`（未授予）保留，再经现有 `materials.create_revision` 产品服务追加同字节 Revision 33，将商业权限显式记为 false。这里包含服务层调用，不能描述成全部经 HTTP 写入。

输入 Revision 33 和六张新成品均为 public=true、model=false、commercial=false。生活封面上游历史成品的权利证据与原 manifest SHA 完整保留；本批没有新增模型或商业授权。新成品接受采用真实 renderer 输出与精确 render-input hash，并明确记录用户委托下的确认，未伪造人类视觉批准。

临时验收脚本只修正三处合同读取问题：current-check 使用 `is_current` boolean、上传缺少商业字段时追加明确拒绝授权的新版本、较大的归档指纹使用普通 SHA 而非有大小限制的 Stage digest。计数使用真实 `provider_generation_task` 表；未修改业务代码或放宽产品守卫。

## 依赖与启动方式

沿用 API 既有 `.venv`、Pillow 和 `graphic.chromium@1` 本机 renderer，无新增依赖、迁移、服务或配置。验收以 TestClient 在隔离 SQLite/素材根上调用现有服务，未监听网络端口。临时执行器为 `/tmp/persona-default-graphic-repair.py`，只读回读器为 `/tmp/persona-default-graphic-fresh-readback.py`；现有启动私有 wrapper 从 `apps/api` 加载 runtime 配置后，执行器强制覆盖为隔离数据库与素材路径。私有数据库、运行配置、凭据和全量原行指纹未导出到本目录。

代码版本和最终合并/归档状态以需求入口及 Git 为准；本次修复不自行进行 Git 操作。
