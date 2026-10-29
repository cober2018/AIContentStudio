# craft-resolve · DaVinci Resolve 入口

剪辑和成片时先读这份目录，再只读对应的那一项（MCP `get_craft_skill` 带 `entry`）。

**写导演稿前先读 `choose.md`**：按片子的问题挑一两招，克制使用，并在镜头备注里写明手法和理由。

| 要做的事 | 读 |
|---|---|
| 选剪辑手法：开场、证明、概念、标注演示、图解聚焦、限制说明、结尾提问，以及先后顺序 | `edit-combos.md` |
| 声音（响度、音乐压低）、字幕断句、Resolve 装配与导出 | `finishing.md` |
| Resolve 时间码与音频的坑、AE 生命周期、工程导出重开与媒体检查 | `native-execution.md` |

## 武器库（按问题从 `choose.md` 进入，只读选中的一节）

| 类别 | 读 |
|---|---|
| 开场、时钟检查、波峰节奏、镜头时长、递进硬切、段落衔接、收尾、长片分段 | `techniques/structure.md` |
| 节拍标记、切分节拍、重拍收尾、变速、曲线变速、动作快转慢（定格）、慢放补帧、补空隙、硬切连闪与分格 | `techniques/beat-and-speed.md` |
| 景别递进、匹配剪辑、并置、J-cut、后期推镜（急推）、口播精剪、放大遮跳切、多机位、转场 | `techniques/cutting.md` |
| 镜头运动接力、藏切点、色块扫屏与节拍卡、线条接力、过曝闪白 | `techniques/transitions.md` |
| 气口微叠、声道、上升音效、混响尾音、自录音效、音乐收尾 | `techniques/sound.md` |
| 示波器、Log 还原、亮暗分区、色轮、S 曲线、单色调整、统一色调 | `techniques/color.md` |
| 分辨率、帧率、编码码率、音频参数、AI 放大、封面候选帧 | `techniques/delivery.md` |
| 代理、挑 B-roll、拆参考片、中间件 | `techniques/workflow.md` |

原则：配音决定节奏；素材按镜头的使用区间裁剪；生成素材默认静音；AE 中间件回到 Resolve 主时间线混音导出。
