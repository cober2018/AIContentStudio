# 发现：提交修改意见后「成片通过」不能点

## 现场数据（项目 53 / 作品 99，只读）
| 时间 | 事件 |
|---|---|
| 2026-11-09 00:29:42 | 用户在成片 71 上提交「封面加数字人形象」，decision=changes |
| 2026-11-09 00:31:13 | 第三方模型开始成片新任务 72（同一导演稿 draft 311，phase=final），约 1.5 分钟后 |
| 当前 | 任务 72 result_ready，页面显示「成片待你看」，「成片通过」可点 |

## 复现（在数据库副本上做，正式库未改）
- 副本：`scratchpad/vrepro/copy.db`
- 对副本上的成片 72 调用 `decide(final, changes)`：状态 final_review → final_changes，标签「成片按你的意见修改中」。
- 按代码，final_changes 允许 approve（video_chain.py decide 第 340 行的 expected 替换规则）。
- 未在副本上执行 approve：approve 会写入素材文件，副本不能验证文件侧。

## 原因（代码层）
1. 提交修改意见后，第三方模型读到决定会马上调用 prepare_video_edit 开新任务（video_chain.py 第 738–739 行，允许从 final_changes 开新任务）。
2. 新任务一开工，`_state` 只看最新任务：状态变成 finishing（排版中）或 making（小样）。
3. 前端 VideoChainPanel.tsx 第 188 行 `reviewing` 只在 _review / _changes 状态显示按钮，finishing 时按钮全部隐藏。
4. 旧任务（71）不再是「最新任务」，状态里取不到它，approve 无法指向它。

所以「只能等新版本」不是按钮被禁用，而是：开了新任务，旧版本就不再是可通过的对象。

## 结论
- 按钮在 final_changes 时是显示的、后端也允许，问题发生在第三方模型开新任务之后。
- 小样（sample_changes → 新小样任务）同样的机制。
- 没有发现按钮被禁用或报错的路径（cover_redo 禁用只在封面重做时）。

## 待你定（见 proposal.md）
- 提交意见后，旧版本能不能直接通过。
- 新任务已经开始时，旧任务怎么处理。

## 实施后验证（数据库副本，正式库未改）
- 副本 1：把成片 72 设为 in_progress（模拟第三方已开新任务）。状态：finishing，previous_cut=71。点通过：71 被采用，72 变为 superseded，状态「已定稿」。
- 副本 2：成片 72 先提交 changes（final_changes），再直接通过：72 被采用，状态「已定稿」，决定记录正常。
- 文件侧（采用成果、封面、送审、归档）用空操作替代，只验证状态流转。
- 后端全量：2329 通过，5 个失败与改动前相同。前端类型检查、测试 36/36、构建通过。
- 未验证：小样路径（sample）只按同一代码路径推理，未在副本上跑。
- 边界：新任务已经在「做」且 dispatch_certainty=possibly_dispatched 时，作废会被拒绝，提示「新版本已经在做，暂时没法作废它」。
