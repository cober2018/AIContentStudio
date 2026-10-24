## 页面结构

`ProductionWorkspace` 中角色视频（`simpleVideo`）的步骤：

| id | 名称 | 组件 |
|---|---|---|
| goal | 选题与资料 | `GuidedProductionGoal`（不变） |
| plan | 导演稿 | `VideoChainPanel step="draft"` + 逐镜 `StoryboardTable paged`；不再挂主稿编辑器 |
| materials | 素材 | 新组件 `ShotMaterialPages`：逐镜（上一镜 / 下一镜 + 镜头编号条），每镜显示素材需求、绑定素材预览（复用素材预览）、缺口；拖放沿用 `StoryboardTable.dropMaterial` 的接口（`shot-slots/{shot}/upload-target` → `attach`） |
| voice | 配音与音乐 | `VoiceoverPanel` + 新的 `MusicPanel`：读当前主稿 `music` 引用并试听；从素材库拖一首音频替换，调 `POST .../video-chain/music`（内部复用 `set_materials(music=...)`） |
| sample | 小样 | `VideoChainPanel step="sample"` |
| final | 成片 | `VideoChainPanel step="final"`；定稿后显示「已定稿」+「复制一份」 |
| delivery | 交付 | 渠道适配（`ChannelVariantsPanel`），从底部「渠道、执行…」移来 |

「高级」页：`workstep=advanced`，步骤栏底部单独一个入口（不编号）。放：`ContentMasterPanel`（完整编辑器，原「更多」内容）、`ProductionContextHeader` 的身份快照、创意执行、方法与偏好、高级自动化。定稿后只读。

步骤到达规则（`chainStep`）：draft_*/not_started → plan；making → materials（素材、配音都可进）；sample_* → sample；finishing/final_*/done → final。materials、voice 在 making 及以后可进。旧链接：`make` → materials，`review` → final，`execution` 参数 → advanced。

顶部「镜头素材」条（`ProductionContextHeader` 内）对角色视频不再显示，信息在第 3 步。底部 `<details>渠道、执行、方法与高级工作流` 对角色视频不渲染。

## 定稿

- 删除 `video_chain.reopen` 与 `POST .../video-chain/reopen`，`_finished` 不再看 reopen 记录：`done` 即 `locked: true`。已有的 reopen 记录（目前没有）忽略。
- `save_revision` 锁定提示改为「成片已定稿，要调整请复制一份」。
- 素材替换、音乐替换、配音生成都走保存主稿，因此一并被拒。

## 退回导演稿

`decide(stage="draft", decision="changes")` 现在只允许在导演稿待看时用。放宽为：未定稿且当前在导演稿之后（making / sample_* / finishing / final_*）也可，记录到当前导演稿上 → `_state` 读到该导演稿最新决定是 changes → `draft_changes`。Claude Code 读到后写新导演稿，流程从导演稿重走。页面：导演稿页在流程已过导演稿且未定稿时显示「退回导演稿」+ 意见框。

## 复制一份

`POST /content-projects/{p}/units/{u}/copy`（编辑权限）：
- 新 `ContentUnit`：同 project、persona、account、series、modality、channel、pinned_workflow；新建身份快照（同 `create_unit`）；标题「原标题 · 副本」（重复时加序号）。
- 视频：取 `video_chain.draft_root(latest)`（采用的导演稿）的 payload 和资产引用，用 `save_revision` 存为新作品第一版，`edit_summary = {"video_chain": "draft", "copied_from": {"unit_id", "master_id"}}`，新作品状态即「导演稿待你看」。
- 图文：取最新主稿 payload 和资产 / 证据引用，存为新作品第一版，`edit_summary = {"copied_from": ...}`。
- 文字：422「文字作品暂不支持复制」。
- 记 `project_event`：`unit.copied`。
- 页面：项目「内容矩阵」每条加「复制一份」；成片页定稿后有「复制一份」，成功后跳到新作品第 2 步。

## 不做

不改表结构；商品视频、文字页面不改。
