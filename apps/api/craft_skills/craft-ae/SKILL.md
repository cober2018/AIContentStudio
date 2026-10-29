# craft-ae · After Effects 入口

做视频里需要 AE 的镜头时先读这份目录，再只读对应的那一项（MCP `get_craft_skill` 带 `entry`）。

## 模板库（优先）

模板是固定好的 AE 工程，只换内容不改设计。先用 `list_ae_templates` 看用途和字段，状态为 ready 的才可自动选用；用 `render_ae_template` 出片，结果是项目里的候选素材，不会绑定到镜头。

谁来选模板：

1. 默认由你按镜头内容和用途自己挑 ready 模板、自己填字段渲染，不用问用户。看不准动画效果时看 `preview_files` 里的预览视频。
2. 用户在微调时明确点名某个效果（说名称或类别），必须用对应模板；它没有当前画幅版本或不是 ready 时，先告诉用户，不擅自换成别的。
3. 画幅跟着片子走：竖屏片 `aspect` 用 9:16，横屏片用 16:9（模板 `variants` 里有 16:9 才能用，不拉伸）。
4. 带 `beats` 字段的模板（如 `keyword-contrast`、`host-parallel`）按口播节奏填：从配音字幕的逐句时间里取，时间以这个模板镜头在时间线上的起点为 0。出现 / 展开对准那句话开口的时刻，收回对准那句话说完的时刻；前一项收回后下一项再出现，顺序和口播一致。

| 要做的事 | 模板 | 说明 |
|---|---|---|
| 突出一个关键数字（以下 6 个早期模板只有竖屏） | `number-card` v1 | 大数字 + 一句说明 + 可选来源 |
| 开场或章节标题 | `title-card` v1 | 小标签 + 大标题 + 副标题 |
| 一个过程拆成 2–4 步 | `diagram-flow` v1 | 自上而下的步骤框和箭头 |
| 地图上从 A 到 B | `map-route` v1 | 地图图片 + 弧线 + 两端地名；坐标用图片相对位置；需要真实地图，不参与自动补齐 |
| 两样东西并排对比 | `compare-pair` v2 | 左右两个面板，各带标签，可各配一张图，下方一句说明；右上角可加标签（生成图标「AI 示意」）。v1 无标签，保留不再自动选用 |
| 一张图做成镜头 | `photo-push` v1 | 图片铺满缓慢推近 + 下方说明 + 右上角小标签（生成图标「AI 示意」，证明类标「AI 示意，非实拍」） |

口播、AI 科技短片和生活短片用的模板（2026-10-28 竖屏入库，2026-10-29 横屏 16:9 版本入库，同名同字段）。「叠加」类出带透明通道的 .mov，放在达芬奇上层轨道；「整屏」类出 .mp4。字段和用法以各自 manifest 的 `use` 为准。

| 类别 | 模板 | 名称 |
|---|---|---|
| 关键词与标题 | `keyword-contrast` v1 | 字体落差强调（叠加） |
|  | `keyword-slab` v1 | 斜切色块重点（叠加） |
|  | `impact-line` v1 | 整句砸出（叠加） |
|  | `outline-box-title` v1 | 描边框标题（叠加） |
|  | `split-rise-title` v1 | 逐字升起标题（叠加） |
|  | `lead-word` v1 | 首词占满补句（叠加） |
|  | `count-title` v1 | 数字重音标题（叠加） |
| 金句与对句 | `quote-card` v1 | 金句大字卡（整屏） |
|  | `quote-hold` v1 | 金句停留升级（叠加） |
|  | `pair-blocks` v1 | 双色块对句（叠加） |
| 标注与聚焦 | `ring-mark` v1 | 手绘圈重点（整屏） |
|  | `callout-label` v1 | 标注引出线（整屏） |
|  | `magnifier` v1 | 局部放大镜（整屏） |
|  | `focus-dim` v1 | 聚焦压暗（整屏） |
| 人物与图形 | `host-to-chip` v1 | 讲者缩位让台（整屏） |
|  | `host-parallel` v1 | 并列图片展开（B-roll）（叠加） |
|  | `name-plate` v1 | 人名条展示牌（叠加） |
|  | `name-chevron` v1 | 折角人名条（叠加） |
|  | `glass-board` v1 | 人物竖卡玻璃台（整屏） |
| 数字与图表 | `value-swap` v1 | 划线换数（叠加） |
|  | `metric-trend` v1 | 数字带趋势线（整屏） |
|  | `number-roll` v1 | 数字滚动计数（整屏） |
|  | `line-story` v1 | 折线分段推演（整屏） |
|  | `bar-grow` v1 | 图表生长（整屏） |
|  | `term-card` v1 | 名词解释卡（叠加） |
|  | `pick-one` v1 | 选项揭晓（整屏） |
| 步骤、流程与对比 | `step-line` v1 | 竖向步骤线（整屏） |
|  | `converge` v1 | 多源汇聚（整屏） |
|  | `timeline-travel` v1 | 时间轴横移（整屏） |
|  | `slider-compare` v1 | 滑杆对比（整屏） |
|  | `split-6040` v1 | 60/40 主从分屏（整屏） |
|  | `before-after-scrub` v1 | 前后拉杆快扫（整屏） |
| 开场、章节与转场 | `chapter-card` v1 | 章节标题卡（叠加） |
|  | `chapter-list` v1 | 章节进度（整屏） |
|  | `title-to-label` v1 | 标题降格成标签（整屏） |
|  | `line-carry` v1 | 线条接力（整屏） |
|  | `shape-wipe` v1 | 色块扫屏（叠加） |
|  | `color-slam` v1 | 纯色节拍卡（整屏） |
| 素材与地图 | `news-desk` v1 | 新闻卡片划重点（整屏） |
|  | `layout-relay` v1 | 多图焦点接力（整屏） |
|  | `grid-hero` v1 | 网格收成主角（整屏） |
|  | `echo-bed` v1 | 同源模糊底（整屏） |
|  | `route-pin` v1 | 地图落钉（整屏） |
| 结尾引导 | `follow-button` v1 | 关注按钮（叠加） |
|  | `follow-card-x` v1 | 资料卡关注（简洁款）（叠加） |
|  | `follow-card-dy` v1 | 主页卡关注（短视频款）（叠加） |

商品工作台用的模板（2026-10-29 入库，竖屏 9:16 和横屏 16:9 同名同字段）。价格、评价、证书、参数、尺寸只填真实资料，商品图保持原比例不变形；缺真实资料时不用这类模板，不编造。

| 类别 | 模板 | 名称 |
|---|---|---|
| 商品：亮相 | `product-hero` v1 | 商品原图亮相（整屏） |
|  | `product-angles` v1 | 多角度轮换（整屏） |
| 商品：卖点 | `selling-points` v1 | 三卖点图标卡（整屏） |
|  | `check-list` v1 | 卖点打勾清单（叠加） |
|  | `callout-label` v1 | 卖点标注引出线（整屏，复用） |
| 商品：参数与对比 | `spec-table` v1 | 参数表（整屏） |
|  | `compare-table` v1 | 对比表（整屏） |
|  | `dimension-mark` v1 | 尺寸标注（整屏） |
| 商品：价格与优惠 | `price-drop` v1 | 到手价（叠加） |
|  | `deal-timer` v1 | 限时标签（叠加） |
| 商品：材质与成分 | `layer-stack` v1 | 材质分层（整屏） |
|  | `magnifier` v1 | 成分 / 细节放大（整屏，复用） |
| 商品：使用方法 | `use-steps` v1 | 三步上手（整屏） |
| 商品：信任背书 | `review-cards` v1 | 真实评价卡（整屏） |
|  | `cert-card` v1 | 认证与检测卡（整屏） |
| 商品：下单引导 | `buy-cta` v1 | 下单引导卡（叠加） |
|  | `color-swatch` v1 | 颜色与规格切换（整屏） |

所有模板的文字和关键内容都在播放安全区内（`safe-zones/`），新做或改动模板后跑 `scripts/check_safe_area.py`。

模板文件：`templates/<id>/<version>/manifest.json`。

## 新效果怎么沉淀成模板

见 `templates.md`：命名约定、数据写法、入库检查（两组不同内容都渲染正确）和版本规则。

## 组件与搭建脚本

| 要做的事 | 读 |
|---|---|
| 竖屏讲解的版式分区、组件（素材卡片、标题条、标签、关键词、大字陈述、结尾卡）和时间规则 | `components.md` |
| 用一份 JSON 说明一次搭出多个合成（一次性成片，不入模板库） | `components.md` 的 Builder spec，脚本 `scripts/ae_build.py` |
| 新建或更新模板工程 | `scripts/make_templates.py` |
| 检查模板文字是否都在播放安全区内 | `scripts/check_safe_area.py`（`--aspect 16:9` 查横屏），规格见 `safe-zones/README.md` |
| 给模板出模板库预览视频 | `scripts/make_previews.py`（示例图片在本机模板库 `_samples/`） |

## 武器库（从 craft-resolve 的 `choose.md` 按问题进入，只读选中的一节）

| 类别 | 读 |
|---|---|
| 两点关键帧、缓动、静态画面运镜 | `techniques/keyframes.md` |
| 人物分离、绿幕、遮罩挡穿帮、三层夹心、混合模式、光效、讲者让位给图形 | `techniques/compositing.md` |
| 点跟踪、平面跟踪、表面离开画面 | `techniques/tracking.md` |
| 文字可读性、安全区、人名条、数字跳动、滚动数字窗、半透明信息卡、关键词重音、对句与改口、金句卡、标题入场、词槽轮换、冲击开场字、章节卡、关注引导卡 | `techniques/titles.md` |
| 手绘圈注、标注线与取景框、聚焦压暗与扫描点名、局部放大镜 | `techniques/annotate.md` |
| 同源模糊底、证据截图卡、多图排版、分屏对比、聊天与评论气泡、屏幕操作演示 | `techniques/material.md` |
| 图表生长、比例点阵、步骤与时间线、选项揭晓、地图与流程补充 | `techniques/data.md` |

## 操作注意

AE 生命周期、撤销组、渲染排队、交给达芬奇：读 craft-resolve 的 `native-execution.md`。
