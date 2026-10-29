## 统一外观（所有模板）

| 项 | 规则 |
|---|---|
| 画幅 | 1080×1920，30fps |
| 安全区 | 以用户提供的播放安全区图为准（`craft-ae/safe-zones/`）。9:16：x 59–1016、y 268–1482，且 y 769–1482 段右边界 886（右侧按钮列）；16:9：x 91–1828、y 190–959。文字和关键内容（标签、按钮、数字、卡片）必须在安全区内，整屏底色和图片可铺满。每个模板工程放一层安全区参考层（guide layer，不渲染）；`check_safe_area.py` 用示例内容逐模板检查，零越界才算通过 |
| 字体 | 思源黑体 SC（Heavy 标题 / Bold、Medium 正文），重音词可用华文宋体 Black |
| 颜色 | 黑白灰为主，每个模板一种饱和强调色（红橙、青绿、蓝、蓝紫、黄、橙）；叠加类用白色块托字，整屏类用浅灰画布或深灰底 |
| 节奏 | 参照所选卡片的入场顺序、错峰、停顿；时长范围写进 manifest |
| 文字 | 每个字段带字数上限，超宽自动缩小，空字段隐藏 |
| 透明 | `alpha: true` 的模板无底色，输出 .mov（ProRes 4444） |

## 渲染改动

`render()`：manifest `alpha` 为真时用 aerender 输出模块模板（ProRes 4444 + Alpha）出 `out.mov`，以 `video/quicktime` 入库；否则照旧 `out.mp4`。达芬奇装配时 alpha 素材放视频 2 轨以上。

## 模板清单

「透明」= 叠在画面上用。字段为初稿，做每批前在批次说明里定稿。

### 第一批：关键词、金句 / 对句、标注、人物与图形

| # | 模板 id | 名称 | 参照卡 | 字段（初稿） | 透明 |
|---|---|---|---|---|---|
| 1 | keyword-contrast | 字体落差强调 | type-contrast-emphasis | 句子、重音词 | 是 |
| 2 | keyword-slab | 斜切色块重点 | slab-punch-title | 第一行、重点词 | 是 |
| 3 | impact-line | 整句砸出 | impact-open-title | 句子、副题 | 是 |
| 4 | outline-box-title | 描边框标题 | outline-box-title | 标题 | 是 |
| 5 | split-rise-title | 逐字裂升 | split-text-stagger | 标题 | 是 |
| 6 | quote-card | 金句大字卡 | quote-card | 3–5 行、关键词 | 否 |
| 7 | quote-hold | 金句停留升级 | quote-hold-arrow | 3 行 | 是 |
| 8 | pair-blocks | 双色块对句 | alt-block-lines | 上句、下句 | 是 |
| 9 | ring-mark | 手绘圈重点 | hand-drawn-ellipse | 截图、圈的位置 | 否 |
| 10 | callout-label | 标注引出线 | callout-line-label | 图、点位置、标签（1–3 处） | 否 |
| 11 | magnifier | 局部放大镜 | magnifier-detail | 图、放大区域 | 否 |
| 12 | focus-dim | 聚焦压暗 | focus-dim-spotlight | 图、2–4 个焦点区域 | 否 |
| 13 | host-to-chip | 讲者缩位让台 | host-shrink-to-chip | 人物视频片段（图片槽先用静帧）、图形 | 否 |
| 14 | host-parallel | 人在场的并列项 | parallel-items-with-host | 3 项文字、可选小图 | 是 |
| 15 | name-plate | 人名条展示牌 | lower-third-nameplate | 姓名、身份 | 是 |
| 16 | name-chevron | 折角人名条 | chevron-lower-third | 姓名、身份 | 是 |

### 第二批：数字、图表、步骤 / 流程、对比

| # | 模板 id | 名称 | 参照卡 | 字段（初稿） | 透明 |
|---|---|---|---|---|---|
| 17 | value-swap | 划线换数 | strike-and-replace | 句子、旧值、新值 | 是 |
| 18 | count-title | 数字重音标题 | count-badge-title | 数字、后半句、第二行 | 是 |
| 19 | metric-trend | 数字带趋势线 | metric-with-sparkline | 标签、数值、单位、4–6 个点 | 否 |
| 20 | number-roll | 数字滚动计数 | number-counter | 起始值、目标值、单位、说明 | 否 |
| 21 | term-card | 名词解释卡 | info-term-card | 词条、两行释义 | 是 |
| 22 | pick-one | 选项揭晓 | chip-grid-single-select | 问题、3–6 个选项、答案序号 | 否 |
| 23 | line-story | 折线分段推演 | line-chart-story-draw | 数据点、拐点、标签、来源 | 否 |
| 24 | bar-grow | 图表生长 | chart-grow | 3–8 组标签与数值、单位、来源、结论 | 否 |
| 25 | glass-board | 人物竖卡玻璃台 | host-card-glass-board | 人物图、标题、2–4 项 | 否 |
| 26 | step-line | 竖向步骤线 | step-timeline-vertical | 3–5 步、当前步 | 否 |
| 27 | converge | 多源汇聚 | source-converge | 2–4 个来源、结果 | 否 |
| 28 | line-carry | 线条接力 | line-carry-transition | A 段标题、B 段标题 | 否 |
| 29 | timeline-travel | 时间轴横移 | timeline-travel | 3–6 个时间点与说明、停靠点 | 否 |
| 30 | slider-compare | 滑杆对比 | split-compare-slider | 前图、后图、标签 | 否 |
| 31 | split-6040 | 60/40 主从分屏 | split-60-40-story | 主图、标题、3 个要点 | 否 |
| 32 | before-after-scrub | 前后拉杆快扫 | before-after-slider-scrub | 前图、后图、标签 | 否 |

### 第三批：开场 / 章节、素材呈现、地图、转场、结尾引导

| # | 模板 id | 名称 | 参照卡 | 字段（初稿） | 透明 |
|---|---|---|---|---|---|
| 33 | chapter-card | 章节标题卡 | chapter-title-card | 编号、章节名、主题色 | 否 |
| 34 | chapter-list | 章节进度 | chapter-progress-list | 3–5 个章节、当前章 | 否 |
| 35 | title-to-label | 标题降格成标签 | title-demote-to-label | 标题、2–3 条内容 | 否 |
| 36 | lead-word | 首词占满补句 | lead-word-zoom-assemble | 首词、后半句 | 是 |
| 37 | news-desk | 新闻卡片划重点 | news-card-desk | 1–2 张截图、划线位置、来源 | 否 |
| 38 | layout-relay | 多图焦点接力 | still-layout-relay | 2–3 张图 | 否 |
| 39 | grid-hero | 网格收成主角 | grid-to-hero | 4 张图、主角序号 | 否 |
| 40 | echo-bed | 同源模糊底 | bed-echo-blur | 素材图、标题、来源 | 否 |
| 41 | route-pin | 地图落钉 | map-route-pin | 地图图、2–3 个点与地名 | 否 |
| 42 | shape-wipe | 色块扫屏 | shape-wipe-transition | 方向、颜色 | 是 |
| 43 | color-slam | 纯色节拍卡 | color-slam-beat-card | 大字、可选素材图、底色 | 否 |
| 44 | follow-button | 关注按钮 | subscribe-cta | 按钮文字 | 是 |
| 45 | follow-card-x | 资料卡关注（简洁款） | x-follow-card | 头像、昵称、简介 | 是 |
| 46 | follow-card-dy | 主页卡关注（短视频款） | douyin-follow-card | 头像、昵称、账号、简介 | 是 |

## 边界

- 关注卡画中性卡片，不使用任何平台的真实界面、图标和商标；头像昵称用账号真实信息，粉丝数不写或写真实值。
- 「人物视频」类模板（13、25）第一版用人物静帧图片槽；要叠真人视频时用透明版在达芬奇里合成。
- 图片槽只接项目里的素材，生成图照旧标「AI 示意」。

## 不做

素材数据源（另一个需求）；数字人；改模板自动选用规则。
