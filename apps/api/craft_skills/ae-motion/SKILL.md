# ae-motion · After Effects 入口

做视频里需要 AE 的镜头时先读这份目录，再只读对应的那一项（MCP `get_craft_skill` 带 `entry`）。

## 模板库（优先）

模板是固定好的 AE 工程，只换内容不改设计。先用 `list_ae_templates` 看用途和字段，状态为 ready 的才可自动选用；用 `render_ae_template` 出片，结果是项目里的候选素材，不会绑定到镜头。

| 要做的事 | 模板 | 说明 |
|---|---|---|
| 突出一个关键数字 | `number-card` v1 | 大数字 + 一句说明 + 可选来源 |
| 开场或章节标题 | `title-card` v1 | 小标签 + 大标题 + 副标题 |
| 一个过程拆成 2–4 步 | `diagram-flow` v1 | 自上而下的步骤框和箭头 |
| 地图上从 A 到 B | `map-route` v1 | 地图图片 + 弧线 + 两端地名；坐标用图片相对位置；需要真实地图，不参与自动补齐 |
| 两样东西并排对比 | `compare-pair` v2 | 左右两个面板，各带标签，可各配一张图，下方一句说明；右上角可加标签（生成图标「AI 示意」）。v1 无标签，保留不再自动选用 |
| 一张图做成镜头 | `photo-push` v1 | 图片铺满缓慢推近 + 下方说明 + 右上角小标签（生成图标「AI 示意」，证明类标「AI 示意，非实拍」） |

模板文件：`templates/<id>/<version>/manifest.json`。

## 新效果怎么沉淀成模板

见 `templates.md`：命名约定、数据写法、入库检查（两组不同内容都渲染正确）和版本规则。

## 组件与搭建脚本

| 要做的事 | 读 |
|---|---|
| 竖屏讲解的版式分区、组件（素材卡片、标题条、标签、关键词、大字陈述、结尾卡）和时间规则 | `components.md` |
| 用一份 JSON 说明一次搭出多个合成（一次性成片，不入模板库） | `components.md` 的 Builder spec，脚本 `scripts/ae_build.py` |
| 新建或更新模板工程 | `scripts/make_templates.py` |

## 操作注意

AE 生命周期、撤销组、渲染排队、交给达芬奇：读 resolve-edit 的 `native-execution.md`。
